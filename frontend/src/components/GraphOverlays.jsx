import React from 'react';
import './GraphOverlays.css';

export function LegendOverlay({ nodeTypes }) {
  const colors = {
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
  };

  return (
    <div className="legend-overlay">
      <h3 className="legend-title">Node Types</h3>
      <div className="legend-items">
        {Object.entries(nodeTypes).map(([type, count]) => (
          <div key={type} className="legend-item">
            <span 
              className="legend-dot" 
              style={{ backgroundColor: colors[type] || '#94a3b8' }}
            ></span>
            <span className="legend-label">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function StatsOverlay({ totalNodes = 0, totalEdges = 0 }) {
  return (
    <div className="stats-overlay">
      <span className="stats-text">
        {(totalNodes || 0).toLocaleString()} nodes - {(totalEdges || 0).toLocaleString()} edges
      </span>
    </div>
  );
}
