# Frontend Setup Guide

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

## Quick Start

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx           # Top header with stats
│   │   ├── GraphVisualization.jsx  # React Flow graph
│   │   ├── NodeDetails.jsx      # Node info panel
│   │   └── ChatPanel.jsx        # AI chat interface
│   ├── api/
│   │   └── client.js            # API client
│   ├── App.jsx                  # Main app component
│   ├── App.css
│   ├── main.jsx                 # Entry point
│   └── index.css
├── index.html
├── vite.config.js
└── package.json
```

## Features

### 1. Graph Visualization
- **Interactive graph** using React Flow
- **Click nodes** to see details
- **Pan and zoom** controls
- **Minimap** for navigation
- **Color-coded** by entity type

### 2. Node Details Panel
- Shows when clicking a node
- Displays all attributes
- Shows connection count
- Bottom-left overlay

### 3. Chat Interface
- **AI-powered** queries via Groq
- **Natural language** understanding
- **Quick query** buttons
- **Conversation history**
- **Auto-highlights** related nodes

### 4. Node Highlighting
- Results from chat queries highlighted in red
- Animated edges for highlighted paths
- Selected node has black border

## Entity Color Scheme

| Entity | Color |
|--------|-------|
| Customer | Green (#10b981) |
| SalesOrder | Blue (#3b82f6) |
| SalesOrderItem | Light Blue (#60a5fa) |
| Delivery | Orange (#f59e0b) |
| DeliveryItem | Light Orange (#fbbf24) |
| Invoice | Pink (#ec4899) |
| InvoiceItem | Light Pink (#f472b6) |
| Payment | Purple (#8b5cf6) |
| Product | Cyan (#06b6d4) |
| Plant | Teal (#14b8a6) |

## Usage Examples

### 1. Explore Graph
- **Click any node** to see details
- **Drag nodes** to rearrange
- **Zoom** with mouse wheel
- **Pan** by dragging background

### 2. Chat Queries
```
"Find order 740506"
"Show me customer 310000108"
"Trace the flow of order 740506"
"Find the journal entry for billing document 91150187"
```

### 3. Navigate Flow
- Chat query highlights relevant nodes
- Click highlighted nodes for details
- Graph automatically loads subgraph

## API Integration

All API calls go through `src/api/client.js`:

```javascript
import { api } from './api/client'

// Get graph stats
const stats = await api.getGraphStats()

// Get node details
const node = await api.getNode('SalesOrder:740506')

// Get subgraph
const subgraph = await api.getSubgraph('SalesOrder:740506', 2)

// Chat
const response = await api.chat('Find order 740506')
```

## Customization

### Change Colors

Edit `src/components/GraphVisualization.jsx`:

```javascript
const nodeColors = {
  Customer: '#your-color',
  // ... other colors
}
```

### Modify Layout

Edit `src/components/GraphVisualization.jsx`:

```javascript
// Change from circular to other layouts
const x = 400 + radius * Math.cos(angle)
const y = 400 + radius * Math.sin(angle)
```

### Adjust Chat Panel Width

Edit `src/components/ChatPanel.css`:

```css
.chat-panel {
  width: 400px; /* Change this */
}
```

## Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Troubleshooting

### Port Already in Use

Change port in `vite.config.js`:

```javascript
server: {
  port: 3001, // Change from 3000
}
```

### API Connection Issues

1. Verify backend is running: `http://localhost:8000/health`
2. Check CORS is enabled in backend
3. Update API URL in `src/api/client.js` if needed

### Graph Not Loading

1. Check console for errors
2. Verify graph file exists: `processed_data/graph.gpickle`
3. Ensure backend loaded successfully

### Chat Not Working

1. Verify Groq API key in backend `.env`
2. Check browser console for errors
3. Test backend directly: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'`

## Development Tips

### Hot Reload

Vite automatically reloads on file changes. Just save and see updates.

### Component Structure

- `Header` - Stateless, displays stats
- `GraphVisualization` - Manages React Flow state
- `NodeDetails` - Receives node data as prop
- `ChatPanel` - Manages chat state, calls API

### State Management

- `App.jsx` manages main state
- Child components receive props
- Callbacks flow data up

## Next Steps

1. **Add more layouts** - Force-directed, hierarchical
2. **Filter by entity type** - Show/hide nodes
3. **Export graph** - Download as image
4. **Search bar** - Quick node search
5. **Dark mode** - Theme toggle
6. **Real-time updates** - WebSocket integration

## Performance

- Graph limited to subgraphs (default depth=2)
- Only renders visible nodes
- Lazy loading for large graphs
- Debounced API calls

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
