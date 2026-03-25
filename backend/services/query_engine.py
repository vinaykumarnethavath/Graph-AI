"""
Query Engine
Executes structured queries from LLM on the graph database
Handles edge cases and returns JSON results
"""

from typing import Dict, List, Any, Optional
from backend.services.graph_service import GraphService
from backend.services.query_service import QueryService
import logging

logger = logging.getLogger(__name__)


class QueryEngineException(Exception):
    """Base exception for query engine errors"""
    pass


class InvalidQueryException(QueryEngineException):
    """Query validation failed"""
    pass


class EntityNotFoundException(QueryEngineException):
    """Requested entity not found"""
    pass


class QueryEngine:
    """
    Unified query engine that takes structured queries and executes them
    Handles edge cases and returns standardized JSON responses
    """
    
    def __init__(self, graph_service: GraphService, query_service: QueryService):
        self.graph_service = graph_service
        self.query_service = query_service
        self.supported_intents = [
            'search', 'get_details', 'trace_flow', 'analytics',
            'find_relationship', 'aggregate', 'detect_missing_links'
        ]
    
    def execute(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a structured query from LLM
        
        Args:
            structured_query: {
                "intent": "search" | "get_details" | "trace_flow" | etc,
                "entity_type": "SalesOrder" | "Customer" | etc,
                "entity_id": "740506" (optional),
                "parameters": {...} (optional)
            }
        
        Returns:
            {
                "success": bool,
                "data": Any,
                "metadata": {
                    "query": Dict,
                    "execution_time_ms": float,
                    "records_found": int
                },
                "errors": List[str],
                "warnings": List[str]
            }
        """
        import time
        start_time = time.time()
        
        # Initialize response
        response: Dict[str, Any] = {
            "success": False,
            "data": None,
            "metadata": {
                "query": structured_query,
                "execution_time_ms": 0,
                "records_found": 0
            },
            "errors": [],
            "warnings": []
        }
        
        try:
            # Validate query
            self._validate_query(structured_query)
            
            # Route to appropriate handler
            intent = structured_query.get('intent')
            
            if intent == 'get_details':
                result = self._handle_get_details(structured_query)
            elif intent == 'search':
                result = self._handle_search(structured_query)
            elif intent == 'trace_flow':
                result = self._handle_trace_flow(structured_query)
            elif intent == 'analytics':
                result = self._handle_analytics(structured_query)
            elif intent == 'find_relationship':
                result = self._handle_find_relationship(structured_query)
            elif intent == 'aggregate':
                result = self._handle_aggregate(structured_query)
            elif intent == 'detect_missing_links':
                result = self._handle_detect_missing_links(structured_query)
            else:
                raise InvalidQueryException(f"Unsupported intent: {intent}")
            
            # Set success response
            response["success"] = True
            response["data"] = result["data"]
            response["warnings"] = result.get("warnings", [])
            
            # Update metadata
            if isinstance(result["data"], list):
                response["metadata"]["records_found"] = len(result["data"])
            elif isinstance(result["data"], dict):
                response["metadata"]["records_found"] = 1
            
        except EntityNotFoundException as e:
            response["errors"].append(str(e))
            response["data"] = None
            logger.warning(f"Entity not found: {e}")
            
        except InvalidQueryException as e:
            response["errors"].append(str(e))
            logger.error(f"Invalid query: {e}")
            
        except Exception as e:
            response["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Query execution error: {e}", exc_info=True)
        
        finally:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            response["metadata"]["execution_time_ms"] = round(execution_time, 2)
        
        return response
    
    def _validate_query(self, query: Dict[str, Any]):
        """Validate query structure"""
        if not query:
            raise InvalidQueryException("Query cannot be empty")
        
        if 'intent' not in query:
            raise InvalidQueryException("Query must have 'intent' field")
        
        if query['intent'] not in self.supported_intents:
            raise InvalidQueryException(
                f"Unsupported intent: {query['intent']}. "
                f"Supported: {', '.join(self.supported_intents)}"
            )
    
    def _handle_get_details(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_details intent"""
        entity_type = query.get('entity_type')
        entity_id = query.get('entity_id')
        
        if not entity_id:
            raise InvalidQueryException("entity_id is required for get_details")
        
        node_id = f"{entity_type}:{entity_id}" if entity_type else entity_id
        
        # Handle invalid node ID format
        if ':' not in node_id:
            raise InvalidQueryException(f"Invalid node ID format: {node_id}")
        
        node = self.graph_service.get_node(node_id)
        
        if not node:
            raise EntityNotFoundException(f"Node not found: {node_id}")
        
        # Get related entities
        edges = self.graph_service.get_edges_for_node(node_id)
        
        return {
            "data": {
                "node": node,
                "connections": {
                    "total": len(edges),
                    "in": node.get('in_degree', 0),
                    "out": node.get('out_degree', 0)
                },
                "edges": edges[:10]  # Limit to first 10
            },
            "warnings": [] if edges else ["Node has no connections"]
        }
    
    def _handle_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search intent"""
        search_query = query.get('entity_id', '')
        entity_types = [query.get('entity_type')] if query.get('entity_type') else None
        limit = query.get('parameters', {}).get('limit', 20)
        
        results = self.query_service.search_entities(search_query, entity_types, limit)
        
        # Handle duplicates
        unique_results = self._deduplicate_results(results)
        
        warnings = []
        if len(unique_results) < len(results):
            warnings.append(f"Removed {len(results) - len(unique_results)} duplicate results")
        
        if not unique_results:
            warnings.append("No results found for search query")
        
        return {
            "data": unique_results,
            "warnings": warnings
        }
    
    def _handle_trace_flow(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trace_flow intent with missing link detection"""
        entity_type = query.get('entity_type')
        entity_id = query.get('entity_id')
        
        if not entity_id:
            raise InvalidQueryException("entity_id is required for trace_flow")
        
        warnings = []
        
        # Handle different entity types
        if entity_type == 'SalesOrder':
            flow = self.graph_service.get_order_flow(entity_id)
            
            if not flow:
                raise EntityNotFoundException(f"Order not found: {entity_id}")
            
            # Detect missing links
            missing_links = self._detect_flow_gaps(flow)
            if missing_links:
                warnings.extend(missing_links)
            
            return {
                "data": flow,
                "warnings": warnings
            }
        
        else:
            # Generic flow tracing
            node_id = f"{entity_type}:{entity_id}"
            
            if not self.graph_service.graph.has_node(node_id):
                raise EntityNotFoundException(f"Node not found: {node_id}")
            
            flow = self.query_service.trace_document_flow(entity_id, entity_type)
            
            return {
                "data": flow,
                "warnings": warnings
            }
    
    def _handle_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics intent with fallback to aggregations"""
        entity_type = query.get('entity_type')
        entity_id = query.get('entity_id')
        
        # Specific analytics for Customer
        if entity_type == 'Customer' and entity_id:
            analytics = self.query_service.get_customer_analytics(entity_id)
            if not analytics:
                raise EntityNotFoundException(f"Customer not found: {entity_id}")
            return {"data": analytics, "warnings": []}
        
        # Generic fallback for count/aggregations (e.g., "how many deliveries...")
        try:
            # If no entity_id, it's likely a general question about the type
            if not entity_id or entity_id == 'total':
                return self._handle_aggregate(query)
            
            # If entity_id is provided but we don't have deep analytics, return node details
            return self._handle_get_details(query)
            
        except Exception:
            raise InvalidQueryException(f"Analytics not supported for {entity_type}")
    
    def _handle_find_relationship(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle find_relationship intent"""
        entity_id = query.get('entity_id')
        entity_type = query.get('entity_type')
        target_type = query.get('parameters', {}).get('target')
        
        if not entity_id:
            raise InvalidQueryException("entity_id is required")
        
        node_id = f"{entity_type}:{entity_id}"
        
        if not self.graph_service.graph.has_node(node_id):
            raise EntityNotFoundException(f"Node not found: {node_id}")
        
        # Find related nodes
        neighbors = self.graph_service.get_node_neighbors(node_id, direction='both')
        
        # Filter by target type if specified
        if target_type:
            filtered = {
                'predecessors': [n for n in neighbors.get('predecessors', []) 
                                if n.startswith(f"{target_type}:")],
                'successors': [n for n in neighbors.get('successors', [])
                              if n.startswith(f"{target_type}:")]
            }
            neighbors = filtered
        
        # Get details for related nodes
        related = []
        for node_list in [neighbors.get('predecessors', []), neighbors.get('successors', [])]:
            for neighbor_id in node_list[:10]:  # Limit
                node_data = self.graph_service.get_node(neighbor_id)
                if node_data:
                    related.append(node_data)
        
        warnings = []
        if not related:
            warnings.append(f"No relationships found for {node_id}")
        
        return {
            "data": {
                "source": node_id,
                "related_nodes": related,
                "total_relationships": len(related)
            },
            "warnings": warnings
        }
    
    def _handle_aggregate(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle aggregation queries"""
        entity_type = query.get('entity_type')
        aggregation = query.get('parameters', {}).get('aggregation', 'count')
        field = query.get('parameters', {}).get('field')

        if entity_type == 'SalesOrder' and aggregation == 'group_by' and field in ['customer', 'customer_id', 'business_partner']:
            result = self.query_service.get_order_counts_by_customer()
            return {
                "data": result,
                "warnings": [] if result.get('customer_breakdown') else ["No customer order relationships found"]
            }
        
        nodes = self.graph_service.search_nodes_by_type(entity_type, limit=10000)
        
        if not nodes:
            return {
                "data": {"count": 0},
                "warnings": [f"No {entity_type} nodes found"]
            }
        
        # Perform aggregation
        if aggregation == 'count':
            result = {"count": len(nodes)}
        
        elif aggregation == 'sum' and field:
            total = sum(float(n.get(field, 0) or 0) for n in nodes)
            result = {"sum": total, "field": field}
        
        elif aggregation == 'avg' and field:
            values = [float(n.get(field, 0) or 0) for n in nodes if n.get(field)]
            avg = sum(values) / len(values) if values else 0
            result = {"average": avg, "field": field}
        
        elif aggregation == 'group_by' and field:
            from collections import Counter
            groups = Counter(n.get(field) for n in nodes if n.get(field))
            result = {"groups": dict(groups), "field": field}
        
        else:
            raise InvalidQueryException(f"Unsupported aggregation: {aggregation}")
        
        return {
            "data": result,
            "warnings": []
        }
    
    def _handle_detect_missing_links(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Detect missing relationships in the graph"""
        entity_type = query.get('entity_type', 'SalesOrder')
        
        # Get all nodes of this type
        nodes = self.graph_service.search_nodes_by_type(entity_type, limit=1000)
        
        missing_links = []
        
        for node in nodes:
            node_id = node['node_id']
            
            # Check expected relationships based on entity type
            if entity_type == 'SalesOrder':
                gaps = self._check_order_completeness(node_id)
                if gaps:
                    missing_links.append({
                        "node_id": node_id,
                        "missing": gaps
                    })
            
            elif entity_type == 'Delivery':
                # Check if delivery has order reference
                neighbors = self.graph_service.get_node_neighbors(node_id)
                if not neighbors.get('successors'):
                    missing_links.append({
                        "node_id": node_id,
                        "missing": ["No order reference"]
                    })
        
        return {
            "data": {
                "total_checked": len(nodes),
                "missing_links": missing_links,
                "completeness_rate": 
                    (1 - len(missing_links) / len(nodes)) * 100 if nodes else 100
            },
            "warnings": [] if not missing_links else 
                [f"Found {len(missing_links)} incomplete records"]
        }
    
    def _detect_flow_gaps(self, flow: Dict[str, Any]) -> List[str]:
        """Detect gaps in order-to-cash flow"""
        warnings = []
        
        if not flow.get('items'):
            warnings.append("Order has no items")
        
        if not flow.get('deliveries'):
            warnings.append("Order has no deliveries")
        
        if not flow.get('invoices'):
            warnings.append("Order has no invoices")
        
        if not flow.get('payments'):
            warnings.append("No payments found for this customer")
        
        if not flow.get('customer'):
            warnings.append("Customer information missing")
        
        return warnings
    
    def _check_order_completeness(self, order_id: str) -> List[str]:
        """Check if an order has all expected relationships"""
        gaps = []
        
        neighbors = self.graph_service.get_node_neighbors(order_id)
        
        # Check for items
        has_items = any(n.startswith('SalesOrderItem:') 
                       for n in neighbors.get('successors', []))
        if not has_items:
            gaps.append("No order items")
        
        # Check for delivery
        has_delivery = any(n.startswith('Delivery:') 
                          for n in neighbors.get('predecessors', []))
        if not has_delivery:
            gaps.append("No delivery")
        
        # Check for customer
        has_customer = any(n.startswith('Customer:') 
                          for n in neighbors.get('successors', []))
        if not has_customer:
            gaps.append("No customer")
        
        return gaps
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on node_id"""
        seen = set()
        unique = []
        
        for result in results:
            node_id = result.get('node_id')
            if node_id and node_id not in seen:
                seen.add(node_id)
                unique.append(result)
        
        return unique
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported query intents"""
        return self.supported_intents
