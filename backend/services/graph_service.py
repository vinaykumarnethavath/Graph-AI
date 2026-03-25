"""
Graph Service Layer
Handles all NetworkX graph operations
"""

import pickle
import networkx as nx
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import deque


class GraphService:
    """Service for managing and querying the knowledge graph"""
    
    def __init__(self, graph_path: str):
        self.graph_path = Path(graph_path)
        self.graph = None
        self._node_type_index = {}
        self._cached_stats = None
        self._load_graph()
    
    def _load_graph(self):
        """Load the graph from disk"""
        try:
            with open(self.graph_path, 'rb') as f:
                self.graph = pickle.load(f)
            print(f"Graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            self._build_indices()
        except Exception as e:
            raise Exception(f"Failed to load graph: {e}")
    
    def _build_indices(self):
        """Build search indices for performance"""
        print("Building search indices...")
        self._node_type_index = {}
        
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'Unknown')
            if node_type not in self._node_type_index:
                self._node_type_index[node_type] = []
            self._node_type_index[node_type].append(node)
        
        print(f"Indices built for {len(self._node_type_index)} entity types")
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get basic graph statistics (cached)"""
        if self._cached_stats is not None:
            return self._cached_stats
        
        node_types = {k: len(v) for k, v in self._node_type_index.items()}
        
        self._cached_stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': node_types,
            'is_directed': self.graph.is_directed()
        }
        
        return self._cached_stats
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node and its attributes"""
        if not self.graph.has_node(node_id):
            return None
        
        attrs = dict(self.graph.nodes[node_id])
        attrs['node_id'] = node_id
        
        # Get connections
        attrs['in_degree'] = self.graph.in_degree(node_id)
        attrs['out_degree'] = self.graph.out_degree(node_id)
        
        return attrs
    
    def get_node_neighbors(self, node_id: str, direction: str = 'both') -> Dict[str, List[str]]:
        """Get neighbors of a node"""
        if not self.graph.has_node(node_id):
            return {'predecessors': [], 'successors': []}
        
        result = {}
        
        if direction in ['both', 'in']:
            result['predecessors'] = list(self.graph.predecessors(node_id))
        
        if direction in ['both', 'out']:
            result['successors'] = list(self.graph.successors(node_id))
        
        return result
    
    def get_edges_for_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all edges connected to a node"""
        if not self.graph.has_node(node_id):
            return []
        
        edges = []
        
        # Outgoing edges
        for source, target, data in self.graph.out_edges(node_id, data=True):
            edges.append({
                'source': source,
                'target': target,
                'direction': 'out',
                'relationship': data.get('relationship', 'UNKNOWN'),
                **data
            })
        
        # Incoming edges
        for source, target, data in self.graph.in_edges(node_id, data=True):
            edges.append({
                'source': source,
                'target': target,
                'direction': 'in',
                'relationship': data.get('relationship', 'UNKNOWN'),
                **data
            })
        
        return edges
    
    def search_nodes_by_type(self, node_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search nodes by type"""
        results = []
        count = 0
        
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == node_type:
                result = dict(data)
                result['node_id'] = node
                results.append(result)
                count += 1
                if count >= limit:
                    break
        
        return results
    
    def search_nodes_by_attribute(self, attribute: str, value: Any, limit: int = 100) -> List[Dict[str, Any]]:
        """Search nodes by attribute value"""
        results = []
        count = 0
        
        for node, data in self.graph.nodes(data=True):
            if data.get(attribute) == value:
                result = dict(data)
                result['node_id'] = node
                results.append(result)
                count += 1
                if count >= limit:
                    break
        
        return results
    
    def find_paths(self, source: str, target: str, max_paths: int = 5, cutoff: int = 10) -> List[List[str]]:
        """Find paths between two nodes"""
        if not self.graph.has_node(source) or not self.graph.has_node(target):
            return []
        
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=cutoff))
            return paths[:max_paths]
        except nx.NetworkXNoPath:
            return []
    
    def get_subgraph(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get subgraph around a node"""
        if not self.graph.has_node(node_id):
            return {'nodes': [], 'edges': []}
        
        # BFS to get nodes within depth (using deque for O(1) pop)
        visited = {node_id}
        queue = deque([(node_id, 0)])
        
        while queue:
            current, current_depth = queue.popleft()
            if current_depth < depth:
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_depth + 1))
                
                for neighbor in self.graph.predecessors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_depth + 1))
        
        # Extract subgraph
        subgraph = self.graph.subgraph(visited)
        
        nodes = []
        for node in subgraph.nodes():
            node_data = dict(self.graph.nodes[node])
            node_data['node_id'] = node
            nodes.append(node_data)
        
        edges = []
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'relationship': data.get('relationship', 'UNKNOWN'),
                **data
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
    
    def get_order_flow(self, sales_order_id: str) -> Dict[str, Any]:
        """Get complete order-to-cash flow for a sales order"""
        order_node = f"SalesOrder:{sales_order_id}"
        
        if not self.graph.has_node(order_node):
            return None
        
        flow = {
            'order': self.get_node(order_node),
            'items': [],
            'deliveries': [],
            'invoices': [],
            'payments': [],
            'customer': None
        }
        
        # Get order items
        for succ in self.graph.successors(order_node):
            if succ.startswith('SalesOrderItem:'):
                flow['items'].append(self.get_node(succ))
        
        # Get deliveries
        for pred in self.graph.predecessors(order_node):
            if pred.startswith('Delivery:'):
                flow['deliveries'].append(self.get_node(pred))
        
        # Get invoices
        for pred in self.graph.predecessors(order_node):
            if pred.startswith('Invoice:'):
                flow['invoices'].append(self.get_node(pred))
        
        # Check invoices via deliveries
        invoice_ids = {inv['node_id'] for inv in flow['invoices']}
        for delivery in flow['deliveries']:
            delivery_id = delivery['node_id']
            for pred in self.graph.predecessors(delivery_id):
                if pred.startswith('Invoice:'):
                    if pred not in invoice_ids:
                        invoice_data = self.get_node(pred)
                        flow['invoices'].append(invoice_data)
                        invoice_ids.add(pred)
        
        # Get customer
        order_data = flow['order']
        customer_id = order_data.get('sold_to_party')
        if customer_id:
            customer_node = f"Customer:{customer_id}"
            flow['customer'] = self.get_node(customer_node)
            
            # Get customer payments
            for pred in self.graph.predecessors(customer_node):
                if pred.startswith('Payment:'):
                    flow['payments'].append(self.get_node(pred))
        
        return flow
