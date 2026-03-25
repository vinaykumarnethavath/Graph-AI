"""
Main script to build the Order-to-Cash knowledge graph
"""

import networkx as nx
from pathlib import Path
from backend.graph_builder import GraphBuilder


def main():
    project_root = Path(__file__).resolve().parent.parent
    processed_data_path = project_root / 'dataset' / 'processed_data'

    # Initialize graph builder
    builder = GraphBuilder()
    
    # Load preprocessed data
    print("Loading preprocessed data...")
    builder.load_data(str(processed_data_path / 'csv'))
    
    # Build the graph
    graph = builder.build_graph()
    
    # Save the graph
    builder.save_graph(str(processed_data_path / 'graph.gpickle'))
    builder.export_graph_metadata(str(processed_data_path / 'graph_metadata.json'))
    
    # Analyze Order → Delivery → Invoice → Payment flow
    print("\n" + "="*80)
    print("Analyzing Order-to-Cash Flow")
    print("="*80)
    
    # Find a sample order and trace its path
    sample_orders = [n for n in graph.nodes() if n.startswith('SalesOrder:')]
    if sample_orders:
        sample_order = sample_orders[0]
        order_id = sample_order.split(':')[1]
        
        print(f"\nTracing flow for {sample_order}:")
        
        # Get order details
        order_node = graph.nodes[sample_order]
        print(f"  Order Amount: {order_node.get('total_net_amount', 'N/A')} {order_node.get('transaction_currency', '')}")
        print(f"  Order Date: {order_node.get('creation_date', 'N/A')}")
        
        # Find connected deliveries
        deliveries = [n for n in graph.neighbors(sample_order) if 'Delivery:' in str(n)]
        delivery_in = [n for n, v, d in graph.in_edges(sample_order, data=True) if d.get('relationship') == 'DELIVERS_ORDER']
        
        # Check incoming edges for deliveries
        for pred in graph.predecessors(sample_order):
            if pred.startswith('Delivery:'):
                print(f"  → Delivered by: {pred}")
        
        # Find connected invoices
        for pred in graph.predecessors(sample_order):
            if pred.startswith('Invoice:'):
                invoice_node = graph.nodes[pred]
                print(f"  → Invoiced by: {pred}")
                print(f"     Invoice Amount: {invoice_node.get('total_net_amount', 'N/A')}")
                print(f"     Invoice Date: {invoice_node.get('creation_date', 'N/A')}")
        
        # Find paths to payments
        paths = builder.get_order_to_payment_paths(order_id)
        if paths:
            print(f"\n  Found {len(paths)} path(s) to payment")
            for i, path in enumerate(paths[:3], 1):
                print(f"\n  Path {i}: {' → '.join([n.split(':')[0] for n in path])}")
        else:
            print("\n  No complete path to payment found for this order")
    
    # Graph statistics
    print("\n" + "="*80)
    print("Graph Statistics")
    print("="*80)
    
    print(f"\nDensity: {nx.density(graph):.6f}")
    
    # Degree distribution
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    
    if in_degrees:
        avg_in = sum(in_degrees.values()) / len(in_degrees)
        max_in = max(in_degrees.values())
        print(f"\nIn-Degree: avg={avg_in:.2f}, max={max_in}")
    
    if out_degrees:
        avg_out = sum(out_degrees.values()) / len(out_degrees)
        max_out = max(out_degrees.values())
        print(f"Out-Degree: avg={avg_out:.2f}, max={max_out}")
    
    # Most connected nodes
    if in_degrees:
        top_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\nTop nodes by In-Degree:")
        for node, degree in top_in:
            node_type = graph.nodes[node].get('node_type', 'Unknown')
            print(f"  {node} ({node_type}): {degree}")
    
    print("\n" + "="*80)
    print("✓ Graph construction complete!")
    print("="*80)
    print(f"\nGraph file: {processed_data_path / 'graph.gpickle'}")
    print(f"Metadata: {processed_data_path / 'graph_metadata.json'}")
    print("\nUse 'graph_analysis.py' for advanced analysis and visualization")


if __name__ == "__main__":
    main()
