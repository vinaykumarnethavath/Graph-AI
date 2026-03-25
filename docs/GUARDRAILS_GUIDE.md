# Guardrails Guide

## Overview

The Guardrails system prevents hallucinations, validates queries, and ensures the system only responds to Order-to-Cash queries.

## Architecture

```
User Query
    ↓
[1] Query Scope Validation
    ↓
LLM Intent Extraction
    ↓
[2] Intent Output Validation
    ↓
Query Execution
    ↓
[3] Result Validation
    ↓
LLM Response Generation
    ↓
[4] Response Sanitization
    ↓
User Response
```

## 5 Layers of Protection

### Layer 1: Query Scope Validation

**Validates BEFORE sending to LLM**

✅ **Accepts:**
- Order-to-Cash queries
- Entity IDs (numbers)
- Domain keywords (order, customer, delivery, etc.)

❌ **Rejects:**
- Weather, sports, news, politics
- General knowledge questions
- Personal advice
- Programming help (except this system)
- SQL injection attempts
- XSS attacks

**Example:**

```python
is_valid, msg = guardrails.validate_user_query("What's the weather?")
# Returns: (False, "This system only answers Order-to-Cash queries...")
```

### Layer 2: Intent Output Validation

**Validates LLM output BEFORE execution**

✅ **Checks:**
- Intent type is allowed
- Entity type exists in schema
- Entity ID format is valid
- No malicious patterns

❌ **Blocks:**
- Hallucinated intents
- Invalid entity types
- Malicious entity IDs
- Missing required fields

**Example:**

```python
intent = {
    "intent": "hack_system",  # Invalid
    "entity_type": "FakeEntity"  # Invalid
}

is_valid, msg = guardrails.validate_intent_output(intent)
# Returns: (False, "Invalid intent: hack_system...")
```

### Layer 3: Result Validation

**Validates query results BEFORE response generation**

✅ **Checks:**
- Result structure is correct
- Execution time is reasonable
- Success/error fields present
- Metadata is valid

❌ **Blocks:**
- Malformed results
- Timeouts (>30s)
- Missing metadata
- Inconsistent data

**Example:**

```python
result = {
    "success": True,
    "data": None,  # Invalid: no data + no warnings
    "metadata": {"execution_time_ms": 50000}  # Too high
}

is_valid, msg = guardrails.validate_query_result(result)
# Returns: (False, "Execution time too high...")
```

### Layer 4: Response Sanitization

**Cleans LLM response BEFORE returning to user**

✅ **Removes:**
- Script tags
- SQL commands
- Malicious content
- XSS attempts

✅ **Limits:**
- Response length (max 2000 chars)

**Example:**

```python
response = "Order 123 <script>alert('xss')</script> found"
sanitized = guardrails.sanitize_response(response)
# Returns: "Order 123  found"
```

### Layer 5: Strict System Prompts

**LLM is instructed to:**
- ONLY answer O2C queries
- REJECT out-of-scope questions
- NEVER hallucinate data
- USE only provided query results
- STATE clearly when data is missing

## Allowed Scope

### Entities
- Customer
- SalesOrder, SalesOrderItem
- Delivery, DeliveryItem
- Invoice, InvoiceItem
- Payment
- Product
- Plant
- JournalEntry

### Intents
- search
- get_details
- trace_flow
- analytics
- find_relationship
- aggregate
- detect_missing_links

### Domain Keywords
- order, orders, sales
- customer, customers
- delivery, deliveries
- invoice, invoices, billing
- payment, payments
- product, products
- plant, plants
- flow, trace, analytics

## Rejected Topics

❌ **Out of Scope:**
- weather, sports, politics, news
- music, movies, games
- programming, code (except this system)
- recipes, cooking
- health, medical, legal
- personal information
- cryptocurrency

## Usage Examples

### Valid Queries (Accepted)

```
✓ "Find order 740506"
✓ "Show me customer 310000108"
✓ "Trace the delivery flow"
✓ "What's the total value of all orders?"
✓ "Analyze customer purchasing patterns"
✓ "Find invoices for customer ABC"
```

### Invalid Queries (Rejected)

```
✗ "What's the weather today?"
   → "This system only answers Order-to-Cash queries..."

✗ "Tell me a joke"
   → "Cannot help with 'joke' related questions"

✗ "Who won the game?"
   → "This system only answers Order-to-Cash queries..."

✗ "'; DROP TABLE orders; --"
   → "Query contains potentially malicious content"
```

## Integration

### In FastAPI (`api/app.py`)

