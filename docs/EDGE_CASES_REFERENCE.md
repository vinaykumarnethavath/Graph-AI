# Edge Cases Reference Guide

## Overview

Comprehensive list of edge cases handled by the Query Engine with detection logic and handling strategies.

## 1. Missing Relationships

### Detection
```python
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
    
    return warnings
```

### Handling
- ✅ Returns partial data with warnings
- ✅ Highlights missing steps in flow
- ✅ Suggests next actions

### Example
```python
query = {
    "intent": "trace_flow",
    "entity_type": "SalesOrder",
    "entity_id": "740506"
}

result = query_engine.execute(query)

# Check for gaps
if result["warnings"]:
    print("Incomplete flow:")
    for warning in result["warnings"]:
        print(f"  - {warning}")
```

**Output:**
```
⚠️  Order has no invoices
⚠️  No payments found for this customer
```

## 2. Duplicate Data

### Detection
```python
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
```

### Handling
- ✅ Automatically deduplicates search results
- ✅ Warns user about removed duplicates
- ✅ Returns unique records only

### Example
```python
query = {"intent": "search", "entity_id": "740"}

result = query_engine.execute(query)

if "Removed X duplicate results" in result["warnings"]:
    print(f"Found duplicates, now showing {len(result['data'])} unique results")
```

## 3. Invalid IDs

### Detection
```python
# Check node ID format
if ':' not in node_id:
    raise InvalidQueryException(f"Invalid node ID format: {node_id}")

# Check if node exists
if not self.graph_service.graph.has_node(node_id):
    raise EntityNotFoundException(f"Node not found: {node_id}")
```

### Handling
- ✅ Validates ID format (EntityType:ID)
- ✅ Checks existence in graph
- ✅ Returns clear error message
- ✅ Does not crash application

### Example
```python
# Invalid format
query = {
    "intent": "get_details",
    "entity_type": "SalesOrder",
    "entity_id": "INVALID_ID"
}

result = query_engine.execute(query)

if not result["success"]:
    print(f"Error: {result['errors'][0]}")
    # Output: "Node not found: SalesOrder:INVALID_ID"
```

## 4. Empty Results

### Detection
```python
if not results:
    warnings.append("No results found for search query")

if result["metadata"]["records_found"] == 0:
    # Handle empty result set
```

### Handling
- ✅ Returns empty array with warning
- ✅ Sets records_found to 0
- ✅ Success remains true (query executed successfully)
- ✅ Provides helpful warning message

### Example
```python
query = {"intent": "search", "entity_id": "NONEXISTENT"}

result = query_engine.execute(query)

print(f"Success: {result['success']}")  # True
print(f"Records: {result['metadata']['records_found']}")  # 0
print(f"Warning: {result['warnings'][0]}")  # "No results found"
```

## 5. Missing Required Fields

### Detection
```python
def _validate_query(self, query: Dict[str, Any]):
    if 'intent' not in query:
        raise InvalidQueryException("Query must have 'intent' field")
    
    if query['intent'] not in self.supported_intents:
        raise InvalidQueryException(f"Unsupported intent: {query['intent']}")

# In handlers
if not entity_id:
    raise InvalidQueryException("entity_id is required for get_details")
```

### Handling
- ✅ Validates query structure
- ✅ Checks required fields per intent
- ✅ Returns specific error message
- ✅ Lists supported intents

### Example
```python
# Missing entity_id
query = {
    "intent": "get_details",
    "entity_type": "SalesOrder"
}

result = query_engine.execute(query)

print(result["errors"])
# ["entity_id is required for get_details"]
```

## 6. Null/None Values

### Detection
```python
# In aggregations
values = [float(n.get(field, 0) or 0) for n in nodes if n.get(field)]

# When creating attributes
attrs = {k: v for k, v in row.items() if pd.notna(v)}
```

### Handling
- ✅ Treats None as 0 for numeric operations
- ✅ Filters out null values in aggregations
- ✅ Skips null attributes when creating nodes
- ✅ Returns 0 or empty for missing fields

### Example
```python
# Sum with null values
query = {
    "intent": "aggregate",
    "entity_type": "SalesOrder",
    "parameters": {
        "aggregation": "sum",
        "field": "total_net_amount"
    }
}

result = query_engine.execute(query)
# Nulls treated as 0, sum is calculated from non-null values
```

## 7. Division by Zero

### Detection
```python
# Safe division
payment_rate = (total_payment / total_order * 100) if total_order > 0 else 0

# Average calculation
avg = sum(values) / len(values) if values else 0
```

### Handling
- ✅ Checks denominator before division
- ✅ Returns 0 or sensible default
- ✅ No exceptions raised

### Example
```python
# Customer with no orders
query = {
    "intent": "analytics",
    "entity_type": "Customer",
    "entity_id": "NEW_CUSTOMER"
}

result = query_engine.execute(query)

# payment_rate safely returns 0 instead of crashing
print(result["data"]["payment_rate"])  # 0
```

