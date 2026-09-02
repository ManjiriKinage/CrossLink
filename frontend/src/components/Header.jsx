import React from 'react';
import { Search, Database, RefreshCw, FolderArchive, Activity, Shield } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, onReloadDemo, isReloading, totalDocs, totalNodes }) {
  return (
    <header style={{
      width: '100%',
      maxWidth: '100vw',
      background: 'linear-gradient(180deg, #111827 0%, #0c101b 100%)',
      borderBottom: '1px solid var(--border-dim)',
      padding: '10px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px',
      boxSizing: 'border-box',
      zIndex: 20,
      flexShrink: 0
    }}>
      {/* Left: Branding */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: '220px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '9px',
          background: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px rgba(245, 158, 11, 0.4)',
          flexShrink: 0
        }}>
          <span style={{ fontSize: '20px' }}>🕵️</span>
        </div>
        <div style={{ overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '17px',
              fontWeight: '900',
              letterSpacing: '0.1em',
              color: 'var(--text-gold)',
              textTransform: 'uppercase',
              textShadow: '0 0 8px rgba(251, 191, 36, 0.3)',
              whiteSpace: 'nowrap'
            }}>
              Cold Case
            </span>
            <span style={{
              background: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--accent-amber)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '4px',
              padding: '1px 6px',
              fontSize: '10px',
              fontWeight: '700',
              letterSpacing: '0.04em',
              whiteSpace: 'nowrap'
            }}>
              IR ENGINE
            </span>
          </div>
          <div style={{
            color: 'var(--text-secondary)',
            fontSize: '11px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            Case #1995-0842 • Downtown Warehouse Arson (Mumbai)
          </div>
        </div>
      </div>

      {/* Center: Navigation Tabs */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-primary)',
        padding: '3px',
        borderRadius: '8px',
        border: '1px solid var(--border-dim)',
        flexShrink: 0
      }}>
        <button
          onClick={() => setActiveTab('investigation')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'investigation' ? 'var(--bg-tertiary)' : 'transparent',
            color: activeTab === 'investigation' ? 'var(--text-gold)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'investigation' ? '600' : '400',
            fontSize: '12.5px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap'
          }}
        >
          <Activity size={15} />
          Investigation Canvas
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'documents' ? 'var(--bg-tertiary)' : 'transparent',
            color: activeTab === 'documents' ? 'var(--text-gold)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'documents' ? '600' : '400',
            fontSize: '12.5px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap'
          }}
        >
          <FolderArchive size={15} />
          Case Archive ({totalDocs})
        </button>

        <button
          onClick={() => setActiveTab('pipeline')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'pipeline' ? 'var(--bg-tertiary)' : 'transparent',
            color: activeTab === 'pipeline' ? 'var(--text-gold)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'pipeline' ? '600' : '400',
            fontSize: '12.5px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap'
          }}
        >
          <Database size={15} />
          IR Pipeline ({totalNodes} Nodes)
        </button>
      </nav>

      {/* Right: Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <button
          onClick={onReloadDemo}
          disabled={isReloading}
          className="btn btn-primary"
          title="Reload 8 fictional cold case files and re-index"
          style={{ fontSize: '12px', padding: '6px 14px' }}
        >
          <RefreshCw size={13} className={isReloading ? "animate-spin" : ""} />
          {isReloading ? "Indexing Files..." : "Load Demo Case"}
        </button>
      </div>
    </header>
  );
}
