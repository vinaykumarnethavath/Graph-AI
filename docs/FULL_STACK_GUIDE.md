# Full Stack Setup Guide

Complete guide to running the Order-to-Cash Graph AI application.

## Architecture

```
┌─────────────────────────────────────────┐
│   React Frontend (Port 3000)            │
│   - Graph Visualization (React Flow)    │
│   - Node Details Panel                  │
│   - AI Chat Interface                   │
└─────────────────────────────────────────┘
                  ↓ HTTP/REST
┌─────────────────────────────────────────┐
│   FastAPI Backend (Port 8000)           │
│   - Graph API Endpoints                 │
│   - LLM Integration (Groq)              │
│   - Business Logic                      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   NetworkX Knowledge Graph              │
│   - 1,139 nodes                         │
│   - 4,139 edges                         │
│   - Order-to-Cash process               │
└─────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 18+
- 4GB RAM minimum
- Modern web browser

### API Keys
- Groq API key (get from https://console.groq.com/keys)

## Step-by-Step Setup

### Part 1: Backend Setup

#### 1. Configure Environment

Create `.env` file in project root:

```env
GROQ_API_KEY=your_groq_api_key_here
APP_NAME=Order-to-Cash Graph AI
APP_VERSION=1.0.0
DEBUG=True
GRAPH_PATH=processed_data/graph.gpickle
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:
- FastAPI
- Uvicorn
- NetworkX
- Groq SDK
- Pydantic

#### 3. Verify Graph Data

Ensure graph file exists:
```bash
ls processed_data/graph.gpickle
```

If not, build it:
```bash
python build_graph.py
```

#### 4. Start Backend Server

```bash
python run_server.py
```

Expected output:
```
Starting up application...
Graph loaded: 1139 nodes, 4139 edges
Services initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 5. Verify Backend

Open browser: http://localhost:8000/docs

Test endpoint:
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status":"healthy","app":"Order-to-Cash Graph AI","version":"1.0.0"}
```

### Part 2: Frontend Setup

#### 1. Navigate to Frontend

```bash
cd frontend
```

#### 2. Install Dependencies

```bash
npm install
```

This installs:
- React 18
- React Flow (graph visualization)
- Axios (HTTP client)
- Lucide React (icons)
- Vite (build tool)

#### 3. Start Development Server

```bash
npm run dev
```

Expected output:
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

#### 4. Open Application

Navigate to: http://localhost:3000

You should see:
- Header with graph stats
- Interactive graph visualization
- Chat panel on the right
- Legend showing entity types

## Using the Application

### 1. Graph Interaction

**Click a Node:**
- Node details panel appears bottom-left
- Shows all attributes
- Displays connection count

**Navigate:**
- Drag to pan
- Scroll to zoom
- Use minimap for overview

**Colors:**
- Each entity type has unique color
- Legend shows all types

### 2. Chat Interface

**Example Queries:**

```
Find order 740506
Show me customer 310000108
Trace the flow of order 740506
Find the journal entry for billing document 91150187
Analyze customer 320000083
```

**Features:**
- AI understands natural language
- Results automatically highlighted
- Graph updates with relevant nodes
- Quick query buttons for common tasks

### 3. Node Details

When clicking a node, see:
- **Type**: Entity type (e.g., SalesOrder)
- **ID**: Full node identifier
- **Connections**: In-degree and out-degree
- **Attributes**: All node properties

### 4. Order-to-Cash Flow

Trace complete flow:
1. Chat: "Trace the flow of order 740506"
2. Graph highlights: Order → Items → Delivery → Invoice → Payment
3. Click each node for details
4. Red highlighting shows the path

## API Endpoints

### Graph Operations

```bash
# Get stats
GET /api/graph/stats

# Get node
POST /api/graph/node
{"node_id": "SalesOrder:740506"}

# Get subgraph
POST /api/graph/subgraph
{"node_id": "SalesOrder:740506", "depth": 2}

# Search
POST /api/graph/search
{"query": "740506", "limit": 20}
```

### Business Queries

```bash
# Order flow
POST /api/query/order-flow
{"sales_order_id": "740506"}

# Customer analytics
POST /api/query/customer-analytics
{"customer_id": "310000108"}

# Document flow
POST /api/query/document-flow
{"document_id": "91150187", "document_type": "Invoice"}
```

