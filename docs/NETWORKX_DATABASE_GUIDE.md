# NetworkX Database Layer Guide

## Overview

We use **NetworkX** as our graph database for the Order-to-Cash knowledge graph.

## Why NetworkX?

✅ **Simple**: Pure Python, no external database  
✅ **Efficient**: In-memory operations, fast queries  
✅ **Flexible**: Dynamic schema, easy to modify  
✅ **Powerful**: Built-in graph algorithms  
✅ **Portable**: Pickle-based persistence  

## 1. Schema Definition

### Node Types

```python
node_types = {
    'Customer': {
        'pk': 'business_partner',
        'attributes': ['organization_bp_name1', 'business_partner_category']
    },
    'SalesOrder': {
        'pk': 'sales_order',
        'attributes': ['total_net_amount', 'transaction_currency', 'creation_date']
    },
    'SalesOrderItem': {
        'pk': ['sales_order', 'sales_order_item'],
        'attributes': ['material', 'requested_quantity', 'net_amount']
    },
    'Delivery': {
        'pk': 'delivery_document',
        'attributes': ['creation_date', 'shipping_point']
    },
    'Invoice': {
        'pk': 'billing_document',
        'attributes': ['total_net_amount', 'billing_document_date']
    },
    'Payment': {
        'pk': ['company_code', 'fiscal_year', 'accounting_document'],
        'attributes': ['amount_in_transaction_currency', 'posting_date']
    },
    'Product': {
        'pk': 'product',
        'attributes': ['product_type', 'product_group', 'base_unit']
    },
    'Plant': {
        'pk': 'plant',
        'attributes': ['plant_name']
    }
}
```

### Relationship Types

```python
relationships = {
    'PLACED_BY': {
        'from': 'SalesOrder',
        'to': 'Customer',
        'cardinality': 'N:1'
    },
    'HAS_ITEM': {
        'from': 'SalesOrder',
        'to': 'SalesOrderItem',
        'cardinality': '1:N'
    },
    'CONTAINS_PRODUCT': {
        'from': 'SalesOrderItem',
        'to': 'Product',
        'cardinality': 'N:1'
    },
    'FROM_PLANT': {
        'from': 'SalesOrderItem',
        'to': 'Plant',
        'cardinality': 'N:1'
    },
    'DELIVERS_ORDER': {
        'from': 'Delivery',
        'to': 'SalesOrder',
        'cardinality': 'N:1'
    },
    'INVOICES_DELIVERY': {
        'from': 'Invoice',
        'to': 'Delivery',
        'cardinality': 'N:1'
    },
    'PAID_BY': {
        'from': 'Payment',
        'to': 'Customer',
        'cardinality': 'N:1'
    }
}
```

## 2. Graph Initialization

### Create Graph

```python
import networkx as nx

# Create directed multi-graph
graph = nx.MultiDiGraph()

print(f"Graph type: {type(graph).__name__}")
print(f"Is directed: {graph.is_directed()}")
```

### Why MultiDiGraph?

- **Directed**: Relationships have direction (Order → Customer)
- **Multi**: Multiple edges between same nodes
- **Supports**: Node/edge attributes

## 3. Insert Operations

### Insert Single Node

```python
# Method 1: Simple insert
graph.add_node('Customer:310000108', 
               node_type='Customer',
               business_partner='310000108',
               organization_bp_name1='ABC Corp')

# Method 2: From dictionary
node_data = {
    'node_type': 'SalesOrder',
    'sales_order': '740506',
    'total_net_amount': 17108.25,
    'transaction_currency': 'INR',
    'creation_date': '2025-03-31'
}
graph.add_node('SalesOrder:740506', **node_data)
```

### Insert Multiple Nodes

```python
# From DataFrame
import pandas as pd

df = pd.read_csv('processed_data/csv/sales_order_headers.csv')

for _, row in df.iterrows():
    node_id = f"SalesOrder:{row['sales_order']}"
    attrs = {k: v for k, v in row.items() if pd.notna(v)}
    attrs['node_type'] = 'SalesOrder'
    graph.add_node(node_id, **attrs)

print(f"Added {len(df)} nodes")
```

### Insert Edges

