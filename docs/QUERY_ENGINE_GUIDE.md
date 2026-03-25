# Query Engine Guide

## Overview

The Query Engine (`services/query_engine.py`) executes structured queries from the LLM on the graph database and returns standardized JSON responses with comprehensive edge case handling.

## Architecture

```
LLM Intent Extraction
        ↓
Structured Query (JSON)
        ↓
Query Engine Validation
        ↓
Route to Handler
        ↓
Execute on Graph
        ↓
Edge Case Detection
        ↓
Standardized JSON Response
```

## Supported Intents

1. **`get_details`** - Get specific entity by ID
2. **`search`** - Search entities by criteria
3. **`trace_flow`** - Trace Order-to-Cash flow
4. **`analytics`** - Compute aggregations and metrics
5. **`find_relationship`** - Find related entities
6. **`aggregate`** - Perform aggregations
7. **`detect_missing_links`** - Find incomplete records

## Response Format

All queries return this standardized format:

```json
{
  "success": true|false,
  "data": {...},
  "metadata": {
    "query": {...},
    "execution_time_ms": 123.45,
    "records_found": 10
  },
  "errors": ["error message"],
  "warnings": ["warning message"]
}
```

## 1. Get Details

### Query Structure

```json
{
  "intent": "get_details",
  "entity_type": "SalesOrder",
  "entity_id": "740506"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "node": {
      "node_id": "SalesOrder:740506",
      "sales_order": "740506",
      "total_net_amount": 17108.25,
      "transaction_currency": "INR",
      ...
    },
    "connections": {
      "total": 6,
      "in": 1,
      "out": 5
    },
    "edges": [...]
  },
  "metadata": {
    "execution_time_ms": 12.5,
    "records_found": 1
  },
  "errors": [],
  "warnings": []
}
```

### Edge Cases Handled

✅ **Invalid ID format** - Returns error
✅ **Non-existent entity** - Raises `EntityNotFoundException`
✅ **No connections** - Returns warning
✅ **Missing entity_type** - Infers from ID

### Example Code

```python
from services.query_engine import QueryEngine

query = {
    "intent": "get_details",
    "entity_type": "SalesOrder",
    "entity_id": "740506"
}

result = query_engine.execute(query)

if result["success"]:
    print(f"Order: {result['data']['node']['sales_order']}")
    print(f"Amount: {result['data']['node']['total_net_amount']}")
else:
    print(f"Error: {result['errors']}")
```

## 2. Search

### Query Structure

```json
{
  "intent": "search",
  "entity_type": "Customer",
  "entity_id": "310000108",
  "parameters": {
    "limit": 20
  }
}
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "node_id": "Customer:310000108",
      "business_partner": "310000108",
      ...
    }
  ],
  "metadata": {
    "records_found": 1
  },
  "warnings": []
}
```

### Edge Cases Handled

✅ **Duplicate results** - Automatically deduplicated
✅ **Empty results** - Returns warning
✅ **Large result sets** - Limited by parameters

### Example Code

```python
query = {
    "intent": "search",
    "entity_type": "SalesOrder",
    "entity_id": "740",  # Partial search
    "parameters": {"limit": 10}
}

result = query_engine.execute(query)

if result["warnings"]:
    print(f"Warnings: {result['warnings']}")

for order in result["data"]:
    print(f"Found: {order['node_id']}")
```

## 3. Trace Flow

### Query Structure

```json
{
  "intent": "trace_flow",
  "entity_type": "SalesOrder",
  "entity_id": "740506"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "order": {...},
    "items": [...],
    "deliveries": [...],
    "invoices": [...],
    "payments": [...],
    "customer": {...}
  },
  "warnings": [
    "Order has no invoices",
    "No payments found for this customer"
  ]
}
```

### Missing Link Detection

The engine automatically detects:

- ✅ Missing order items
- ✅ Missing deliveries
- ✅ Missing invoices
- ✅ Missing payments
- ✅ Missing customer info

### Edge Cases Handled

✅ **Incomplete flow** - Returns warnings for each missing step
✅ **Non-existent order** - Raises exception
✅ **Partial flow** - Returns available data with warnings

