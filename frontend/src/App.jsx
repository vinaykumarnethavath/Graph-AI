import { useState, useCallback, useEffect } from 'react'
import GraphVisualization from './components/GraphVisualization'
import ChatPanel from './components/ChatPanel'
import NodeDetails from './components/NodeDetails'
import Header from './components/Header'
import { api } from './api/client'
import './App.css'

function collectNodeIds(value, ids = new Set()) {
  if (!value) {
    return ids
  }

  if (Array.isArray(value)) {
    value.forEach((item) => collectNodeIds(item, ids))
    return ids
  }

  if (typeof value === 'object') {
    if (typeof value.node_id === 'string' && value.node_id.length > 0) {
      ids.add(value.node_id)
    }

    Object.values(value).forEach((nestedValue) => collectNodeIds(nestedValue, ids))
  }

  return ids
}

function findFirstNodeObject(value) {
  if (!value) {
    return null
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const result = findFirstNodeObject(item)
      if (result) {
        return result
      }
    }
    return null
  }

  if (typeof value === 'object') {
    if (typeof value.node_id === 'string' && value.node_id.length > 0) {
      return value
    }

    for (const nestedValue of Object.values(value)) {
      const result = findFirstNodeObject(nestedValue)
      if (result) {
        return result
      }
    }
  }

  return null
}

function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [highlightedNodes, setHighlightedNodes] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load initial graph stats
  useEffect(() => {
    loadGraphStats()
  }, [])

  const loadGraphStats = async () => {
    try {
      const data = await api.getGraphStats()
      setStats(data)
      setLoading(false)
    } catch (error) {
      console.error('Error loading stats:', error)
      setLoading(false)
    }
  }

  // Handle node click
  const handleNodeClick = useCallback(async (nodeId) => {
    try {
      const node = await api.getNode(nodeId)
      setSelectedNode(node)
      
      // Get node neighbors to highlight
      const subgraph = await api.getSubgraph(nodeId, 1)
      const connectedIds = [
        nodeId,
        ...subgraph.nodes.filter(n => n.node_id !== nodeId).map(n => n.node_id)
      ]
      setHighlightedNodes(connectedIds)
    } catch (error) {
      console.error('Error loading node:', error)
    }
  }, [])

  // Handle chat query results
  const handleQueryResult = useCallback((result) => {
    if (!result) return

    const nodeIds = Array.from(collectNodeIds(result))
    setHighlightedNodes(nodeIds)

    const firstNode = findFirstNodeObject(result)
    if (firstNode) {
      setSelectedNode(firstNode)
    }
  }, [])

  // Load full graph on mount
  useEffect(() => {
    const loadFullGraph = async () => {
      try {
        const fullGraph = await api.getFullGraph()
        setGraphData(fullGraph)
        console.log(`Loaded full graph: ${fullGraph.total_nodes} nodes, ${fullGraph.total_edges} edges`)
      } catch (error) {
        console.error('Error loading full graph:', error)
      }
    }
    
    if (!loading && graphData.nodes.length === 0) {
      loadFullGraph()
    }
  }, [loading, graphData.nodes.length])

  return (
    <div className="app">
      <Header stats={stats} />
      
      <div className="main-content">
        <div className="graph-section">
          <GraphVisualization
            data={graphData}
            selectedNode={selectedNode?.node_id}
            highlightedNodes={highlightedNodes}
            onNodeClick={handleNodeClick}
          />
          
          {selectedNode && (
            <NodeDetails
              node={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          )}
        </div>
        
        <ChatPanel onQueryResult={handleQueryResult} />
      </div>
    </div>
  )
}

export default App