```python
# Simple edge
graph.add_edge('SalesOrder:740506', 
               'Customer:310000108',
               relationship='PLACED_BY')

# Edge with attributes
graph.add_edge('SalesOrderItem:740506:10',
               'Product:S8907367001003',
               relationship='CONTAINS_PRODUCT',
               quantity=48,
               unit='PC')

# Multiple edges
for _, row in df.iterrows():
    graph.add_edge(
        f"SalesOrder:{row['sales_order']}",
        f"Customer:{row['sold_to_party']}",
        relationship='PLACED_BY'
    )
```

## 4. Query Operations

### Basic Queries

```python
# Check if node exists
exists = graph.has_node('SalesOrder:740506')

# Get node attributes
node_data = graph.nodes['SalesOrder:740506']
print(f"Amount: {node_data['total_net_amount']}")

# Get all nodes of a type
sales_orders = [n for n in graph.nodes() 
                if graph.nodes[n].get('node_type') == 'SalesOrder']
print(f"Total orders: {len(sales_orders)}")
```

### Relationship Queries

```python
# Get neighbors (outgoing)
successors = list(graph.successors('SalesOrder:740506'))
print(f"Connected to: {successors}")

# Get neighbors (incoming)
predecessors = list(graph.predecessors('SalesOrder:740506'))
print(f"Connected from: {predecessors}")

# Get all neighbors
neighbors = list(graph.neighbors('SalesOrder:740506'))

# Get edges
edges = list(graph.edges('SalesOrder:740506', data=True))
for source, target, attrs in edges:
    print(f"{source} --[{attrs['relationship']}]--> {target}")
```

### Advanced Queries

```python
# Get subgraph (2-hop neighborhood)
def get_subgraph(graph, node_id, depth=2):
    visited = {node_id}
    queue = [(node_id, 0)]
    
    while queue:
        current, d = queue.pop(0)
        if d < depth:
            for neighbor in graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))
            
            for neighbor in graph.predecessors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))
    
    return graph.subgraph(visited)

subgraph = get_subgraph(graph, 'SalesOrder:740506', depth=2)
print(f"Subgraph: {subgraph.number_of_nodes()} nodes")
```

### Path Queries

```python
# Find paths
try:
    paths = list(nx.all_simple_paths(
        graph,
        'SalesOrder:740506',
        'Customer:310000108',
        cutoff=5
    ))
    print(f"Found {len(paths)} paths")
except nx.NetworkXNoPath:
    print("No path exists")

# Shortest path
try:
    path = nx.shortest_path(
        graph,
        'SalesOrder:740506',
        'Customer:310000108'
    )
    print(f"Shortest path: {' → '.join(path)}")
except:
    print("No path found")
```

### Search Queries

```python
# Search by attribute
def search_by_attribute(graph, attr, value):
    results = []
    for node, data in graph.nodes(data=True):
        if data.get(attr) == value:
            results.append(node)
    return results

# Find all orders for a customer
orders = search_by_attribute(graph, 'sold_to_party', '310000108')
print(f"Found {len(orders)} orders")

# Search by multiple attributes
def search_nodes(graph, **criteria):
    results = []
    for node, data in graph.nodes(data=True):
        match = all(data.get(k) == v for k, v in criteria.items())
        if match:
            results.append(node)
    return results

orders = search_nodes(
    graph,
    node_type='SalesOrder',
    transaction_currency='INR'
)
```

## 5. Update Operations

```python
# Update node attribute
graph.nodes['SalesOrder:740506']['status'] = 'Completed'

# Update multiple attributes
graph.nodes['SalesOrder:740506'].update({
    'status': 'Completed',
    'completed_date': '2025-04-01'
})

# Update edge attribute
for u, v, key, data in graph.edges(keys=True, data=True):
    if data['relationship'] == 'PLACED_BY':
        graph[u][v][key]['verified'] = True
```

## 6. Delete Operations

```python
# Delete node (and all connected edges)
graph.remove_node('SalesOrder:740506')

# Delete edge
graph.remove_edge('SalesOrder:740506', 'Customer:310000108')

# Delete nodes matching criteria
to_delete = [n for n in graph.nodes() 
             if graph.nodes[n].get('status') == 'Cancelled']
graph.remove_nodes_from(to_delete)
```

## 7. Persistence

### Save Graph

```python
import pickle

# Save to file
with open('processed_data/graph.gpickle', 'wb') as f:
    pickle.dump(graph, f)

print(f"Saved {graph.number_of_nodes()} nodes")
```