### Example Code

```python
query = {
    "intent": "trace_flow",
    "entity_type": "SalesOrder",
    "entity_id": "740506"
}

result = query_engine.execute(query)

flow = result["data"]

print(f"Order: {flow['order']['sales_order']}")
print(f"Items: {len(flow['items'])}")
print(f"Deliveries: {len(flow['deliveries'])}")
print(f"Invoices: {len(flow['invoices'])}")
print(f"Payments: {len(flow['payments'])}")

# Check for incomplete flow
if result["warnings"]:
    print("⚠️  Incomplete flow:")
    for warning in result["warnings"]:
        print(f"  - {warning}")
```

## 4. Analytics

### Query Structure

```json
{
  "intent": "analytics",
  "entity_type": "Customer",
  "entity_id": "310000108"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "customer": {...},
    "total_orders": 5,
    "total_order_value": 50000.0,
    "total_payments": 3,
    "total_payment_value": 45000.0,
    "payment_rate": 90.0,
    "orders": [...],
    "payments": [...]
  }
}
```

### Edge Cases Handled

✅ **No orders** - Returns 0 values
✅ **No payments** - Payment rate = 0%
✅ **Division by zero** - Safely handled

## 5. Find Relationship

### Query Structure

```json
{
  "intent": "find_relationship",
  "entity_type": "Invoice",
  "entity_id": "91150187",
  "parameters": {
    "target": "JournalEntry"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "source": "Invoice:91150187",
    "related_nodes": [
      {
        "node_id": "JournalEntry:...",
        "accounting_document": "9400635958",
        ...
      }
    ],
    "total_relationships": 1
  },
  "warnings": []
}
```

### Edge Cases Handled

✅ **No relationships** - Returns empty array with warning
✅ **Invalid target type** - Returns all relationships
✅ **Non-existent node** - Raises exception

## 6. Aggregate

### Query Structure

```json
{
  "intent": "aggregate",
  "entity_type": "SalesOrder",
  "parameters": {
    "aggregation": "sum",
    "field": "total_net_amount"
  }
}
```

### Supported Aggregations

- **`count`** - Count records
- **`sum`** - Sum numeric field
- **`avg`** - Average of field
- **`group_by`** - Group by field value

### Response Examples

**Count:**
```json
{
  "data": {
    "count": 100
  }
}
```

**Sum:**
```json
{
  "data": {
    "sum": 1234567.89,
    "field": "total_net_amount"
  }
}
```

**Average:**
```json
{
  "data": {
    "average": 12345.67,
    "field": "total_net_amount"
  }
}
```

**Group By:**
```json
{
  "data": {
    "groups": {
      "INR": 95,
      "USD": 5
    },
    "field": "transaction_currency"
  }
}
```

### Edge Cases Handled

✅ **No records** - Returns 0 or empty groups
✅ **Null values** - Treated as 0 for numeric ops
✅ **Invalid field** - Returns 0
✅ **Unsupported aggregation** - Raises error

## 7. Detect Missing Links

### Query Structure

```json
{
  "intent": "detect_missing_links",
  "entity_type": "SalesOrder"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "total_checked": 100,
    "missing_links": [
      {
        "node_id": "SalesOrder:740510",
        "missing": ["No delivery", "No customer"]
      },
      {
        "node_id": "SalesOrder:740511",
        "missing": ["No order items"]
      }
    ],
    "completeness_rate": 98.0
  },
  "warnings": [
    "Found 2 incomplete records"
  ]
}
```

### Checks Performed

For **SalesOrder**:
- ✅ Has order items
- ✅ Has customer
- ✅ Has delivery
- ✅ Has invoice

For **Delivery**:
- ✅ Has order reference

### Example Code

```python
query = {
    "intent": "detect_missing_links",
    "entity_type": "SalesOrder"
}

result = query_engine.execute(query)

print(f"Checked: {result['data']['total_checked']} orders")
print(f"Completeness: {result['data']['completeness_rate']}%")

for issue in result["data"]["missing_links"]:
    print(f"\n{issue['node_id']}:")
    for missing in issue["missing"]:
        print(f"  ⚠️  {missing}")
```