```python
@app.post("/api/chat")
async def chat(message, guardrails):
    # Step 1: Validate query
    is_valid, error_msg = guardrails.validate_user_query(message)
    if not is_valid:
        return rejection_response(error_msg)
    
    # Step 2: Extract intent
    intent = llm.extract_query_intent(message)
    
    # Check if LLM marked as out of scope
    if intent.get('intent') == 'out_of_scope':
        return rejection_response()
    
    # Step 3: Validate intent
    is_valid, error_msg = guardrails.validate_intent_output(intent)
    if not is_valid:
        return error_response(error_msg)
    
    # Step 4: Execute query
    result = query_engine.execute(intent)
    
    # Step 5: Validate result
    is_valid, error_msg = guardrails.validate_query_result(result)
    if not is_valid:
        return error_response(error_msg)
    
    # Step 6: Generate response
    response = llm.generate_response(message, result)
    
    # Step 7: Sanitize response
    response = guardrails.sanitize_response(response)
    
    return response
```

## Testing

Run comprehensive test suite:

```bash
python test_guardrails.py
```

Tests:
- ✓ Valid O2C queries (9 cases)
- ✓ Rejected queries (10 cases)
- ✓ SQL injection prevention (6 cases)
- ✓ Edge cases (3 cases)
- ✓ Intent validation (5 cases)
- ✓ Result validation (3 cases)
- ✓ Response sanitization (4 cases)
- ✓ Complete flow (2 scenarios)

## Security Features

### SQL Injection Prevention

Detects and blocks:
```
'; DROP TABLE orders; --
1' OR '1'='1
UNION SELECT * FROM users
DELETE FROM customers
```

### XSS Prevention

Removes:
```
<script>alert('xss')</script>
<img src=x onerror=alert(1)>
```

### Input Validation

Blocks:
- Empty queries
- Queries > 500 characters
- Invalid characters in entity IDs
- Malicious patterns

## Error Messages

### Out of Scope
```
"This system only answers Order-to-Cash queries. 
Cannot help with 'weather' related questions."
```

### Malicious Content
```
"Query contains potentially malicious content"
```

### Invalid Intent
```
"Invalid intent: hack_system. 
Allowed: search, get_details, trace_flow, analytics, 
find_relationship, aggregate, detect_missing_links"
```

### Invalid Entity Type
```
"Invalid entity_type: FakeEntity. 
Allowed: Customer, SalesOrder, Delivery, Invoice, 
Payment, Product, Plant"
```

## Standard Rejection Message

```
I can only help with Order-to-Cash queries related to:
• Sales Orders and Items
• Deliveries
• Invoices and Billing
• Payments
• Customers
• Products and Plants

Please ask about orders, customers, deliveries, invoices, or payments.
```

## Configuration

### Modify Allowed Entities

Edit `services/guardrails.py`:

```python
self.allowed_entities = {
    'Customer', 'SalesOrder', 'Delivery',
    'Invoice', 'Payment', 'Product', 'Plant',
    'YourNewEntity'  # Add here
}
```

### Add Domain Keywords

```python
self.domain_keywords = {
    'order', 'customer', 'delivery', 'invoice',
    'your_keyword'  # Add here
}
```

### Add Rejected Topics

```python
self.rejected_topics = {
    'weather', 'sports', 'politics',
    'your_rejected_topic'  # Add here
}
```

## Best Practices

✅ **Always validate** user input before LLM  
✅ **Always validate** LLM output before execution  
✅ **Always validate** query results before response  
✅ **Always sanitize** responses before returning  
✅ **Log rejections** for monitoring  
✅ **Use strict prompts** for LLM  
✅ **Test regularly** with new attack patterns  

## Monitoring

Track in production:
- Rejection rate
- Rejection reasons
- Malicious attempt patterns
- Common out-of-scope queries

## Example Logs

```
2026-03-25 18:00:01 - Rejected: "What's the weather?" - Out of scope
2026-03-25 18:00:15 - Rejected: "'; DROP TABLE--" - Malicious content
2026-03-25 18:01:30 - Rejected: "Tell me a joke" - Out of scope
```

## Performance Impact

- Query validation: ~1ms
- Intent validation: ~0.5ms
- Result validation: ~0.5ms
- Response sanitization: ~2ms

**Total overhead: ~4ms** (negligible)

## Summary

The guardrails system provides **5 layers of protection**:

1. **Query Scope Validation** - Blocks out-of-scope queries
2. **Intent Validation** - Prevents hallucinated intents
3. **Result Validation** - Ensures valid query execution
4. **Response Sanitization** - Removes malicious content
5. **Strict Prompts** - Instructs LLM to reject invalid queries

**Result:** System ONLY answers Order-to-Cash queries with actual data.