### Load Graph

```python
# Load from file
with open('processed_data/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)

print(f"Loaded {graph.number_of_nodes()} nodes")
```

### Export to Other Formats

```python
# Export to GraphML
nx.write_graphml(graph, 'graph.graphml')

# Export to JSON
import json
data = nx.node_link_data(graph)
with open('graph.json', 'w') as f:
    json.dump(data, f)

# Export to CSV
# Nodes
with open('nodes.csv', 'w') as f:
    f.write('node_id,node_type,attributes\n')
    for node, data in graph.nodes(data=True):
        f.write(f"{node},{data.get('node_type')},{data}\n")

# Edges
with open('edges.csv', 'w') as f:
    f.write('source,target,relationship\n')
    for u, v, data in graph.edges(data=True):
        f.write(f"{u},{v},{data.get('relationship')}\n")
```

## 8. Graph Algorithms

```python
# Degree centrality
centrality = nx.degree_centrality(graph)
top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
print("Most connected nodes:", top_nodes)

# PageRank
pagerank = nx.pagerank(graph)
top_important = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
print("Most important nodes:", top_important)

# Connected components (for undirected view)
undirected = graph.to_undirected()
components = list(nx.connected_components(undirected))
print(f"Number of components: {len(components)}")

# Clustering coefficient
clustering = nx.clustering(undirected)
avg_clustering = sum(clustering.values()) / len(clustering)
print(f"Average clustering: {avg_clustering}")
```

## 9. Performance Tips

```python
# Use views for large graphs
node_view = graph.nodes()  # Returns a view, not a copy
edge_view = graph.edges()

# Batch operations
nodes_to_add = [
    ('Node1', {'type': 'A'}),
    ('Node2', {'type': 'B'})
]
graph.add_nodes_from(nodes_to_add)

edges_to_add = [
    ('Node1', 'Node2', {'rel': 'CONNECTS'})
]
graph.add_edges_from(edges_to_add)

# Index commonly queried attributes
from collections import defaultdict
type_index = defaultdict(list)
for node, data in graph.nodes(data=True):
    node_type = data.get('node_type')
    type_index[node_type].append(node)

# Now O(1) lookup
sales_orders = type_index['SalesOrder']
```

## 10. Complete Example

```python
import networkx as nx
import pandas as pd
import pickle

# 1. Create graph
graph = nx.MultiDiGraph()

# 2. Load data
orders_df = pd.read_csv('processed_data/csv/sales_order_headers.csv')
customers_df = pd.read_csv('processed_data/csv/business_partners.csv')

# 3. Insert nodes
for _, row in customers_df.iterrows():
    node_id = f"Customer:{row['business_partner']}"
    attrs = {k: v for k, v in row.items() if pd.notna(v)}
    attrs['node_type'] = 'Customer'
    graph.add_node(node_id, **attrs)

for _, row in orders_df.iterrows():
    node_id = f"SalesOrder:{row['sales_order']}"
    attrs = {k: v for k, v in row.items() if pd.notna(v)}
    attrs['node_type'] = 'SalesOrder'
    graph.add_node(node_id, **attrs)

# 4. Insert edges
for _, row in orders_df.iterrows():
    graph.add_edge(
        f"SalesOrder:{row['sales_order']}",
        f"Customer:{row['sold_to_party']}",
        relationship='PLACED_BY'
    )

# 5. Query
order_node = graph.nodes['SalesOrder:740506']
print(f"Order amount: {order_node['total_net_amount']}")

customer_id = order_node['sold_to_party']
customer = graph.nodes[f"Customer:{customer_id}"]
print(f"Customer: {customer.get('organization_bp_name1')}")

# 6. Save
with open('graph.gpickle', 'wb') as f:
    pickle.dump(graph, f)

print(f"Graph saved: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
```

## Summary

✅ **Schema**: Flexible, attribute-based  
✅ **Insert**: Add nodes/edges with attributes  
✅ **Query**: Fast in-memory lookups  
✅ **Persistence**: Pickle-based, portable  
✅ **Algorithms**: Built-in graph algorithms  
✅ **Simple**: Pure Python, no setup  
✅ **Efficient**: O(1) node lookup, O(d) traversal  

**Perfect for medium-scale graphs (< 1M nodes)**
