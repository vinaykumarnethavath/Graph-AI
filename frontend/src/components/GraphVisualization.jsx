import { useCallback, useEffect, useState, useMemo } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow'
import { Layers } from 'lucide-react'
import { LegendOverlay, StatsOverlay } from './GraphOverlays'
import 'reactflow/dist/style.css'
import './GraphVisualization.css'

const nodeColors = {
  'SalesOrder': '#3b82f6',
  'SalesOrderItem': '#60a5fa',
  'Delivery': '#22c55e',
  'DeliveryItem': '#10b981',
  'BillingDocument': '#f59e0b',
  'BillingItem': '#fbbf24',
  'JournalEntry': '#8b5cf6',
  'Payment': '#f43f5e',
  'Customer': '#eab308',
  'Product': '#d946ef',
  'Plant': '#6366f1'
}

const getNodeColor = (nodeType) => nodeColors[nodeType] || '#94a3b8'

const visibleTypes = ['Customer', 'SalesOrder', 'Delivery', 'BillingDocument', 'Payment', 'JournalEntry']

const clusterAnchors = {
  Customer: { x: 420, y: 360 },
  SalesOrder: { x: 820, y: 520 },
  SalesOrderItem: { x: 1180, y: 420 },
  Delivery: { x: 1260, y: 820 },
  DeliveryItem: { x: 1460, y: 660 },
  BillingDocument: { x: 1640, y: 420 },
  BillingItem: { x: 1760, y: 620 },
  JournalEntry: { x: 620, y: 180 },
  Payment: { x: 1860, y: 880 },
  Product: { x: 2200, y: 500 },
  Plant: { x: 2360, y: 760 },
  Unknown: { x: 2000, y: 220 },
}

function hashString(value) {
  let hash = 0
  const str = String(value || '')
  for (let i = 0; i < str.length; i += 1) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

function getClusteredPositions(nodes) {
  const positions = new Map()
  const typeCounts = new Map()

  nodes.forEach((node) => {
    const nodeType = node.node_type || 'Unknown'
    typeCounts.set(nodeType, (typeCounts.get(nodeType) || 0) + 1)
  })

  const typeIndexes = new Map()

  nodes.forEach((node) => {
    const nodeType = node.node_type || 'Unknown'
    const anchor = clusterAnchors[nodeType] || clusterAnchors.Unknown
    const index = typeIndexes.get(nodeType) || 0
    const total = typeCounts.get(nodeType) || 1
    const hash = hashString(node.node_id)
    const ring = 28 + (index % 18) * 12 + (hash % 11)
    const angle = ((index / Math.max(total, 1)) * Math.PI * 2) + ((hash % 360) * Math.PI / 180)
    const driftX = ((Math.floor(hash / 7) % 21) - 10) * 3
    const driftY = ((Math.floor(hash / 17) % 21) - 10) * 3

    positions.set(node.node_id, {
      x: anchor.x + Math.cos(angle) * ring + driftX,
      y: anchor.y + Math.sin(angle) * ring + driftY,
    })

    typeIndexes.set(nodeType, index + 1)
  })

  return positions
}

export default function GraphVisualization({ 
  data, 
  selectedNode, 
  highlightedNodes = [],
  onNodeClick 
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [showGranular, setShowGranular] = useState(true)

  // Calculate node types for legend
  const nodeTypes = useMemo(() => {
    if (!data?.nodes) return {}
    const counts = {}
    data.nodes.forEach(n => {
      const type = n.node_type || 'Unknown'
      counts[type] = (counts[type] || 0) + 1
    })
    return counts
  }, [data])

  // Convert graph data to React Flow format
  useEffect(() => {
    if (!data?.nodes || data.nodes.length === 0) return

    const sourceNodes = showGranular
      ? data.nodes
      : data.nodes.filter((node) => visibleTypes.includes(node.node_type || 'Unknown'))
    const visibleNodeIds = new Set(sourceNodes.map((node) => node.node_id))
    const sourceEdges = data.edges.filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
    const positions = getClusteredPositions(sourceNodes)

    const flowNodes = sourceNodes.map((node) => {
      const nodeType = node.node_type || 'Unknown'
      const isSelected = node.node_id === selectedNode
      const isHighlighted = highlightedNodes.includes(node.node_id)
      
      const pos = positions.get(node.node_id) || { x: 0, y: 0 }
      return {
        id: node.node_id,
        data: { 
          label: '', 
          nodeType: nodeType,
        },
        position: pos,
        type: 'default',
        style: {
          background: getNodeColor(nodeType),
          width: isSelected ? 12 : isHighlighted ? 10 : 6,
          height: isSelected ? 12 : isHighlighted ? 10 : 6,
          borderRadius: '50%',
          border: isSelected ? '2px solid #1d4ed8' : isHighlighted ? '1.5px solid #60a5fa' : 'none',
          boxShadow: isSelected ? '0 0 0 5px rgba(59, 130, 246, 0.18)' : isHighlighted ? '0 0 0 3px rgba(96, 165, 250, 0.14)' : 'none',
          opacity: highlightedNodes.length === 0 || isHighlighted || isSelected ? 1 : 0.22,
          transition: 'all 0.3s ease-in-out'
        },
      }
    })

    const highlightedSet = new Set(highlightedNodes)
    const flowEdges = sourceEdges.map((edge, index) => {
      const isHighlighted = highlightedSet.has(edge.source) && highlightedSet.has(edge.target)
      return {
        id: `e-${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        type: 'simplebezier',
        style: {
          stroke: isHighlighted ? '#0ea5e9' : '#93c5fd',
          strokeWidth: isHighlighted ? 2.2 : 0.9,
          opacity: highlightedNodes.length === 0 ? 0.55 : isHighlighted ? 0.95 : 0.08,
        },
        animated: isHighlighted,
      }
    })

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [data, selectedNode, highlightedNodes, showGranular, setNodes, setEdges])

  const handleNodeClick = useCallback((event, node) => {
    onNodeClick(node.id)
  }, [onNodeClick])

  return (
    <div className="graph-visualization">
      <div className="graph-controls">
        <button className="control-btn" onClick={() => setShowGranular(!showGranular)}>
          <Layers size={14} />
          <span>{showGranular ? 'Hide Granular Overlay' : 'Show Granular Overlay'}</span>
        </button>
      </div>

      <LegendOverlay nodeTypes={nodeTypes} />
      {data && data.total_nodes !== undefined && (
        <StatsOverlay totalNodes={data.total_nodes} totalEdges={data.total_edges} />
      )}
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        minZoom={0.01}
        maxZoom={4}
        nodesDraggable={true}
        elementsSelectable={true}
        panOnDrag={true}
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          color="#eff6ff" 
          gap={36} 
          size={1}
          style={{ backgroundColor: '#ffffff' }}
        />
        <Controls 
          showInteractive={false}
          style={{ button: { background: '#ffffff', border: '1px solid #e5e7eb' } }}
        />
        <MiniMap
          nodeColor={(node) => node.style?.background || '#94a3b8'}
          maskColor="rgba(148, 163, 184, 0.15)"
          style={{ 
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px'
          }}
        />
      </ReactFlow>
    </div>
  )
}
