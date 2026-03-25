"""
Example Usage: How to use the processed data for graph construction
"""

import pandas as pd
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = PROJECT_ROOT / 'dataset' / 'processed_data'


def load_processed_data(format='csv'):
    """Load processed data (csv or parquet)"""
    base_path = DATASET_ROOT / format
    
    entities = {}
    for file in base_path.glob(f'*.{format}'):
        entity_name = file.stem
        if format == 'csv':
            entities[entity_name] = pd.read_csv(file)
        else:
            entities[entity_name] = pd.read_parquet(file)
        print(f"Loaded {entity_name}: {len(entities[entity_name])} records")
    
    return entities


def load_relationship_metadata():
    """Load relationship metadata for graph construction"""
    with open(DATASET_ROOT / 'relationships.json', 'r') as f:
        metadata = json.load(f)
    return metadata


def example_graph_queries(entities):
    """Example queries on the processed data"""
    
    print("\n" + "="*80)
    print("Example 1: Sales Orders with Customer Information")
    print("="*80)
    
    # Join sales orders with customers
    orders = entities['sales_order_headers']
    customers = entities['business_partners']
    
    order_customer = orders.merge(
        customers,
        left_on='sold_to_party',
        right_on='business_partner',
        how='left'
    )
    
    print(order_customer[['sales_order', 'sold_to_party', 'business_partner', 
                           'total_net_amount', 'transaction_currency']].head())
    
    print("\n" + "="*80)
    print("Example 2: Order to Delivery to Billing Flow")
    print("="*80)
    
    # Get order items
    order_items = entities['sales_order_items']
    delivery_items = entities['outbound_delivery_items']
    billing_items = entities['billing_document_items']
    products = entities['products']
    
    # Join order items with products
    order_products = order_items.merge(
        products[['product', 'product_type', 'product_group']],
        left_on='material',
        right_on='product',
        how='left'
    )
    
    print(f"Total Sales Order Items: {len(order_items)}")
    print(f"Total Delivery Items: {len(delivery_items)}")
    print(f"Total Billing Items: {len(billing_items)}")
    print(f"\nProduct breakdown:")
    print(order_products['product_type'].value_counts())
    
    print("\n" + "="*80)
    print("Example 3: Payment Analysis")
    print("="*80)
    
    payments = entities['payments_accounts_receivable']
    
    # Aggregate payments by customer
    customer_payments = payments.groupby('customer').agg({
        'amount_in_transaction_currency': 'sum',
        'accounting_document': 'count'
    }).reset_index()
    customer_payments.columns = ['customer', 'total_amount', 'payment_count']
    
    print(customer_payments.head())
    print(f"\nTotal Payment Amount: {payments['amount_in_transaction_currency'].sum():,.2f}")
    
    print("\n" + "="*80)
    print("Example 4: Product-Plant Network")
    print("="*80)
    
    product_plants = entities['product_plants']
    
    print(f"Total Product-Plant relationships: {len(product_plants)}")
    print(f"Unique Products: {product_plants['product'].nunique()}")
    print(f"Unique Plants: {product_plants['plant'].nunique()}")
    
    # Products with most plant assignments
    top_products = product_plants['product'].value_counts().head()
    print("\nTop products by plant distribution:")
    print(top_products)


def export_for_neo4j(entities, metadata):
    """Example: Prepare data for Neo4j import"""
    output_path = DATASET_ROOT / 'neo4j_import'
    output_path.mkdir(exist_ok=True)
    
    # Example: Export nodes
    nodes = {
        'Customer': entities['business_partners'][['business_partner']].rename(
            columns={'business_partner': 'id'}
        ),
        'Product': entities['products'][['product', 'product_type', 'product_group']].rename(
            columns={'product': 'id'}
        ),
        'SalesOrder': entities['sales_order_headers'][['sales_order', 'total_net_amount']].rename(
            columns={'sales_order': 'id'}
        ),
        'Plant': entities['plants'][['plant']].rename(
            columns={'plant': 'id'}
        )
    }
    
    for node_type, df in nodes.items():
        df.to_csv(output_path / f'{node_type}_nodes.csv', index=False)
        print(f"Exported {node_type} nodes: {len(df)} records")
    
    # Example: Export relationships
    relationships = {
        'ORDERED_BY': entities['sales_order_headers'][['sales_order', 'sold_to_party']].rename(
            columns={'sales_order': 'from', 'sold_to_party': 'to'}
        ),
        'CONTAINS': entities['sales_order_items'][['sales_order', 'material']].rename(
            columns={'sales_order': 'from', 'material': 'to'}
        ),
        'LOCATED_AT': entities['product_plants'][['product', 'plant']].rename(
            columns={'product': 'from', 'plant': 'to'}
        )
    }
    
    for rel_type, df in relationships.items():
        df.to_csv(output_path / f'{rel_type}_relationships.csv', index=False)
        print(f"Exported {rel_type} relationships: {len(df)} records")


if __name__ == "__main__":
    print("Loading processed data...")
    entities = load_processed_data(format='csv')
    
    print("\nLoading relationship metadata...")
    metadata = load_relationship_metadata()
    
    print(f"\nPrimary Keys Defined: {len(metadata['primary_keys'])} entities")
    print(f"Foreign Key Relationships: {len(metadata['foreign_key_relationships'])} relationships")
    
    # Run example queries
    example_graph_queries(entities)
    
    # Prepare for Neo4j
    print("\n" + "="*80)
    print("Exporting for Neo4j...")
    print("="*80)
    export_for_neo4j(entities, metadata)
    
    print("\n✓ Examples completed!")
