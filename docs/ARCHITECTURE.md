# Order-to-Cash Graph AI Architecture

## Overview

A layered architecture for querying and analyzing the Order-to-Cash knowledge graph using AI-powered natural language understanding.

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                    │
│            (api/app.py)                         │
│  - REST endpoints                               │
│  - Request/response handling                    │
│  - Error handling                               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│               LLM Layer                         │
│         (services/llm_service.py)               │
│  - Groq API integration                         │
│  - Intent extraction                            │
│  - Natural language generation                  │
│  - Conversation management                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│             Query Layer                         │
│        (services/query_service.py)              │
│  - Complex graph queries                        │
│  - Business logic                               │
│  - Analytics aggregation                        │
│  - Document flow tracing                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            Graph Layer                          │
│        (services/graph_service.py)              │
│  - NetworkX operations                          │
│  - Node/edge queries                            │
│  - Path finding                                 │
│  - Subgraph extraction                          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Knowledge Graph                        │
│       (processed_data/graph.gpickle)            │
│  - 1,139 nodes                                  │
│  - 4,139 edges                                  │
│  - Order-to-Cash entities                       │
└─────────────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Backend (`api/app.py`)

**Responsibilities:**
- HTTP endpoint exposure
- Request validation (Pydantic models)
- Service orchestration
- Error handling and logging
- CORS configuration

**Key Endpoints:**
- `GET /health` - Health check
- `GET /api/graph/stats` - Graph statistics
- `POST /api/graph/node` - Get node details
- `POST /api/graph/search` - Search nodes
- `POST /api/query/order-flow` - Trace order flow
- `POST /api/chat` - AI chat interface

### 2. LLM Layer (`services/llm_service.py`)

**Responsibilities:**
- Groq API integration (Llama 3.3 70B)
- Natural language understanding
- Intent extraction from user queries
- Response generation
- Conversation history management

**Key Methods:**
- `extract_query_intent()` - Parse user query to structured intent
- `generate_response()` - Convert query results to natural language
- `chat()` - General conversation interface
- `clear_history()` - Reset conversation

**Example Intent Extraction:**
```
User: "Find order 740506"
→ {
    "intent": "get_details",
    "entity_type": "SalesOrder",
    "entity_id": "740506",
    "question_type": "find"
  }
```

### 3. Query Layer (`services/query_service.py`)

**Responsibilities:**
- Business logic implementation
- Complex graph queries
- Multi-hop traversals
- Analytics computation
- Document flow analysis

**Key Methods:**
- `find_by_id()` - Find entity by type and ID
- `get_customer_orders()` - Customer order history
- `get_order_flow()` - Complete O2C flow
- `trace_document_flow()` - Document lifecycle
- `get_customer_analytics()` - Customer metrics
- `search_entities()` - Text-based search

### 4. Graph Layer (`services/graph_service.py`)

**Responsibilities:**
- NetworkX graph management
- Low-level graph operations
- Node/edge retrieval
- Path finding algorithms
- Subgraph extraction

**Key Methods:**
- `get_node()` - Retrieve node with attributes
- `get_node_neighbors()` - Get adjacent nodes
- `get_edges_for_node()` - Get connected edges
- `search_nodes_by_type()` - Filter by node type
- `find_paths()` - Find paths between nodes
- `get_subgraph()` - Extract local neighborhood

## Data Flow Example

### User Query: "Find the journal entry for billing document 91150187"

```
1. FastAPI receives POST /api/chat
   ↓
2. LLMService.extract_query_intent()
   → Intent: "find_relationship"
   → Entity: "Invoice:91150187"
   → Target: "JournalEntry"
   ↓
3. QueryService.find_journal_entry()
   → Searches for journal entries
   → Matches reference_sd_document
   ↓
4. GraphService.search_nodes_by_attribute()
   → Queries NetworkX graph
   → Returns matching nodes
   ↓
5. LLMService.generate_response()
   → Formats result
   → Generates natural language
   ↓
6. FastAPI returns ChatResponse
   → Response: "The journal entry number linked to billing document 91150187 is 9400635958."
   → query_result: {...}
```

## Configuration

### Environment Variables (`.env`)

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Application
APP_NAME=Order-to-Cash Graph AI
APP_VERSION=1.0.0
DEBUG=True

# Graph
GRAPH_PATH=processed_data/graph.gpickle
```

### Settings (`config.py`)

Uses `pydantic-settings` for type-safe configuration management.

## API Models (`models/schemas.py`)

**Request Models:**
- `ChatMessage` - Chat request
- `SearchQuery` - Search parameters
- `OrderFlowQuery` - Order flow request
- `DocumentFlowQuery` - Document trace request

**Response Models:**
- `ChatResponse` - AI response with results
- `GraphStats` - Graph statistics
- `SubgraphResponse` - Subgraph data
- `OrderFlowResponse` - Order flow data

**Enums:**
- `EntityType` - Valid entity types
- `QueryIntent` - Intent categories

## Separation of Concerns

| Layer | Concern | Dependencies |
|-------|---------|--------------|
| **API** | HTTP, validation, routing | FastAPI, Pydantic |
| **LLM** | NLU, NLG, conversation | Groq SDK |
| **Query** | Business logic, analytics | Graph Service |
| **Graph** | Graph operations | NetworkX, pickle |

## Running the Application

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Edit .env file
GROQ_API_KEY=your_actual_key_here
```

### 3. Start Server

```bash
python run_server.py
```

Server runs at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# Graph stats
curl http://localhost:8000/api/graph/stats

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find order 740506"}'
```

## Key Features

✓ **Layered Architecture** - Clear separation of concerns  
✓ **Type Safety** - Pydantic models throughout  
✓ **AI-Powered** - Groq LLM for natural language  
✓ **RESTful API** - Standard HTTP endpoints  
✓ **Auto Documentation** - Swagger UI at `/docs`  
✓ **Error Handling** - Comprehensive exception management  
✓ **Conversation Context** - Multi-turn dialogue support  
✓ **Graph Analytics** - Complex queries and analysis  

## Next Steps

1. **Frontend** - Build React UI for visualization
2. **Authentication** - Add API key/JWT authentication
3. **Caching** - Redis for query result caching
4. **Logging** - Structured logging with ELK stack
5. **Testing** - Unit and integration tests
6. **Deployment** - Docker containerization
7. **Monitoring** - Prometheus metrics