### AI Chat

```bash
# Chat
POST /api/chat
{"message": "Find order 740506"}

# Clear history
POST /api/chat/clear
```

## Project Structure

```
GraphAI/
├── Backend
│   ├── api/
│   │   └── app.py              # FastAPI application
│   ├── services/
│   │   ├── graph_service.py    # Graph operations
│   │   ├── query_service.py    # Business logic
│   │   └── llm_service.py      # Groq integration
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── config.py               # Configuration
│   ├── .env                    # Environment variables
│   └── run_server.py           # Server launcher
│
├── Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── GraphVisualization.jsx
│   │   │   ├── NodeDetails.jsx
│   │   │   └── ChatPanel.jsx
│   │   ├── api/
│   │   │   └── client.js       # API client
│   │   ├── App.jsx             # Main component
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   └── vite.config.js
│
└── Data
    ├── processed_data/
    │   ├── graph.gpickle       # NetworkX graph
    │   ├── csv/                # Clean CSV files
    │   └── parquet/            # Parquet files
    └── sap-o2c-data/           # Raw data
```

## Testing

### Backend Tests

```bash
python test_api.py
```

Expected: 7/7 tests passing

### Frontend Tests

1. Open http://localhost:3000
2. Click sample order node
3. Use chat: "Find order 740506"
4. Verify graph updates
5. Check node details panel

### Integration Tests

1. **Health Check**: Backend responds at /health
2. **Graph Load**: Frontend displays graph
3. **Node Click**: Details panel appears
4. **Chat Query**: Results highlight nodes
5. **API Call**: Chat sends to backend, receives response

## Troubleshooting

### Backend Issues

**"Graph file not found"**
```bash
python build_graph.py
```

**"Invalid Groq API key"**
- Check `.env` file
- Verify key at https://console.groq.com

**Port 8000 in use**
- Change port in `run_server.py`
- Update frontend proxy in `vite.config.js`

### Frontend Issues

**"Cannot connect to server"**
- Verify backend is running: `http://localhost:8000/health`
- Check CORS is enabled
- Clear browser cache

**Graph not rendering**
- Check browser console for errors
- Verify API returns data
- Try different browser

**Chat not working**
- Test backend directly: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'`
- Check Groq API quota
- Review backend logs

## Production Deployment

### Backend

```bash
# Using Gunicorn
gunicorn api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker
docker build -t graph-ai-backend .
docker run -p 8000:8000 --env-file .env graph-ai-backend
```

### Frontend

```bash
cd frontend
npm run build

# Serve with nginx or any static server
npx serve -s dist -l 3000
```

### Environment Variables (Production)

```env
GROQ_API_KEY=prod_key_here
DEBUG=False
GRAPH_PATH=/data/graph.gpickle
```

## Performance Tips

1. **Backend**:
   - Use Redis for caching
   - Limit subgraph depth
   - Implement pagination

2. **Frontend**:
   - Lazy load large graphs
   - Debounce API calls
   - Use React.memo for components

3. **Network**:
   - Enable gzip compression
   - Use CDN for static assets
   - Implement HTTP caching

## Security

1. **API Authentication**: Add JWT tokens
2. **Rate Limiting**: Implement request limits
3. **CORS**: Configure allowed origins
4. **API Keys**: Store in environment, never commit
5. **Input Validation**: All endpoints use Pydantic

## Next Steps

1. **Add authentication** - User login system
2. **Real-time collaboration** - WebSocket for multi-user
3. **Advanced analytics** - More graph algorithms
4. **Export features** - Download graph as image/PDF
5. **Custom layouts** - Force-directed, hierarchical
6. **Dark mode** - Theme switching
7. **Mobile responsive** - Touch-friendly UI

## Resources

- **Backend API Docs**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:3000
- **Groq Documentation**: https://console.groq.com/docs
- **React Flow Docs**: https://reactflow.dev
- **NetworkX Docs**: https://networkx.org

## Support

For issues:
1. Check logs (backend console, browser console)
2. Verify all services running
3. Test API endpoints directly
4. Review error messages carefully
