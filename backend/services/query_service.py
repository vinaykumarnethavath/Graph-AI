"""
Query Service Layer
Handles complex graph queries and analytics
"""

from typing import Dict, List, Any, Optional
from backend.services.graph_service import GraphService


class QueryService:
    """Service for complex graph queries and analysis"""
    
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
    
    def find_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find an entity by type and ID"""
        node_id = f"{entity_type}:{entity_id}"
        return self.graph_service.get_node(node_id)
    
    def find_journal_entry(self, billing_document: str) -> Optional[Dict[str, Any]]:
        """Find journal entry linked to a billing document"""
        # Search for journal entries with matching reference
        results = self.graph_service.search_nodes_by_attribute(
            'reference_sd_document', billing_document
        )
        
        if not results:
            # Try invoice reference
            results = self.graph_service.search_nodes_by_attribute(
                'invoice_reference', billing_document
            )
        
        return results[0] if results else None
    
    def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a customer"""
        customer_node = f"Customer:{customer_id}"
        
        if not self.graph_service.graph.has_node(customer_node):
            return []
        
        orders = []
        for pred in self.graph_service.graph.predecessors(customer_node):
            if pred.startswith('SalesOrder:'):
                order_data = self.graph_service.get_node(pred)
                if order_data:
                    orders.append(order_data)
        
        return orders

    def get_order_counts_by_customer(self) -> Dict[str, Any]:
        """Get order counts for each customer with node references for graph highlighting"""
        customer_nodes = self.graph_service.search_nodes_by_type('Customer', limit=10000)
        breakdown = []
        highlighted_orders = []

        for customer in customer_nodes:
            customer_id = customer.get('business_partner') or customer.get('customer_id') or customer.get('node_id', '').split(':')[-1]
            customer_node_id = customer.get('node_id')
            orders = self.get_customer_orders(customer_id)

            order_refs = []
            for order in orders:
                order_node_id = order.get('node_id')
                if order_node_id:
                    order_refs.append({
                        'node_id': order_node_id,
                        'sales_order': order.get('sales_order')
                    })
                    highlighted_orders.append({
                        'node_id': order_node_id,
                        'sales_order': order.get('sales_order')
                    })

            breakdown.append({
                'customer_id': customer_id,
                'node_id': customer_node_id,
                'customer_name': customer.get('customer_name') or customer.get('business_partner_name') or customer_id,
                'order_count': len(orders),
                'orders': order_refs
            })

        breakdown.sort(key=lambda item: item['order_count'], reverse=True)

        return {
            'metric': 'orders_per_customer',
            'total_customers': len(breakdown),
            'total_orders': sum(item['order_count'] for item in breakdown),
            'customer_breakdown': breakdown,
            'nodes': [
                {
                    'node_id': item['node_id'],
                    'customer_id': item['customer_id'],
                    'customer_name': item['customer_name'],
                    'order_count': item['order_count']
                }
                for item in breakdown if item['node_id']
            ],
            'orders': highlighted_orders
        }
    
    def get_product_orders(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all order items for a product"""
        product_node = f"Product:{product_id}"
        
        if not self.graph_service.graph.has_node(product_node):
            return []
        
        order_items = []
        for pred in self.graph_service.graph.predecessors(product_node):
            if pred.startswith('SalesOrderItem:'):
                item_data = self.graph_service.get_node(pred)
                if item_data:
                    order_items.append(item_data)
        
        return order_items
    
    def get_delivery_details(self, delivery_id: str) -> Dict[str, Any]:
        """Get complete delivery details with related entities"""
        delivery_node = f"Delivery:{delivery_id}"
        delivery = self.graph_service.get_node(delivery_node)
        
        if not delivery:
            return None
        
        details = {
            'delivery': delivery,
            'items': [],
            'orders': [],
            'invoices': []
        }
        
        # Get delivery items
        for succ in self.graph_service.graph.successors(delivery_node):
            if succ.startswith('DeliveryItem:'):
                details['items'].append(self.graph_service.get_node(succ))
        
        # Get related orders
        for succ in self.graph_service.graph.successors(delivery_node):
            if succ.startswith('SalesOrder:'):
                details['orders'].append(self.graph_service.get_node(succ))
        
        # Get invoices
        for pred in self.graph_service.graph.predecessors(delivery_node):
            if pred.startswith('Invoice:'):
                details['invoices'].append(self.graph_service.get_node(pred))
        
        return details
    
    def get_invoice_details(self, billing_document: str) -> Dict[str, Any]:
        """Get complete invoice details"""
        invoice_node = f"Invoice:{billing_document}"
        invoice = self.graph_service.get_node(invoice_node)
        
        if not invoice:
            return None
        
        details = {
            'invoice': invoice,
            'items': [],
            'deliveries': [],
            'orders': []
        }
        
        # Get invoice items
        for succ in self.graph_service.graph.successors(invoice_node):
            if succ.startswith('InvoiceItem:'):
                details['items'].append(self.graph_service.get_node(succ))
        
        # Get related deliveries
        for succ in self.graph_service.graph.successors(invoice_node):
            if succ.startswith('Delivery:'):
                details['deliveries'].append(self.graph_service.get_node(succ))
        
        # Get related orders
        for succ in self.graph_service.graph.successors(invoice_node):
            if succ.startswith('SalesOrder:'):
                details['orders'].append(self.graph_service.get_node(succ))
        
        return details
    
    def search_entities(self, query: str, entity_types: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search entities by text query (deduplicated)"""
        results = []
        seen_nodes = set()
        query_lower = query.lower()
        
        for node, data in self.graph_service.graph.nodes(data=True):
            if node in seen_nodes:
                continue
                
            node_type = data.get('node_type', '')
            
            # Filter by entity type if specified
            if entity_types and node_type not in entity_types:
                continue
            
            match_found = False
            
            # Search in node ID
            if query_lower in node.lower():
                match_found = True
            
            # Search in attribute values
            if not match_found:
                for key, value in data.items():
                    if isinstance(value, str) and query_lower in str(value).lower():
                        match_found = True
                        break
            
            if match_found:
                result = dict(data)
                result['node_id'] = node
                results.append(result)
                seen_nodes.add(node)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_customer_analytics(self, customer_id: str) -> Dict[str, Any]:
        """Get analytics for a customer"""
        customer_node = f"Customer:{customer_id}"
        customer = self.graph_service.get_node(customer_node)
        
        if not customer:
            return None
        
        orders = self.get_customer_orders(customer_id)
        
        total_order_value = sum(
            float(order.get('total_net_amount', 0) or 0)
            for order in orders
        )
        
        # Get payments
        payments = []
        for pred in self.graph_service.graph.predecessors(customer_node):
            if pred.startswith('Payment:'):
                payments.append(self.graph_service.get_node(pred))
        
        total_payment_value = sum(
            float(payment.get('amount_in_transaction_currency', 0) or 0)
            for payment in payments
        )
        
        return {
            'customer': customer,
            'total_orders': len(orders),
            'total_order_value': total_order_value,
            'total_payments': len(payments),
            'total_payment_value': total_payment_value,
            'payment_rate': (total_payment_value / total_order_value * 100) if total_order_value > 0 else 0,
            'orders': orders[:5],  # Latest 5 orders
            'payments': payments[:5]  # Latest 5 payments
        }
    
    def trace_document_flow(self, document_id: str, document_type: str) -> Dict[str, Any]:
        """Trace the complete flow of a document through the O2C process"""
        node_id = f"{document_type}:{document_id}"
        
        if not self.graph_service.graph.has_node(node_id):
            return None
        
        # Get 2-hop subgraph
        subgraph = self.graph_service.get_subgraph(node_id, depth=2)
        
        # Identify flow stages
        flow_stages = {
            'current': self.graph_service.get_node(node_id),
            'upstream': [],
            'downstream': [],
            'related': []
        }
        
        for node_data in subgraph['nodes']:
            node_type = node_data.get('node_type', '')
            node_key = node_data['node_id']
            
            if node_key == node_id:
                continue
            
            if node_type in ['Customer', 'Product', 'Plant']:
                flow_stages['related'].append(node_data)
            elif document_type == 'SalesOrder':
                if node_type in ['SalesOrderItem']:
                    flow_stages['downstream'].append(node_data)
                elif node_type in ['Delivery', 'Invoice']:
                    flow_stages['downstream'].append(node_data)
            elif document_type == 'Delivery':
                if node_type in ['SalesOrder']:
                    flow_stages['upstream'].append(node_data)
                elif node_type in ['Invoice', 'DeliveryItem']:
                    flow_stages['downstream'].append(node_data)
            elif document_type == 'Invoice':
                if node_type in ['Delivery', 'SalesOrder']:
                    flow_stages['upstream'].append(node_data)
                elif node_type in ['Payment', 'InvoiceItem']:
                    flow_stages['downstream'].append(node_data)
        
        return {
            **flow_stages,
            'subgraph': subgraph
        }