## Edge Case Handling

### 1. Missing Relationships

```python
# Automatically detected in trace_flow
result = query_engine.execute({
    "intent": "trace_flow",
    "entity_type": "SalesOrder",
    "entity_id": "740506"
})

# Check warnings
if "Order has no invoices" in result["warnings"]:
    print("⚠️  Order not yet invoiced")
```

### 2. Duplicate Data

```python
# Automatically deduplicated in search
result = query_engine.execute({
    "intent": "search",
    "entity_id": "740506"
})

# Check if duplicates were removed
if "Removed X duplicate results" in result["warnings"]:
    print("Duplicates found and removed")
```

### 3. Invalid IDs

```python
try:
    result = query_engine.execute({
        "intent": "get_details",
        "entity_type": "SalesOrder",
        "entity_id": "INVALID_ID"
    })
except EntityNotFoundException as e:
    print(f"Entity not found: {e}")

# Or check errors in response
if not result["success"]:
    for error in result["errors"]:
        print(f"Error: {error}")
```

### 4. Empty Results

```python
result = query_engine.execute({
    "intent": "search",
    "entity_id": "NONEXISTENT"
})

if result["metadata"]["records_found"] == 0:
    print("No results found")
    print(f"Warnings: {result['warnings']}")
```

## Complete Integration Example

```python
from services.graph_service import GraphService
from services.query_service import QueryService
from services.query_engine import QueryEngine
from services.llm_service import LLMService

# Initialize services
graph_svc = GraphService("processed_data/graph.gpickle")
query_svc = QueryService(graph_svc)
query_engine = QueryEngine(graph_svc, query_svc)
llm_svc = LLMService("your_groq_api_key")

# User input
user_query = "Find the invoices for order 740506"

# 1. LLM extracts intent
intent = llm_svc.extract_query_intent(user_query, {})

# 2. Execute on graph
result = query_engine.execute(intent)

# 3. Check result
if result["success"]:
    print(f"Found {result['metadata']['records_found']} results")
    print(f"Execution time: {result['metadata']['execution_time_ms']}ms")
    
    # Display data
    print(json.dumps(result["data"], indent=2))
    
    # Check warnings
    for warning in result["warnings"]:
        print(f"⚠️  {warning}")
else:
    # Handle errors
    for error in result["errors"]:
        print(f"❌ {error}")
```

## Error Hierarchy

```
QueryEngineException
  ├── InvalidQueryException
  │     ├── Missing intent
  │     ├── Unsupported intent
  │     ├── Missing required field
  │     └── Invalid parameters
  └── EntityNotFoundException
        ├── Node not found
        └── Invalid node ID
```

## Best Practices

✅ **Always check `success` field** before using data  
✅ **Log warnings** for monitoring  
✅ **Handle empty results** gracefully  
✅ **Use try/except** for exceptions  
✅ **Set appropriate limits** for large queries  
✅ **Monitor execution times** for performance  
✅ **Check metadata** for query statistics  

## Performance Monitoring

```python
result = query_engine.execute(query)

# Check execution time
if result["metadata"]["execution_time_ms"] > 1000:
    print("⚠️  Slow query detected")

# Check result size
if result["metadata"]["records_found"] > 1000:
    print("⚠️  Large result set")
```

## Testing

```python
# Test all intents
test_queries = [
    {"intent": "get_details", "entity_type": "SalesOrder", "entity_id": "740506"},
    {"intent": "search", "entity_id": "740"},
    {"intent": "trace_flow", "entity_type": "SalesOrder", "entity_id": "740506"},
    {"intent": "analytics", "entity_type": "Customer", "entity_id": "310000108"},
    {"intent": "aggregate", "entity_type": "SalesOrder", "parameters": {"aggregation": "count"}},
    {"intent": "detect_missing_links", "entity_type": "SalesOrder"}
]

for query in test_queries:
    result = query_engine.execute(query)
    print(f"Intent: {query['intent']}")
    print(f"Success: {result['success']}")
    print(f"Time: {result['metadata']['execution_time_ms']}ms")
    print()
```
