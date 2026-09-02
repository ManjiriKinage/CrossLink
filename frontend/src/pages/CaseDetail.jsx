import React, { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw, Activity, FolderArchive, Database, Layers, ShieldAlert, Sparkles, UploadCloud } from 'lucide-react';
import SearchBar from '../components/SearchBar';
import GraphCanvas from '../components/GraphCanvas';
import EvidenceSidebar from '../components/EvidenceSidebar';
import DocumentExplorer from '../components/DocumentExplorer';
import PipelineDashboard from '../components/PipelineDashboard';

export default function CaseDetail({ caseData, onBack }) {
  const [activeTab, setActiveTab] = useState('investigation');
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 });
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  // Search & Evidence state
  const [currentQuery, setCurrentQuery] = useState('');
  const [searchEvidence, setSearchEvidence] = useState([]);
  const [searchMetrics, setSearchMetrics] = useState(null);
  const [directAnswer, setDirectAnswer] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [sidebarVisible, setSidebarVisible] = useState(true);

  // Document explorer navigation helper
  const [docToView, setDocToView] = useState(null);

  // Load case graph and documents
  const loadCaseData = async () => {
    if (!caseData || !caseData.id) return;
    setLoading(true);
    try {
      const [graphRes, docsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/cases/${caseData.id}/graph`),
        fetch(`http://localhost:8000/api/cases/${caseData.id}/documents`)
      ]);

      if (graphRes.ok) {
        const gData = await graphRes.json();
        setGraphData(gData);
      }
      if (docsRes.ok) {
        const dData = await docsRes.json();
        setDocuments(dData);
      }
    } catch (err) {
      console.error("Error loading case details:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseData();
  }, [caseData.id]);

  // Execute hybrid search scoped to case
  const handleSearch = async (queryText) => {
    if (!queryText || !queryText.trim()) return;
    setIsSearching(true);
    setCurrentQuery(queryText);
    setSelectedEdge(null);
    setSelectedNode(null);

    try {
      const res = await fetch(`http://localhost:8000/api/cases/${caseData.id}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, top_k: 6 })
      });

      if (res.ok) {
        const result = await res.json();
        setGraphData({
          nodes: result.nodes || [],
          edges: result.edges || [],
          total_nodes: result.metrics?.total_nodes || result.nodes?.length || 0,
          total_edges: result.metrics?.total_edges || result.edges?.length || 0
        });
        setSearchEvidence(result.evidence || []);
        setSearchMetrics(result.metrics || null);
        setDirectAnswer(result.direct_answer || null);
        setSidebarVisible(true);
      }
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setIsSearching(false);
    }
  };

  // Reset search / full graph view
  const handleClearSearch = async () => {
    setCurrentQuery('');
    setSearchEvidence([]);
    setSearchMetrics(null);
    setDirectAnswer(null);
    setSelectedEdge(null);
    setSelectedNode(null);
    await loadCaseData();
  };

  const handleSelectEdge = (edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    if (edge) setSidebarVisible(true);
  };

  const handleSelectNode = (nodeId) => {
    setSelectedNode(nodeId);
    setSelectedEdge(null);
    if (nodeId) setSidebarVisible(true);
  };

  const handleViewDocument = (docName) => {
    setDocToView(docName);
    setActiveTab('documents');
  };

  const handleUploadSuccess = async () => {
    await loadCaseData();
  };

  const handleDocumentDeleted = async (docId) => {
    setDocuments(prev => prev.filter(d => d.id !== docId));
    await loadCaseData();
  };

  const stats = {
    totalDocs: documents.length,
    totalNodes: graphData.total_nodes || graphData.nodes?.length || 0,
    totalEdges: graphData.total_edges || graphData.edges?.length || 0,
    totalChunks: documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)
  };

  return (
    <div className="app-container">
      {/* Case Header */}
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
        {/* Left: Back & Case Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: '240px' }}>
          <button
            onClick={onBack}
            className="btn btn-secondary"
            title="Back to all cases"
            style={{ padding: '6px 10px', fontSize: '12px' }}
          >
            <ArrowLeft size={14} /> Cases
          </button>

          <div style={{ overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontFamily: 'var(--font-serif)',
                fontSize: '16px',
                fontWeight: '800',
                letterSpacing: '0.06em',
                color: 'var(--text-gold)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: '280px'
              }}>
                {caseData.name}
              </span>
              <span style={{
                background: 'rgba(245, 158, 11, 0.15)',
                color: 'var(--accent-amber)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '4px',
                padding: '1px 6px',
                fontSize: '10px',
                fontWeight: '700',
                whiteSpace: 'nowrap'
              }}>
                CASE #{caseData.id.toString().padStart(4, '0')}
              </span>
            </div>
            <div style={{
              color: 'var(--text-secondary)',
              fontSize: '11px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '320px'
            }}>
              {caseData.description || "Active Investigation Dossier"}
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
            Case Archive ({documents.length})
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
            IR Pipeline ({stats.totalNodes} Nodes)
          </button>
        </nav>

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <button
            onClick={loadCaseData}
            disabled={loading}
            className="btn btn-secondary"
            title="Refresh case graph & documents"
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </header>

      {/* Main Tab Content */}
      <div className="main-content">
        {activeTab === 'investigation' && (
          <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', overflow: 'hidden' }}>
            <SearchBar
              caseData={caseData}
              graphData={graphData}
              documents={documents}
              onSearch={handleSearch}
              onClear={handleClearSearch}
              isLoading={isSearching}
              currentQuery={currentQuery}
              hasActiveFilter={!!currentQuery || !!selectedEdge || !!selectedNode}
              sidebarVisible={sidebarVisible}
              onToggleSidebar={() => setSidebarVisible(prev => !prev)}
            />

            <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative', overflow: 'hidden' }}>
              <div style={{ flex: 1, minWidth: 0, height: '100%', position: 'relative' }}>
                <GraphCanvas
                  graphData={graphData}
                  onSelectEdge={handleSelectEdge}
                  onSelectNode={handleSelectNode}
                  selectedEdge={selectedEdge}
                  selectedNode={selectedNode}
                />
              </div>

              {sidebarVisible && (
                <EvidenceSidebar
                  caseId={caseData.id}
                  selectedEdge={selectedEdge}
                  selectedNode={selectedNode}
                  onClearSelection={() => {
                    setSelectedEdge(null);
                    setSelectedNode(null);
                  }}
                  searchEvidence={searchEvidence}
                  searchMetrics={searchMetrics}
                  directAnswer={directAnswer}
                  query={currentQuery}
                  onViewDocument={handleViewDocument}
                  onClose={() => setSidebarVisible(false)}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'documents' && (
          <DocumentExplorer
            caseId={caseData.id}
            documents={documents}
            initialDocName={docToView}
            onDocumentDeleted={handleDocumentDeleted}
            onUploadSuccess={handleUploadSuccess}
          />
        )}

        {activeTab === 'pipeline' && (
          <PipelineDashboard
            caseId={caseData.id}
            stats={stats}
            documents={documents}
            onReloadDemo={loadCaseData}
            isReloading={loading}
            onUploadSuccess={handleUploadSuccess}
            onDocumentDeleted={handleDocumentDeleted}
            onResetSystem={loadCaseData}
          />
        )}
      </div>
    </div>
  );
}