## 8. Circular References

### Detection
```python
# Limit search depth
subgraph = get_subgraph(node_id, depth=2)  # Max depth prevents infinite loops

# Path finding with cutoff
paths = nx.all_simple_paths(graph, source, target, cutoff=10)
```

### Handling
- ✅ Maximum depth limits
- ✅ Visited node tracking
- ✅ Cutoff parameters in path finding
- ✅ Prevents infinite loops

## 9. Large Result Sets

### Detection
```python
# Limit results
results = search_entities(query, entity_types, limit=20)

# Limit edges in response
"edges": edges[:10]  # First 10 only
```

### Handling
- ✅ Configurable limits
- ✅ Pagination support
- ✅ Returns subset with total count
- ✅ Prevents memory issues

### Example
```python
query = {
    "intent": "search",
    "entity_id": "S",  # Matches many products
    "parameters": {"limit": 5}
}

result = query_engine.execute(query)
print(f"Showing {len(result['data'])} of many results")
```

## 10. Unsupported Operations

### Detection
```python
if aggregation not in ['count', 'sum', 'avg', 'group_by']:
    raise InvalidQueryException(f"Unsupported aggregation: {aggregation}")

if entity_type != 'Customer':
    raise InvalidQueryException(f"Analytics not supported for {entity_type}")
```

### Handling
- ✅ Validates operation type
- ✅ Returns clear error message
- ✅ Lists supported operations
- ✅ Suggests alternatives

### Example
```python
query = {
    "intent": "aggregate",
    "entity_type": "SalesOrder",
    "parameters": {"aggregation": "median"}  # Not supported
}

result = query_engine.execute(query)
print(result["errors"])
# ["Unsupported aggregation: median"]
```

## 11. Malformed JSON

### Detection
```python
# In LLM service
try:
    intent = json.loads(content)
    return intent
except Exception as e:
    # Fallback to keyword extraction
    return self._fallback_intent_extraction(query)
```

### Handling
- ✅ Try/except around JSON parsing
- ✅ Fallback to keyword extraction
- ✅ Always returns valid structure
- ✅ Logs parsing errors

## 12. Connection Failures

### Detection
```python
try:
    response = self.client.chat.completions.create(...)
except Exception as e:
    # Fallback mechanism
    intent = self._fallback_intent_extraction(query)
```

### Handling
- ✅ Graceful degradation
- ✅ Fallback to keyword-based extraction
- ✅ Error logging
- ✅ User notification

## 13. Incomplete Data

### Detection
```python
def _check_order_completeness(self, order_id: str) -> List[str]:
    """Check if an order has all expected relationships"""
    gaps = []
    
    if not has_items:
        gaps.append("No order items")
    
    if not has_delivery:
        gaps.append("No delivery")
    
    if not has_customer:
        gaps.append("No customer")
    
    return gaps
```

### Handling
- ✅ Lists all missing components
- ✅ Returns partial data
- ✅ Provides completeness metrics
- ✅ Suggests remediation

### Example
```python
query = {"intent": "detect_missing_links", "entity_type": "SalesOrder"}

result = query_engine.execute(query)

print(f"Completeness: {result['data']['completeness_rate']}%")
for issue in result["data"]["missing_links"]:
    print(f"{issue['node_id']}: {issue['missing']}")
```

## 14. Timeout Scenarios

### Detection
```python
import time
start_time = time.time()

# Execute query

execution_time = (time.time() - start_time) * 1000

# Monitor in metadata
response["metadata"]["execution_time_ms"] = execution_time
```

### Handling
- ✅ Track execution time
- ✅ Return time in metadata
- ✅ Can implement timeouts if needed
- ✅ Performance monitoring

## Summary Table

| Edge Case | Detection | Handling | Status |
|-----------|-----------|----------|--------|
| Missing relationships | Flow analysis | Return partial + warnings | ✅ |
| Duplicate data | Set-based dedup | Auto-remove + warn | ✅ |
| Invalid IDs | Format + existence check | Return error | ✅ |
| Empty results | Count check | Return empty + warn | ✅ |
| Missing fields | Validation | Return error | ✅ |
| Null values | Conditional checks | Treat as 0 or skip | ✅ |
| Division by zero | Denominator check | Return 0 | ✅ |
| Circular refs | Depth limits | Prevent infinite loops | ✅ |
| Large results | Limit parameters | Paginate | ✅ |
| Unsupported ops | Type validation | Return error | ✅ |
| Malformed JSON | Try/catch | Fallback extraction | ✅ |
| Connection fails | Exception handling | Fallback mechanism | ✅ |
| Incomplete data | Completeness check | Return partial + report | ✅ |
| Timeouts | Time tracking | Monitor + metadata | ✅ |

## Testing Edge Cases

Run comprehensive tests:

```bash
python test_query_engine.py
```

This tests all edge cases automatically.
