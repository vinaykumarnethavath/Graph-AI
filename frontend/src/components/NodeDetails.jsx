import { X } from 'lucide-react'
import './NodeDetails.css'

export default function NodeDetails({ node, onClose }) {
  if (!node) return null

  const formatValue = (value) => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'string' && value.includes('T00:00:00')) {
      return new Date(value).toLocaleDateString()
    }
    return String(value)
  }

  const excludeKeys = ['node_id', 'node_type', 'in_degree', 'out_degree']
  const attributes = Object.entries(node)
    .filter(([key]) => !excludeKeys.includes(key))
    .sort(([a], [b]) => a.localeCompare(b))

  return (
    <div className="node-details">
      <div className="details-header">
        <div>
          <div className="details-type">{node.node_type}</div>
          <div className="details-id">{node.node_id}</div>
        </div>
        <button className="close-btn" onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      <div className="details-content">
        <div className="details-section">
          <h3>Connections</h3>
          <div className="connection-stats">
            <div>
              <span className="label">In-degree:</span>
              <span className="value">{node.in_degree || 0}</span>
            </div>
            <div>
              <span className="label">Out-degree:</span>
              <span className="value">{node.out_degree || 0}</span>
            </div>
          </div>
        </div>

        <div className="details-section">
          <h3>Attributes</h3>
          <div className="attributes">
            {attributes.map(([key, value]) => (
              <div key={key} className="attribute-row">
                <span className="attr-key">{formatKey(key)}</span>
                <span className="attr-value">{formatValue(value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function formatKey(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
