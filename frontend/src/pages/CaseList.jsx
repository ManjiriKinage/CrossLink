import React, { useState, useEffect } from 'react';
import { FolderArchive, Plus, Search, Trash2, ArrowRight, ShieldAlert, Sparkles, Database, FileText, Share2, Layers, RefreshCw } from 'lucide-react';

export default function CaseList({ onSelectCase, onCreateCase }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState('');
  const [newCaseDesc, setNewCaseDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/cases');
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      } else {
        setErrorMsg('Failed to load cases from server.');
      }
    } catch (err) {
      console.error('Error loading cases:', err);
      setErrorMsg(`Server connection error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleCreateCase = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newCaseName.trim()) return;

    setCreating(true);
    setErrorMsg(null);
    try {
      const res = await fetch('http://localhost:8000/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newCaseName.trim(),
          description: newCaseDesc.trim() || undefined
        })
      });

      if (res.ok) {
        const newCase = await res.json();
        setShowCreateModal(false);
        setNewCaseName('');
        setNewCaseDesc('');
        if (onCreateCase) {
          onCreateCase(newCase);
        } else {
          fetchCases();
        }
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Failed to create case.');
      }
    } catch (err) {
      setErrorMsg(`Error creating case: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteCase = async (caseId, caseName, e) => {
    if (e) e.stopPropagation();
    const confirmed = window.confirm(
      `Are you sure you want to permanently delete investigation case "${caseName}"?\n\nAll documents, entities, and graph relations will be removed.`
    );
    if (!confirmed) return;

    try {
      const res = await fetch(`http://localhost:8000/api/cases/${caseId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setCases(prev => prev.filter(c => c.id !== caseId));
      } else {
        alert('Failed to delete case.');
      }
    } catch (err) {
      console.error('Error deleting case:', err);
      alert(`Error deleting case: ${err.message}`);
    }
  };

  const handleLoadDemo = async () => {
    setLoadingDemo(true);
    setErrorMsg(null);
    try {
      const res = await fetch('http://localhost:8000/api/demo/load', {
        method: 'POST'
      });
      if (res.ok) {
        await fetchCases();
      }
    } catch (err) {
      console.error('Error loading demo case:', err);
    } finally {
      setLoadingDemo(false);
    }
  };

  const filteredCases = cases.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.description && c.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const totalDocs = cases.reduce((sum, c) => sum + (c.document_count || 0), 0);
  const totalEntities = cases.reduce((sum, c) => sum + (c.entity_count || 0), 0);
  const totalRels = cases.reduce((sum, c) => sum + (c.relationship_count || 0), 0);

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-primary)',
      overflowY: 'auto',
      boxSizing: 'border-box'
    }}>
      {/* Top Banner */}
      <header style={{
        background: 'linear-gradient(180deg, #111827 0%, #0c101b 100%)',
        borderBottom: '1px solid var(--border-dim)',
        padding: '16px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(245, 158, 11, 0.4)',
            fontSize: '22px'
          }}>
            🕵️
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                fontFamily: 'var(--font-serif)',
                fontSize: '20px',
                fontWeight: '900',
                letterSpacing: '0.12em',
                color: 'var(--text-gold)',
                textTransform: 'uppercase'
              }}>
                Cold Case
              </span>
              <span style={{
                background: 'rgba(245, 158, 11, 0.15)',
                color: 'var(--accent-amber)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '4px',
                padding: '2px 8px',
                fontSize: '11px',
                fontWeight: '700'
              }}>
                IR & KNOWLEDGE GRAPH ENGINE
              </span>
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
              Multi-Case Investigative Information Retrieval & Relationship Discovery System
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleLoadDemo}
            disabled={loadingDemo}
            className="btn btn-secondary"
            style={{ padding: '8px 16px', fontSize: '12.5px' }}
          >
            <RefreshCw size={14} className={loadingDemo ? "animate-spin" : ""} />
            {loadingDemo ? "Loading Demo..." : "Quick Load Demo"}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '12.5px' }}
          >
            <Plus size={15} />
            New Investigation Case
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div style={{ maxWidth: '1100px', width: '100%', margin: '0 auto', padding: '28px 20px', boxSizing: 'border-box' }}>
        {/* Aggregate Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
          marginBottom: '28px'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-dim)',
            borderRadius: '10px',
            padding: '16px 20px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
              Active Cases
            </div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: 'var(--text-gold)', marginTop: '4px' }}>
              {cases.length}
            </div>
          </div>

          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-dim)',
            borderRadius: '10px',
            padding: '16px 20px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
              Indexed Documents
            </div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: 'var(--accent-blue)', marginTop: '4px' }}>
              {totalDocs}
            </div>
          </div>

          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-dim)',
            borderRadius: '10px',
            padding: '16px 20px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
              Discovered Entities
            </div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: 'var(--accent-emerald)', marginTop: '4px' }}>
              {totalEntities}
            </div>
          </div>

          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-dim)',
            borderRadius: '10px',
            padding: '16px 20px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
              Verified Relationships
            </div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: 'var(--accent-purple)', marginTop: '4px' }}>
              {totalRels}
            </div>
          </div>
        </div>

        {/* Search & Actions Bar */}
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px'
        }}>
          <div style={{
            flex: 1,
            maxWidth: '480px',
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-dim)',
            borderRadius: '8px',
            padding: '4px 14px'
          }}>
            <Search size={16} color="var(--accent-amber)" style={{ marginRight: '10px' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter investigation cases by name or description..."
              style={{
                background: 'transparent',
                border: 'none',
                color: '#fff',
                fontSize: '13px',
                outline: 'none',
                width: '100%',
                padding: '6px 0'
              }}
            />
          </div>

          <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
            Showing <strong>{filteredCases.length}</strong> of <strong>{cases.length}</strong> cases
          </div>
        </div>

        {/* Error message */}
        {errorMsg && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--accent-rose)',
            fontSize: '12.5px',
            marginBottom: '18px'
          }}>
            {errorMsg}
          </div>
        )}

        {/* Case Cards Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-secondary)' }}>
            <Sparkles size={32} className="animate-spin" color="var(--accent-amber)" style={{ margin: '0 auto 12px' }} />
            <div>Loading investigation dossiers...</div>
          </div>
        ) : filteredCases.length > 0 ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '18px'
          }}>
            {filteredCases.map(c => (
              <div
                key={c.id}
                onClick={() => onSelectCase(c)}
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '12px',
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '14px',
                  boxShadow: 'var(--shadow-sm)',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-amber)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.6)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-dim)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span className="badge badge-location" style={{ fontSize: '10px' }}>
                      CASE #{c.id.toString().padStart(4, '0')}
                    </span>
                    <button
                      onClick={(e) => handleDeleteCase(c.id, c.name, e)}
                      title="Delete case"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                        borderRadius: '4px'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#ffffff', marginBottom: '6px' }}>
                    {c.name}
                  </h3>

                  <p style={{
                    fontSize: '12.5px',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.5',
                    minHeight: '38px',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {c.description || "No description provided for this case file."}
                  </p>
                </div>

                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 0',
                    borderTop: '1px solid var(--border-dim)',
                    borderBottom: '1px solid var(--border-dim)',
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)'
                  }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <FileText size={12} color="var(--accent-blue)" />
                      <strong>{c.document_count || 0}</strong> docs
                    </span>
                    <span>•</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Layers size={12} color="var(--accent-emerald)" />
                      <strong>{c.entity_count || 0}</strong> entities
                    </span>
                    <span>•</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Share2 size={12} color="var(--accent-purple)" />
                      <strong>{c.relationship_count || 0}</strong> rels
                    </span>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: '12px'
                  }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                    <span style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '12px',
                      fontWeight: '700',
                      color: 'var(--accent-amber)'
                    }}>
                      Investigate Case <ArrowRight size={13} />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px dashed var(--border-dim)',
            borderRadius: '12px',
            padding: '48px 24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '36px', marginBottom: '12px' }}>📂</div>
            <h3 style={{ fontSize: '16px', color: '#fff', fontWeight: '700', marginBottom: '6px' }}>
              No Investigation Cases Found
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto 20px', lineHeight: '1.5' }}>
              Create a new investigation dossier to start uploading case documents, or load the default demo case.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                onClick={handleLoadDemo}
                disabled={loadingDemo}
                className="btn btn-secondary"
                style={{ padding: '8px 16px' }}
              >
                <RefreshCw size={14} className={loadingDemo ? "animate-spin" : ""} />
                Load Sample Demo Case
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary"
                style={{ padding: '8px 18px' }}
              >
                <Plus size={15} />
                Create New Case
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(5, 8, 14, 0.85)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px',
          boxSizing: 'border-box'
        }}>
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-dim)',
            borderRadius: '14px',
            padding: '24px 28px',
            maxWidth: '520px',
            width: '100%',
            boxShadow: 'var(--shadow-md)',
            boxSizing: 'border-box'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                fontWeight: '700',
                color: 'var(--text-gold)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                <ShieldAlert size={16} /> Open New Cold Case Dossier
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-ghost"
                style={{ padding: '4px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCase} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Case Title *
                </label>
                <input
                  type="text"
                  required
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  placeholder="e.g. Bandra Docks Cargo Disappearance (1998)"
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-dim)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: '13px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Case Synopsis / Background
                </label>
                <textarea
                  rows={4}
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  placeholder="Brief synopsis of the investigation, key allegations, known locations, and primary objectives..."
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-dim)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: '13px',
                    outline: 'none',
                    boxSizing: 'border-box',
                    resize: 'vertical',
                    fontFamily: 'var(--font-sans)'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                  style={{ padding: '8px 16px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newCaseName.trim()}
                  className="btn btn-primary"
                  style={{ padding: '8px 20px' }}
                >
                  {creating ? "Opening Dossier..." : "Create Case Dossier"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
