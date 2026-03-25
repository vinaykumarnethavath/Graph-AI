# API Guide - Order-to-Cash Graph AI

## Quick Start

### 1. Setup Environment

Create `.env` file with your Groq API key:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
APP_NAME=Order-to-Cash Graph AI
APP_VERSION=1.0.0
DEBUG=True
GRAPH_PATH=processed_data/graph.gpickle
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Server

```bash
python run_server.py
```

Server will start at: `http://localhost:8000`

### 4. Access API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Stats

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "app": "Order-to-Cash Graph AI",
  "version": "1.0.0"
}
```

#### Graph Statistics
```bash
GET /api/graph/stats
```

Response:
```json
{
  "total_nodes": 1139,
  "total_edges": 4139,
  "node_types": {
    "Customer": 8,
    "SalesOrder": 100,
    "Product": 69,
    ...
  },
  "is_directed": true
}
```

### Graph Queries

#### Get Node by ID
```bash
POST /api/graph/node
Content-Type: application/json

{
  "node_id": "SalesOrder:740506"
}
```

Response:
```json
{
  "node_id": "SalesOrder:740506",
  "node_type": "SalesOrder",
  "sales_order": "740506",
  "total_net_amount": "17108.25",
  "transaction_currency": "INR",
  "sold_to_party": "310000108",
  "creation_date": "2025-03-31T00:00:00.000Z",
  "in_degree": 1,
  "out_degree": 5
}
```

#### Get Node Neighbors
```bash
GET /api/graph/node/{node_id}/neighbors?direction=both
```

Example:
```bash
GET /api/graph/node/SalesOrder:740506/neighbors?direction=both
```

#### Search Nodes
```bash
POST /api/graph/search
Content-Type: application/json

{
  "query": "740506",
  "entity_types": ["SalesOrder"],
  "limit": 20
}
```

#### Get Subgraph
```bash
POST /api/graph/subgraph
Content-Type: application/json

{
  "node_id": "SalesOrder:740506",
  "depth": 2
}
```

### Business Queries

#### Get Order Flow
```bash
POST /api/query/order-flow
Content-Type: application/json

{
  "sales_order_id": "740506"
}
```

Response:
```json
{
  "order": {...},
  "items": [{...}, {...}],
  "deliveries": [{...}],
  "invoices": [],
  "payments": [],
  "customer": {...}
}
```

#### Get Customer Analytics
```bash
POST /api/query/customer-analytics
Content-Type: application/json

{
  "customer_id": "310000108"
}
```

#### Trace Document Flow
```bash
POST /api/query/document-flow
Content-Type: application/json

{
  "document_id": "91150187",
  "document_type": "Invoice"
}
```

#### Get Customer Orders
```bash
GET /api/query/customer/{customer_id}/orders
```

Example:
```bash
GET /api/query/customer/310000108/orders
```

#### Get Delivery Details
```bash
GET /api/query/delivery/{delivery_id}
```

Example:
```bash
GET /api/query/delivery/80737721
```

#### Get Invoice Details
```bash
GET /api/query/invoice/{billing_document}
```

Example:
```bash
GET /api/query/invoice/91150187
```

### AI Chat Interface

#### Chat with Graph AI
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Find order 740506",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "response": "I found sales order 740506. This order was placed by customer 310000108 on 2025-03-31 with a total amount of ₹17,108.25 INR. The order contains 5 items...",
  "session_id": "optional-session-id",
  "query_result": {
    "node_id": "SalesOrder:740506",
    ...
  }
}
```

**Example Chat Queries:**

```bash
# Find an order
POST /api/chat
{"message": "Show me order 740506"}

# Trace flow
POST /api/chat
{"message": "Trace the complete flow of order 740506"}

# Find journal entry (like in the screenshot)
POST /api/chat
{"message": "91150187 - Find the journal entry number linked to this?"}

# Customer analytics
POST /api/chat
{"message": "Analyze customer 310000108"}

# General search
POST /api/chat
{"message": "Find all orders for customer 320000083"}
```

#### Clear Chat History
```bash
POST /api/chat/clear
```

## Python Examples

### Using requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Get order flow
response = requests.post(
    f"{BASE_URL}/api/query/order-flow",
    json={"sales_order_id": "740506"}
)
flow = response.json()
print(f"Order has {len(flow['items'])} items")

# Chat
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={"message": "Find order 740506"}
)
print(response.json()["response"])
```

### Using Python SDK (httpx)

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Get stats
        response = await client.get("http://localhost:8000/api/graph/stats")
        stats = response.json()
        print(f"Graph has {stats['total_nodes']} nodes")
        
        # Chat
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "Show me customer 310000108"}
        )
        print(response.json()["response"])

asyncio.run(main())
```

## Testing

Run the test suite:

```bash
python test_api.py
```

Expected output:
```
[Test] Health Check
Status: 200
Response: {'status': 'healthy', ...}

[Test] Graph Statistics
Status: 200
Total Nodes: 1139
Total Edges: 4139

...

Test Results Summary
✓ PASS - Health Check
✓ PASS - Graph Stats
✓ PASS - Get Node
✓ PASS - Order Flow
✓ PASS - Search
✓ PASS - Chat - Basic
✓ PASS - Chat - Journal Entry

Passed: 7/7
```

## Entity Types

Available entity types for queries:

- `Customer` - Business partners
- `SalesOrder` - Sales order headers
- `SalesOrderItem` - Order line items
- `Delivery` - Outbound deliveries
- `DeliveryItem` - Delivery line items
- `Invoice` - Billing documents
- `InvoiceItem` - Invoice line items
- `Payment` - Payment transactions
- `Product` - Materials/products
- `Plant` - Manufacturing facilities

## Node ID Format

Entity IDs follow the pattern: `{EntityType}:{ID}`

Examples:
- `SalesOrder:740506`
- `Customer:310000108`
- `Invoice:91150187`
- `Delivery:80737721`
- `Product:S8907367001003`
- `Plant:1920`

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `404` - Entity not found
- `422` - Validation error
- `500` - Internal server error

Error response format:
```json
{
  "error": "Error message",
  "detail": "Additional details"
}
```

## Rate Limiting

No rate limiting is currently implemented. For production:
- Add rate limiting middleware
- Implement API key authentication
- Monitor Groq API usage

## Troubleshooting

### Server won't start

1. Check `.env` file exists with valid `GROQ_API_KEY`
2. Ensure graph file exists: `processed_data/graph.gpickle`
3. Check port 8000 is not in use

### Chat not working

1. Verify Groq API key is valid
2. Check Groq API quota/limits
3. Review server logs for errors

### Empty results

1. Verify entity ID exists in graph
2. Check node ID format: `EntityType:ID`
3. Use `/api/graph/stats` to see available entities

## Next Steps

1. **Frontend**: Build UI for graph visualization
2. **Auth**: Add API authentication
3. **WebSocket**: Real-time chat with streaming
4. **Cache**: Add Redis for query caching
5. **Deploy**: Docker + Kubernetes deployment
