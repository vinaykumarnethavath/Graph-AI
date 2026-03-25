# Order-to-Cash Knowledge Graph

## Graph Overview

**Successfully constructed NetworkX MultiDiGraph with:**
- **1,139 nodes** across 10 entity types
- **4,139 edges** representing 10 relationship types

## Node Types

| Node Type | Count | Description | ID Format |
|-----------|-------|-------------|-----------|
| Customer | 8 | Business partners | `Customer:{business_partner}` |
| Product | 69 | Materials/products | `Product:{product}` |
| Plant | 44 | Manufacturing/distribution plants | `Plant:{plant}` |
| SalesOrder | 100 | Sales order headers | `SalesOrder:{sales_order}` |
| SalesOrderItem | 167 | Line items in orders | `SalesOrderItem:{sales_order}:{item}` |
| Delivery | 86 | Outbound delivery headers | `Delivery:{delivery_document}` |
| DeliveryItem | 137 | Line items in deliveries | `DeliveryItem:{delivery_doc}:{item}` |
| Invoice | 163 | Billing documents | `Invoice:{billing_document}` |
| InvoiceItem | 245 | Line items in invoices | `InvoiceItem:{billing_doc}:{item}` |
| Payment | 120 | Payment records | `Payment:{company}:{year}:{doc}` |

## Relationship Types

| Relationship | Count | From → To | Description |
|--------------|-------|-----------|-------------|
| PLACED_BY | 100 | SalesOrder → Customer | Order placed by customer |
| HAS_ITEM | 167 | SalesOrder → SalesOrderItem | Order contains items |
| CONTAINS_PRODUCT | 167 | SalesOrderItem → Product | Item references product |
| FROM_PLANT | 167 | SalesOrderItem → Plant | Item from specific plant |
| DELIVERS_ORDER | 137 | Delivery → SalesOrder | Delivery fulfills order |
| INVOICES_DELIVERY | 245 | Invoice → Delivery | Invoice for delivery |
| PAID_BY | 120 | Payment → Customer | Payment from customer |
| AVAILABLE_AT | 3,036 | Product → Plant | Product available at plant |

## Order-to-Cash Flow

```
Customer
   ↓ (PLACED_BY)
SalesOrder
   ↓ (HAS_ITEM)
SalesOrderItem → Product (CONTAINS_PRODUCT)
   ↓              → Plant (FROM_PLANT)
Delivery (DELIVERS_ORDER)
   ↓
Invoice (INVOICES_DELIVERY)
   ↓
Payment (PAID_BY) → Customer
```

## Usage Examples

### 1. Load the Graph

```python
import pickle

# Load the graph
with open('processed_data/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)

print(f"Nodes: {graph.number_of_nodes()}")
print(f"Edges: {graph.number_of_edges()}")
```

### 2. Trace an Order Flow

```python
from graph_analysis import GraphAnalyzer

analyzer = GraphAnalyzer()
analyzer.trace_order_flow('740506')
```

### 3. Query Node Attributes

```python
# Get order details
order_attrs = graph.nodes['SalesOrder:740506']
print(f"Amount: {order_attrs['total_net_amount']}")
print(f"Currency: {order_attrs['transaction_currency']}")
print(f"Customer: {order_attrs['sold_to_party']}")
```

### 4. Find Relationships

```python
# Get all items in an order
order_items = [n for n in graph.successors('SalesOrder:740506') 
               if n.startswith('SalesOrderItem:')]

# Get customer's orders
customer_orders = [n for n in graph.predecessors('Customer:310000108')
                   if n.startswith('SalesOrder:')]

# Find deliveries for an order
deliveries = [n for n in graph.predecessors('SalesOrder:740506')
              if n.startswith('Delivery:')]
```

### 5. Network Analysis

```python
import networkx as nx

# Degree centrality
centrality = nx.degree_centrality(graph)
top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

# Find paths
paths = list(nx.all_simple_paths(graph, 
                                  'SalesOrder:740506', 
                                  'Customer:310000108',
                                  cutoff=5))
```

## Graph Files

- **`graph.gpickle`** - Serialized NetworkX graph (binary)
- **`graph_metadata.json`** - Graph statistics and metadata
- **`analysis/order_flow_analysis.csv`** - Order completion metrics
- **`analysis/customer_behavior.csv`** - Customer purchasing patterns
- **`analysis/product_flow.csv`** - Product distribution analysis

## Graph Statistics

- **Density**: 0.003193 (sparse graph)
- **Directed**: Yes (MultiDiGraph)
- **Average In-Degree**: 3.63
- **Average Out-Degree**: 3.63
- **Most Connected Node**: Plant:WB05 (179 connections)

## Next Steps

1. **Visualization**: Use matplotlib, plotly, or Gephi
2. **Graph Algorithms**: PageRank, community detection, shortest paths
3. **Export to Neo4j**: For scalable graph database storage
4. **Machine Learning**: Graph embeddings, link prediction
5. **Process Mining**: Analyze O2C process variants and bottlenecks

## Scripts Reference

- `build_graph.py` - Main graph construction script
- `graph_builder.py` - Graph builder module with all logic
- `graph_analysis.py` - Analysis and flow tracing utilities
- `example_usage.py` - Example queries and exports
