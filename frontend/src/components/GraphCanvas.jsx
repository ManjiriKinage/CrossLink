import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Maximize2, ZoomIn, ZoomOut, Play, Pause, Layers } from 'lucide-react';

const TYPE_COLORS = {
  PERSON: {
    background: '#1e3a8a',
    border: '#60a5fa',
    highlight: { background: '#2563eb', border: '#93c5fd' },
    font: { color: '#ffffff' }
  },
  LOCATION: {
    background: '#78350f',
    border: '#f59e0b',
    highlight: { background: '#d97706', border: '#fbbf24' },
    font: { color: '#ffffff' }
  },
  ORGANIZATION: {
    background: '#064e3b',
    border: '#34d399',
    highlight: { background: '#059669', border: '#6ee7b7' },
    font: { color: '#ffffff' }
  },
  DATE: {
    background: '#881337',
    border: '#f43f5e',
    highlight: { background: '#e11d48', border: '#fda4af' },
    font: { color: '#ffffff' }
  },
  UNKNOWN: {
    background: '#334155',
    border: '#94a3b8',
    highlight: { background: '#475569', border: '#cbd5e1' },
    font: { color: '#ffffff' }
  }
};

export default function GraphCanvas({ graphData, onSelectEdge, onSelectNode, selectedEdge, selectedNode }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [physicsEnabled, setPhysicsEnabled] = useState(true);

  useEffect(() => {
    if (!containerRef.current || !graphData || !graphData.nodes) return;

    // Prepare vis nodes
    const visNodes = graphData.nodes.map(node => {
      const typeStyle = TYPE_COLORS[node.type] || TYPE_COLORS.UNKNOWN;
      const isSelected = selectedNode === node.id;

      return {
        id: node.id,
        label: node.label || node.id,
        shape: 'box',
        margin: 10,
        color: {
          background: isSelected ? '#38bdf8' : typeStyle.background,
          border: isSelected ? '#ffffff' : typeStyle.border,
          highlight: typeStyle.highlight
        },
        font: {
          color: isSelected ? '#000000' : '#f8fafc',
          size: 13,
          face: 'Plus Jakarta Sans',
          bold: { color: '#ffffff' }
        },
        borderWidth: isSelected ? 3 : 1.5,
        shadow: {
          enabled: true,
          color: isSelected ? 'rgba(56, 189, 248, 0.6)' : 'rgba(0,0,0,0.5)',
          size: isSelected ? 15 : 6
        },
        entityType: node.type
      };
    });

    // Prepare vis edges
    const visEdges = graphData.edges.map((edge, idx) => {
      const isSelected = selectedEdge &&
        ((selectedEdge.source === edge.source && selectedEdge.target === edge.target) ||
         (selectedEdge.source === edge.target && selectedEdge.target === edge.source));

      const edgeWeight = edge.weight || 1.0;
      const docCount = edge.documents ? edge.documents.length : 1;

      return {
        id: `edge_${edge.source}_${edge.target}_${idx}`,
        from: edge.source,
        to: edge.target,
        width: isSelected ? 5 : Math.max(1.8, Math.min(6.5, edgeWeight * 1.4)),
        color: {
          color: isSelected ? '#f59e0b' : '#475569',
          highlight: '#fbbf24',
          hover: '#fbbf24'
        },
        label: edgeWeight > 1 ? `×${edgeWeight}` : undefined,
        font: {
          color: isSelected ? '#fbbf24' : '#94a3b8',
          size: 10,
          background: 'rgba(10, 13, 20, 0.85)',
          strokeWidth: 0
        },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.15
        },
        selectionWidth: 3,
        hoverWidth: 1.5,
        sourceEntity: edge.source,
        targetEntity: edge.target,
        rawEdge: edge
      };
    });

    const data = {
      nodes: new DataSet(visNodes),
      edges: new DataSet(visEdges)
    };

    const options = {
      physics: {
        enabled: physicsEnabled,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -70,
          centralGravity: 0.015,
          springLength: 120,
          springConstant: 0.08,
          damping: 0.85,
          avoidOverlap: 0.8
        },
        stabilization: {
          iterations: 150,
          updateInterval: 25
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        selectConnectedEdges: false,
        navigationButtons: false,
        keyboard: true
      }
    };

    const network = new Network(containerRef.current, data, options);
    networkRef.current = network;

    // Handle clicks
    network.on('click', (params) => {
      if (params.edges.length > 0 && params.nodes.length === 0) {
        // Direct Edge Clicked
        const edgeId = params.edges[0];
        const edgeObj = data.edges.get(edgeId);
        if (edgeObj && onSelectEdge) {
          onSelectEdge({
            source: edgeObj.sourceEntity,
            target: edgeObj.targetEntity,
            weight: edgeObj.rawEdge.weight,
            documents: edgeObj.rawEdge.documents
          });
        }
      } else if (params.nodes.length > 0) {
        // Node Clicked
        const nodeId = params.nodes[0];
        if (onSelectNode) {
          onSelectNode(nodeId);
        }
      } else {
        // Canvas clicked (deselect)
        if (onSelectEdge) onSelectEdge(null);
        if (onSelectNode) onSelectNode(null);
      }
    });

    return () => {
      network.destroy();
    };
  }, [graphData, selectedEdge, selectedNode, physicsEnabled]);

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.25 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale / 1.25 });
    }
  };

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
    }
  };

  const togglePhysics = () => {
    setPhysicsEnabled(prev => !prev);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: 'var(--bg-primary)' }}>
      {/* Network Canvas */}
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Control Buttons (Floating Top-Right) */}
      <div style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        background: 'rgba(19, 28, 46, 0.85)',
        backdropFilter: 'blur(8px)',
        border: '1px solid var(--border-dim)',
        borderRadius: '8px',
        padding: '6px',
        boxShadow: 'var(--shadow-md)',
        zIndex: 10
      }}>
        <button
          onClick={handleFit}
          className="btn-ghost"
          style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
          title="Fit Graph to Viewport"
        >
          <Maximize2 size={16} />
        </button>
        <button
          onClick={handleZoomIn}
          className="btn-ghost"
          style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
          title="Zoom In"
        >
          <ZoomIn size={16} />
        </button>
        <button
          onClick={handleZoomOut}
          className="btn-ghost"
          style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
          title="Zoom Out"
        >
          <ZoomOut size={16} />
        </button>
        <button
          onClick={togglePhysics}
          className="btn-ghost"
          style={{
            padding: '6px',
            borderRadius: '4px',
            cursor: 'pointer',
            color: physicsEnabled ? 'var(--accent-amber)' : 'var(--text-muted)'
          }}
          title={physicsEnabled ? "Freeze Physics" : "Enable Physics"}
        >
          {physicsEnabled ? <Pause size={16} /> : <Play size={16} />}
        </button>
      </div>

      {/* Legend (Floating Bottom-Left) */}
      <div style={{
        position: 'absolute',
        bottom: '16px',
        left: '16px',
        background: 'rgba(17, 24, 36, 0.88)',
        backdropFilter: 'blur(8px)',
        border: '1px solid var(--border-dim)',
        borderRadius: '8px',
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        boxShadow: 'var(--shadow-sm)',
        zIndex: 10
      }}>
        <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Entity Nodes:
        </span>
        <span className="badge badge-person">👤 Person</span>
        <span className="badge badge-location">📍 Location</span>
        <span className="badge badge-organization">🏢 Org</span>
        <span className="badge badge-date">📅 Date</span>
      </div>
    </div>
  );
}
