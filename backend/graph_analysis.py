"""
Graph Analysis and Visualization Module
"""

import networkx as nx
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class GraphAnalyzer:
    """Analyze the Order-to-Cash knowledge graph"""
    
    def __init__(self, graph_path: str = str(PROJECT_ROOT / 'dataset' / 'processed_data' / 'graph.gpickle')):
        import pickle
        with open(graph_path, 'rb') as f:
            self.graph = pickle.load(f)
        print(f"Loaded graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
    
    def trace_order_flow(self, sales_order_id: str):
        """Trace the complete Order → Delivery → Invoice → Payment flow"""
        order_node = f"SalesOrder:{sales_order_id}"
        
        if not self.graph.has_node(order_node):
            print(f"Order {sales_order_id} not found in graph")
            return
        
        flow = {
            'order': order_node,
            'items': [],
            'deliveries': [],
            'invoices': [],
            'payments': []
        }
        
        print(f"\n{'='*80}")
        print(f"Order Flow Trace: {sales_order_id}")
        print(f"{'='*80}")
        
        # Get order details
        order_data = self.graph.nodes[order_node]
        print(f"\n[1] SALES ORDER: {sales_order_id}")
        print(f"    Amount: {order_data.get('total_net_amount', 'N/A')} {order_data.get('transaction_currency', '')}")
        print(f"    Date: {order_data.get('creation_date', 'N/A')}")
        print(f"    Customer: {order_data.get('sold_to_party', 'N/A')}")
        
        # Get order items
        for succ in self.graph.successors(order_node):
            if succ.startswith('SalesOrderItem:'):
                flow['items'].append(succ)
                item_data = self.graph.nodes[succ]
                print(f"\n    Item {item_data.get('sales_order_item')}:")
                print(f"      Product: {item_data.get('material', 'N/A')}")
                print(f"      Quantity: {item_data.get('requested_quantity', 'N/A')} {item_data.get('requested_quantity_unit', '')}")
                print(f"      Amount: {item_data.get('net_amount', 'N/A')}")
        
        # Find deliveries
        print(f"\n[2] DELIVERIES:")
        for pred in self.graph.predecessors(order_node):
            if pred.startswith('Delivery:'):
                flow['deliveries'].append(pred)
                delivery_data = self.graph.nodes[pred]
                delivery_id = delivery_data.get('delivery_document')
                print(f"    Delivery {delivery_id}:")
                print(f"      Date: {delivery_data.get('creation_date', 'N/A')}")
                print(f"      Status: {delivery_data.get('overall_goods_movement_status', 'N/A')}")
        
        if not flow['deliveries']:
            print("    No deliveries found")
        
        # Find invoices
        print(f"\n[3] INVOICES:")
        for pred in self.graph.predecessors(order_node):
            if pred.startswith('Invoice:'):
                flow['invoices'].append(pred)
                invoice_data = self.graph.nodes[pred]
                invoice_id = invoice_data.get('billing_document')
                print(f"    Invoice {invoice_id}:")
                print(f"      Amount: {invoice_data.get('total_net_amount', 'N/A')} {invoice_data.get('transaction_currency', '')}")
                print(f"      Date: {invoice_data.get('creation_date', 'N/A')}")
        
        # Check via deliveries too
        for delivery in flow['deliveries']:
            for pred in self.graph.predecessors(delivery):
                if pred.startswith('Invoice:') and pred not in flow['invoices']:
                    flow['invoices'].append(pred)
                    invoice_data = self.graph.nodes[pred]
                    invoice_id = invoice_data.get('billing_document')
                    print(f"    Invoice {invoice_id} (via delivery):")
                    print(f"      Amount: {invoice_data.get('total_net_amount', 'N/A')} {invoice_data.get('transaction_currency', '')}")
                    print(f"      Date: {invoice_data.get('creation_date', 'N/A')}")
        
        if not flow['invoices']:
            print("    No invoices found")
        
        # Find payments
        print(f"\n[4] PAYMENTS:")
        customer_id = order_data.get('sold_to_party')
        if customer_id:
            customer_node = f"Customer:{customer_id}"
            for pred in self.graph.predecessors(customer_node):
                if pred.startswith('Payment:'):
                    flow['payments'].append(pred)
                    payment_data = self.graph.nodes[pred]
                    print(f"    Payment {payment_data.get('accounting_document')}:")
                    print(f"      Amount: {payment_data.get('amount_in_transaction_currency', 'N/A')} {payment_data.get('transaction_currency', '')}")
                    print(f"      Date: {payment_data.get('posting_date', 'N/A')}")
        
        if not flow['payments']:
            print("    No payments found for this customer")
        
        print(f"\n{'='*80}\n")
        return flow
    
    def get_all_order_flows(self):
        """Get flow statistics for all orders"""
        orders = [n for n in self.graph.nodes() if n.startswith('SalesOrder:')]
        
        flow_stats = []
        for order_node in orders:
            order_id = order_node.split(':')[1]
            order_data = self.graph.nodes[order_node]
            
            # Count related entities
            items = len([s for s in self.graph.successors(order_node) if s.startswith('SalesOrderItem:')])
            deliveries = len([p for p in self.graph.predecessors(order_node) if p.startswith('Delivery:')])
            invoices = len([p for p in self.graph.predecessors(order_node) if p.startswith('Invoice:')])
            
            # Get customer payments
            customer_id = order_data.get('sold_to_party')
            payments = 0
            if customer_id:
                customer_node = f"Customer:{customer_id}"
                payments = len([p for p in self.graph.predecessors(customer_node) if p.startswith('Payment:')])
            
            flow_stats.append({
                'sales_order': order_id,
                'amount': order_data.get('total_net_amount'),
                'currency': order_data.get('transaction_currency'),
                'items': items,
                'deliveries': deliveries,
                'invoices': invoices,
                'customer_payments': payments,
                'complete_flow': deliveries > 0 and invoices > 0 and payments > 0
            })
        
        return pd.DataFrame(flow_stats)
    
    def analyze_customer_behavior(self):
        """Analyze customer purchasing behavior"""
        customers = [n for n in self.graph.nodes() if n.startswith('Customer:')]
        
        customer_stats = []
        for customer_node in customers:
            customer_id = customer_node.split(':')[1]
            
            # Get orders
            orders = [p for p in self.graph.predecessors(customer_node) 
                     if p.startswith('SalesOrder:')]
            
            # Get payments
            payments = [p for p in self.graph.predecessors(customer_node) 
                       if p.startswith('Payment:')]
            
            # Calculate totals
            total_order_value = sum(
                self.graph.nodes[o].get('total_net_amount', 0) or 0 
                for o in orders
            )
            
            total_payment_value = sum(
                self.graph.nodes[p].get('amount_in_transaction_currency', 0) or 0 
                for p in payments
            )
            
            customer_stats.append({
                'customer_id': customer_id,
                'total_orders': len(orders),
                'total_order_value': total_order_value,
                'total_payments': len(payments),
                'total_payment_value': total_payment_value,
                'payment_rate': (total_payment_value / total_order_value * 100) if total_order_value > 0 else 0
            })
        
        return pd.DataFrame(customer_stats)
    
    def analyze_product_flow(self):
        """Analyze product flow through the O2C process"""
        products = [n for n in self.graph.nodes() if n.startswith('Product:')]
        
        product_stats = []
        for product_node in products:
            product_id = product_node.split(':')[1]
            product_data = self.graph.nodes[product_node]
            
            # Count orders
            order_items = [p for p in self.graph.predecessors(product_node) 
                          if p.startswith('SalesOrderItem:')]
            
            # Count plants
            plants = [s for s in self.graph.successors(product_node) 
                     if s.startswith('Plant:')]
            
            product_stats.append({
                'product_id': product_id,
                'product_type': product_data.get('product_type'),
                'product_group': product_data.get('product_group'),
                'times_ordered': len(order_items),
                'available_at_plants': len(plants)
            })
        
        return pd.DataFrame(product_stats)
    
    def export_analysis_reports(self, output_dir: str = 'processed_data/analysis'):
        """Export all analysis reports"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print("\nGenerating analysis reports...")
        
        # Order flow analysis
        order_flows = self.get_all_order_flows()
        order_flows.to_csv(output_dir / 'order_flow_analysis.csv', index=False)
        print(f"✓ Order flow analysis: {len(order_flows)} orders")
        
        # Customer behavior
        customer_stats = self.analyze_customer_behavior()
        customer_stats.to_csv(output_dir / 'customer_behavior.csv', index=False)
        print(f"✓ Customer behavior: {len(customer_stats)} customers")
        
        # Product flow
        product_stats = self.analyze_product_flow()
        product_stats.to_csv(output_dir / 'product_flow.csv', index=False)
        print(f"✓ Product flow: {len(product_stats)} products")
        
        print(f"\nReports saved to {output_dir}")
        return order_flows, customer_stats, product_stats


def main():
    print("Loading and analyzing graph...")
    analyzer = GraphAnalyzer()
    
    # Trace a sample order
    orders = [n.split(':')[1] for n in analyzer.graph.nodes() if n.startswith('SalesOrder:')]
    if orders:
        analyzer.trace_order_flow(orders[0])
    
    # Generate reports
    order_flows, customer_stats, product_stats = analyzer.export_analysis_reports()
    
    # Summary statistics
    print("\n" + "="*80)
    print("Analysis Summary")
    print("="*80)
    
    print(f"\nOrder Flow Completion:")
    print(f"  Orders with deliveries: {(order_flows['deliveries'] > 0).sum()}")
    print(f"  Orders with invoices: {(order_flows['invoices'] > 0).sum()}")
    print(f"  Complete flows: {order_flows['complete_flow'].sum()}")
    
    print(f"\nCustomer Statistics:")
    print(f"  Total customers: {len(customer_stats)}")
    print(f"  Average orders per customer: {customer_stats['total_orders'].mean():.2f}")
    print(f"  Average payment rate: {customer_stats['payment_rate'].mean():.2f}%")
    
    print(f"\nProduct Statistics:")
    print(f"  Total products: {len(product_stats)}")
    print(f"  Most ordered: {product_stats.nlargest(1, 'times_ordered')['product_id'].values[0]}")
    print(f"  Average plants per product: {product_stats['available_at_plants'].mean():.2f}")


if __name__ == "__main__":
    main()
