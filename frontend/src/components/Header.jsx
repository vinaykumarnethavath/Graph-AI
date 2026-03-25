import { Database, GitBranch } from 'lucide-react'
import './Header.css'

export default function Header({ stats }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-breadcrumb">
          <span className="breadcrumb-main">Mapping</span>
          <span className="breadcrumb-separator">/</span>
          <span className="breadcrumb-sub">Order to Cash</span>
        </div>
        
        {stats && (
          <div className="header-meta">
            <span className="status-dot"></span>
            <span className="meta-text">
              {stats.total_nodes.toLocaleString()} nodes - {stats.total_edges.toLocaleString()} edges
            </span>
          </div>
        )}
      </div>
    </header>
  )
}
