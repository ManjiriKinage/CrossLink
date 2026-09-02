import React, { useState, useEffect } from 'react';
import { Search, Sparkles, X, RotateCcw, PanelRightClose, PanelRightOpen } from 'lucide-react';

export default function SearchBar({
  caseData,
  graphData,
  documents,
  onSearch,
  onClear,
  isLoading,
  currentQuery,
  hasActiveFilter,
  sidebarVisible,
  onToggleSidebar
}) {
  const [query, setQuery] = useState(currentQuery || "");
  const [quickClues, setQuickClues] = useState([]);

  useEffect(() => {
    setQuery(currentQuery || "");
  }, [currentQuery]);

  // Compute or fetch dynamic quick clues tailored specifically to the active case
  useEffect(() => {
    let active = true;

    const generateOrFetchClues = async () => {
      if (caseData && caseData.id) {
        try {
          const res = await fetch(`http://localhost:8000/api/cases/${caseData.id}/quick-clues`);
          if (res.ok) {
            const data = await res.json();
            if (active && data && data.length > 0) {
              setQuickClues(data);
              return;
            }
          }
        } catch (err) {
          console.error("Failed to fetch quick clues from backend:", err);
        }
      }

      // Dynamic local computation fallback from graphData and documents
      const dynamicList = [];
      if (graphData && graphData.nodes && graphData.nodes.length > 0) {
        const nodes = graphData.nodes;
        const edges = graphData.edges || [];
        const persons = nodes.filter(n => n.type === 'PERSON').map(n => n.label || n.id);
        const locations = nodes.filter(n => n.type === 'LOCATION').map(n => n.label || n.id);
        const orgs = nodes.filter(n => n.type === 'ORGANIZATION').map(n => n.label || n.id);
        const dates = nodes.filter(n => n.type === 'DATE').map(n => n.label || n.id);

        if (edges.length > 0) {
          const topEdge = edges[0];
          if (topEdge.source !== topEdge.target) {
            dynamicList.push(`What connects ${topEdge.source} and ${topEdge.target}?`);
          }
        }
        if (locations.length > 0) {
          const dateStr = dates.length > 0 ? ` in ${dates[0]}` : "";
          dynamicList.push(`Who was connected to ${locations[0]}${dateStr}?`);
        }
        if (persons.length > 0) {
          dynamicList.push(`What was the role of ${persons[0]}?`);
        }
        if (orgs.length > 0) {
          dynamicList.push(`Show connections for ${orgs[0]}`);
        }
        if (edges.length > 1 && dynamicList.length < 5) {
          const e2 = edges[1];
          if (e2.source !== e2.target) {
            dynamicList.push(`What links ${e2.source} to ${e2.target}?`);
          }
        }
      }

      if (dynamicList.length === 0) {
        const caseName = caseData?.name || "this case";
        dynamicList.push(`Who is involved in ${caseName}?`);
        dynamicList.push(`What incident occurred in ${caseName}?`);
        dynamicList.push(`What evidence has been discovered?`);
      }

      if (active) {
        setQuickClues(dynamicList.slice(0, 6));
      }
    };

    generateOrFetchClues();

    return () => {
      active = false;
    };
  }, [caseData?.id, graphData?.total_nodes, graphData?.nodes?.length, documents?.length]);

  const handleSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleSelectPill = (text) => {
    setQuery(text);
    onSearch(text);
  };

  const handleClear = () => {
    setQuery("");
    if (onClear) onClear();
  };

  return (
    <div style={{
      width: '100%',
      maxWidth: '100%',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-dim)',
      padding: '10px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      boxSizing: 'border-box',
      overflow: 'hidden',
      flexShrink: 0
    }}>
      {/* Top Search & Actions Row */}
      <div style={{
        display: 'flex',
        gap: '8px',
        alignItems: 'center',
        width: '100%',
        maxWidth: '100%',
        boxSizing: 'border-box'
      }}>
        {/* Search Input Box */}
        <form
          onSubmit={handleSubmit}
          style={{
            flex: 1,
            minWidth: 0,
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-dim)',
            borderRadius: '8px',
            padding: '2px 12px',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.4)'
          }}
        >
          <Search size={16} color="var(--accent-amber)" style={{ marginRight: '10px', flexShrink: 0 }} />
          <input
            id="input-search-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Ask an investigative question about ${caseData?.name || 'this case'}...`}
            style={{
              flex: 1,
              minWidth: 0,
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none',
              padding: '7px 0',
              fontFamily: 'var(--font-sans)'
            }}
          />
          {query && (
            <button
              id="btn-input-clear-x"
              type="button"
              onClick={handleClear}
              title="Clear search text"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                flexShrink: 0
              }}
            >
              <X size={15} />
            </button>
          )}
        </form>

        {/* Action: Hybrid Search */}
        <button
          id="btn-hybrid-search"
          type="button"
          onClick={handleSubmit}
          disabled={isLoading || !query.trim()}
          className="btn btn-primary"
          style={{ padding: '8px 18px', flexShrink: 0 }}
        >
          <Search size={14} />
          {isLoading ? "Investigating..." : "AI Detective Search"}
        </button>

        {/* Action: Clear Output / Reset View */}
        <button
          id="btn-clear-output"
          type="button"
          onClick={handleClear}
          className="btn btn-clear"
          title="Clear search results and reset graph to full case view"
          style={{ padding: '8px 14px', flexShrink: 0 }}
        >
          <RotateCcw size={13} />
          Full Case View
        </button>

        {/* Action: Toggle Sidebar */}
        <button
          id="btn-toggle-evidence"
          type="button"
          onClick={onToggleSidebar}
          className="btn btn-secondary"
          title={sidebarVisible ? "Hide Evidence Panel" : "Show Evidence Panel"}
          style={{ padding: '8px 12px', flexShrink: 0 }}
        >
          {sidebarVisible ? <PanelRightClose size={15} /> : <PanelRightOpen size={15} />}
          <span style={{ fontSize: '11.5px' }}>{sidebarVisible ? "Hide Dossier" : "Show Dossier"}</span>
        </button>
      </div>

      {/* Quick Clue Pills Row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        width: '100%',
        maxWidth: '100%',
        minWidth: 0,
        overflowX: 'auto',
        paddingBottom: '2px',
        boxSizing: 'border-box'
      }}>
        <span style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '10.5px',
          fontWeight: '700',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          whiteSpace: 'nowrap',
          flexShrink: 0
        }}>
          <Sparkles size={11} color="var(--accent-amber)" />
          Quick Clues:
        </span>
        {quickClues.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectPill(q)}
            style={{
              background: query === q ? 'rgba(245, 158, 11, 0.15)' : 'var(--bg-tertiary)',
              border: `1px solid ${query === q ? 'var(--accent-amber)' : 'var(--border-dim)'}`,
              color: query === q ? 'var(--text-gold)' : 'var(--text-secondary)',
              borderRadius: '9999px',
              padding: '3px 10px',
              fontSize: '11px',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              flexShrink: 0,
              transition: 'all 0.15s ease'
            }}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
