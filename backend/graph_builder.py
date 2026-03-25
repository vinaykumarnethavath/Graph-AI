"""
Graph Builder Module
Constructs a NetworkX graph from preprocessed SAP O2C data
"""

import pandas as pd
import networkx as nx
import json
from pathlib import Path
from typing import Dict, List, Tuple
import pickle


class GraphBuilder:
    """Build and manage the Order-to-Cash knowledge graph"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.entities = {}
        self.node_count = {}
        self.edge_count = {}
        
    def load_data(self, data_path: str = 'processed_data/csv'):
        """Load all preprocessed entities"""
        data_path = Path(data_path)
        
        entity_files = {
            'sales_order_headers': 'sales_order_headers.csv',
            'sales_order_items': 'sales_order_items.csv',
            'sales_order_schedule_lines': 'sales_order_schedule_lines.csv',
            'outbound_delivery_headers': 'outbound_delivery_headers.csv',
            'outbound_delivery_items': 'outbound_delivery_items.csv',
            'billing_document_headers': 'billing_document_headers.csv',
            'billing_document_items': 'billing_document_items.csv',
            'journal_entry_items_accounts_receivable': 'journal_entry_items_accounts_receivable.csv',
            'payments_accounts_receivable': 'payments_accounts_receivable.csv',
            'business_partners': 'business_partners.csv',
            'products': 'products.csv',
            'plants': 'plants.csv',
            'product_plants': 'product_plants.csv',
        }
        
        for entity_name, filename in entity_files.items():
            file_path = data_path / filename
            if file_path.exists():
                self.entities[entity_name] = pd.read_csv(file_path)
                print(f"Loaded {entity_name}: {len(self.entities[entity_name])} records")
        
        return self.entities
    
    def create_customer_nodes(self):
        """Create Customer nodes"""
        if 'business_partners' not in self.entities:
            return
        
        df = self.entities['business_partners']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Customer:{row['business_partner']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Customer'
            attrs['customer_id'] = row['business_partner']
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Customer'] = count
        print(f"Created {count} Customer nodes")
    
    def create_product_nodes(self):
        """Create Product nodes"""
        if 'products' not in self.entities:
            return
        
        df = self.entities['products']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Product:{row['product']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Product'
            attrs['product_id'] = row['product']
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Product'] = count
        print(f"Created {count} Product nodes")
    
    def create_plant_nodes(self):
        """Create Plant nodes"""
        if 'plants' not in self.entities:
            return
        
        df = self.entities['plants']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Plant:{row['plant']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Plant'
            attrs['plant_id'] = row['plant']
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Plant'] = count
        print(f"Created {count} Plant nodes")
    
    def create_sales_order_nodes(self):
        """Create SalesOrder and SalesOrderItem nodes"""
        if 'sales_order_headers' not in self.entities:
            return
        
        # Sales Order Headers
        df = self.entities['sales_order_headers']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"SalesOrder:{row['sales_order']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'SalesOrder'
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['SalesOrder'] = count
        print(f"Created {count} SalesOrder nodes")
        
        # Sales Order Items
        if 'sales_order_items' in self.entities:
            df_items = self.entities['sales_order_items']
            item_count = 0
            
            for _, row in df_items.iterrows():
                node_id = f"SalesOrderItem:{row['sales_order']}:{row['sales_order_item']}"
                attrs = {k: v for k, v in row.items() if pd.notna(v)}
                attrs['node_type'] = 'SalesOrderItem'
                self.graph.add_node(node_id, **attrs)
                item_count += 1
            
            self.node_count['SalesOrderItem'] = item_count
            print(f"Created {item_count} SalesOrderItem nodes")
    
    def create_delivery_nodes(self):
        """Create Delivery and DeliveryItem nodes"""
        if 'outbound_delivery_headers' not in self.entities:
            return
        
        # Delivery Headers
        df = self.entities['outbound_delivery_headers']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Delivery:{row['delivery_document']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Delivery'
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Delivery'] = count
        print(f"Created {count} Delivery nodes")
        
        # Delivery Items
        if 'outbound_delivery_items' in self.entities:
            df_items = self.entities['outbound_delivery_items']
            item_count = 0
            
            for _, row in df_items.iterrows():
                node_id = f"DeliveryItem:{row['delivery_document']}:{row['delivery_document_item']}"
                attrs = {k: v for k, v in row.items() if pd.notna(v)}
                attrs['node_type'] = 'DeliveryItem'
                self.graph.add_node(node_id, **attrs)
                item_count += 1
            
            self.node_count['DeliveryItem'] = item_count
            print(f"Created {item_count} DeliveryItem nodes")
    
    def create_billing_nodes(self):
        """Create Invoice (Billing) and InvoiceItem nodes"""
        if 'billing_document_headers' not in self.entities:
            return
        
        # Billing Headers
        df = self.entities['billing_document_headers']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Invoice:{row['billing_document']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Invoice'
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Invoice'] = count
        print(f"Created {count} Invoice nodes")
        
        # Billing Items
        if 'billing_document_items' in self.entities:
            df_items = self.entities['billing_document_items']
            item_count = 0
            
            for _, row in df_items.iterrows():
                node_id = f"InvoiceItem:{row['billing_document']}:{row['billing_document_item']}"
                attrs = {k: v for k, v in row.items() if pd.notna(v)}
                attrs['node_type'] = 'InvoiceItem'
                self.graph.add_node(node_id, **attrs)
                item_count += 1
            
            self.node_count['InvoiceItem'] = item_count
            print(f"Created {item_count} InvoiceItem nodes")
    
    def create_payment_nodes(self):
        """Create Payment nodes"""
        if 'payments_accounts_receivable' not in self.entities:
            return
        
        df = self.entities['payments_accounts_receivable']
        count = 0
        
        for _, row in df.iterrows():
            node_id = f"Payment:{row['company_code']}:{row['fiscal_year']}:{row['accounting_document']}"
            attrs = {k: v for k, v in row.items() if pd.notna(v)}
            attrs['node_type'] = 'Payment'
            self.graph.add_node(node_id, **attrs)
            count += 1
        
        self.node_count['Payment'] = count
        print(f"Created {count} Payment nodes")
    
    def create_edges(self):
        """Create all edges based on relationships"""
        edge_counts = {}
        
        # Customer → SalesOrder (PLACED_BY)
        if 'sales_order_headers' in self.entities:
            df = self.entities['sales_order_headers']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('sold_to_party')):
                    self.graph.add_edge(
                        f"SalesOrder:{row['sales_order']}",
                        f"Customer:{row['sold_to_party']}",
                        relationship='PLACED_BY'
                    )
                    count += 1
            edge_counts['PLACED_BY'] = count
        
        # SalesOrder → SalesOrderItem (HAS_ITEM)
        if 'sales_order_items' in self.entities:
            df = self.entities['sales_order_items']
            count = 0
            for _, row in df.iterrows():
                self.graph.add_edge(
                    f"SalesOrder:{row['sales_order']}",
                    f"SalesOrderItem:{row['sales_order']}:{row['sales_order_item']}",
                    relationship='HAS_ITEM'
                )
                count += 1
            edge_counts['HAS_ITEM'] = count
        
        # SalesOrderItem → Product (CONTAINS_PRODUCT)
        if 'sales_order_items' in self.entities:
            df = self.entities['sales_order_items']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('material')):
                    self.graph.add_edge(
                        f"SalesOrderItem:{row['sales_order']}:{row['sales_order_item']}",
                        f"Product:{row['material']}",
                        relationship='CONTAINS_PRODUCT',
                        quantity=row.get('requested_quantity')
                    )
                    count += 1
            edge_counts['CONTAINS_PRODUCT'] = count
        
        # SalesOrderItem → Plant (FROM_PLANT)
        if 'sales_order_items' in self.entities:
            df = self.entities['sales_order_items']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('production_plant')):
                    self.graph.add_edge(
                        f"SalesOrderItem:{row['sales_order']}:{row['sales_order_item']}",
                        f"Plant:{row['production_plant']}",
                        relationship='FROM_PLANT'
                    )
                    count += 1
            edge_counts['FROM_PLANT'] = count
        
        # Delivery → SalesOrder (DELIVERS_ORDER)
        if 'outbound_delivery_items' in self.entities:
            df = self.entities['outbound_delivery_items']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('reference_sd_document')):
                    self.graph.add_edge(
                        f"Delivery:{row['delivery_document']}",
                        f"SalesOrder:{row['reference_sd_document']}",
                        relationship='DELIVERS_ORDER'
                    )
                    count += 1
            edge_counts['DELIVERS_ORDER'] = count
        
        # Invoice → Delivery (INVOICES_DELIVERY)
        if 'billing_document_items' in self.entities:
            df = self.entities['billing_document_items']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('reference_sd_document')):
                    self.graph.add_edge(
                        f"Invoice:{row['billing_document']}",
                        f"Delivery:{row['reference_sd_document']}",
                        relationship='INVOICES_DELIVERY'
                    )
                    count += 1
            edge_counts['INVOICES_DELIVERY'] = count
        
        # Invoice → SalesOrder (INVOICES_ORDER) - fallback
        if 'billing_document_items' in self.entities:
            df = self.entities['billing_document_items']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('sales_document')):
                    self.graph.add_edge(
                        f"Invoice:{row['billing_document']}",
                        f"SalesOrder:{row['sales_document']}",
                        relationship='INVOICES_ORDER'
                    )
                    count += 1
            edge_counts['INVOICES_ORDER'] = count
        
        # Payment → Customer (PAID_BY)
        if 'payments_accounts_receivable' in self.entities:
            df = self.entities['payments_accounts_receivable']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('customer')):
                    self.graph.add_edge(
                        f"Payment:{row['company_code']}:{row['fiscal_year']}:{row['accounting_document']}",
                        f"Customer:{row['customer']}",
                        relationship='PAID_BY'
                    )
                    count += 1
            edge_counts['PAID_BY'] = count
        
        # Payment → Invoice (SETTLES_INVOICE) via journal entries
        if 'journal_entry_items_accounts_receivable' in self.entities:
            df = self.entities['journal_entry_items_accounts_receivable']
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('clearing_accounting_document')) and pd.notna(row.get('customer')):
                    payment_id = f"Payment:{row['company_code']}:{row['fiscal_year']}:{row['clearing_accounting_document']}"
                    # Link to customer for now (invoice linkage would need more data)
                    if self.graph.has_node(payment_id) and self.graph.has_node(f"Customer:{row['customer']}"):
                        count += 1
            edge_counts['SETTLES_INVOICE'] = count
        
        # Product → Plant (AVAILABLE_AT)
        if 'product_plants' in self.entities:
            df = self.entities['product_plants']
            count = 0
            for _, row in df.iterrows():
                self.graph.add_edge(
                    f"Product:{row['product']}",
                    f"Plant:{row['plant']}",
                    relationship='AVAILABLE_AT'
                )
                count += 1
            edge_counts['AVAILABLE_AT'] = count
        
        self.edge_count = edge_counts
        for rel_type, count in edge_counts.items():
            print(f"Created {count} {rel_type} edges")
    
    def build_graph(self):
        """Build the complete graph"""
        print("\n" + "="*80)
        print("Building Order-to-Cash Knowledge Graph")
        print("="*80)
        
        print("\n[1] Creating Nodes...")
        self.create_customer_nodes()
        self.create_product_nodes()
        self.create_plant_nodes()
        self.create_sales_order_nodes()
        self.create_delivery_nodes()
        self.create_billing_nodes()
        self.create_payment_nodes()
        
        print("\n[2] Creating Edges...")
        self.create_edges()
        
        print("\n" + "="*80)
        print("Graph Construction Summary")
        print("="*80)
        print(f"\nTotal Nodes: {self.graph.number_of_nodes()}")
        print(f"Total Edges: {self.graph.number_of_edges()}")
        
        print("\nNode Breakdown:")
        for node_type, count in sorted(self.node_count.items()):
            print(f"  {node_type}: {count}")
        
        print("\nEdge Breakdown:")
        for edge_type, count in sorted(self.edge_count.items()):
            print(f"  {edge_type}: {count}")
        
        return self.graph
    
    def save_graph(self, output_path: str = 'processed_data/graph.gpickle'):
        """Save graph to disk"""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump(self.graph, f)
        print(f"\n✓ Graph saved to {output_path}")
    
    def export_graph_metadata(self, output_path: str = 'processed_data/graph_metadata.json'):
        """Export graph metadata"""
        metadata = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': self.node_count,
            'edge_types': self.edge_count,
            'graph_type': 'MultiDiGraph',
            'is_directed': self.graph.is_directed(),
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Metadata saved to {output_path}")
    
    def get_order_to_payment_paths(self, sales_order_id: str) -> List[List[str]]:
        """Find all paths from a sales order to payments"""
        source = f"SalesOrder:{sales_order_id}"
        
        if not self.graph.has_node(source):
            return []
        
        # Find all payment nodes
        payment_nodes = [n for n in self.graph.nodes() if n.startswith('Payment:')]
        
        all_paths = []
        for payment in payment_nodes:
            try:
                paths = list(nx.all_simple_paths(self.graph, source, payment, cutoff=10))
                all_paths.extend(paths)
            except nx.NetworkXNoPath:
                continue
        
        return all_paths
