import React, { useEffect, useState } from 'react';
import { FileText, ArrowRight, ShieldAlert, Sparkles, ExternalLink, X, RotateCcw, Clock, CheckCircle, UserCheck, BookOpen, AlertTriangle, Compass, Calendar, ShieldCheck, MapPin, Building } from 'lucide-react';

export default function EvidenceSidebar({
  caseId,
  selectedEdge,
  selectedNode,
  onClearSelection,
  searchEvidence,
  searchMetrics,
  directAnswer,
  query,
  onViewDocument,
  onClose
}) {
  const [edgeEvidence, setEdgeEvidence] = useState([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [activeTab, setActiveTab] = useState('detective'); // 'detective', 'citations', or 'timeline'

  // Fetch edge-specific evidence when selectedEdge changes
  useEffect(() => {
    if (!selectedEdge) {
      setEdgeEvidence([]);
      return;
    }

    const fetchEvidence = async () => {
      setLoadingEvidence(true);
      const url = caseId
        ? `http://localhost:8000/api/cases/${caseId}/evidence/${encodeURIComponent(selectedEdge.source)}/${encodeURIComponent(selectedEdge.target)}`
        : `http://localhost:8000/api/evidence/${encodeURIComponent(selectedEdge.source)}/${encodeURIComponent(selectedEdge.target)}`;

      try {
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setEdgeEvidence(data.evidence || []);
        }
      } catch (err) {
        console.error("Failed to load edge evidence:", err);
      } finally {
        setLoadingEvidence(false);
      }
    };

    fetchEvidence();
  }, [selectedEdge, caseId]);

  // When a direct answer arrives, default to detective briefing
  useEffect(() => {
    if (directAnswer && directAnswer.summary) {
      setActiveTab('detective');
    }
  }, [directAnswer]);

  const formatDocTitle = (filename) => {
    if (!filename) return "CASE RECORD";
    return filename
      .replace(/^\d+_/, '')
      .replace('.txt', '')
      .replace(/_/g, ' ')
      .toUpperCase();
  };

  return (
    <aside style={{
      width: '420px',
      maxWidth: '420px',
      minWidth: '340px',
      height: '100%',
      background: 'var(--bg-secondary)',
      borderLeft: '1px solid var(--border-dim)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      boxSizing: 'border-box',
      flexShrink: 0,
      zIndex: 15
    }}>
      {/* Sidebar Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-dim)',
        background: 'var(--bg-tertiary)',
        boxSizing: 'border-box',
        flexShrink: 0
      }}>
        {/* Top Control Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '8px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            fontWeight: '800',
            color: 'var(--accent-amber)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em'
          }}>
            <span style={{ fontSize: '14px' }}>🕵️</span>
            {selectedEdge ? "Relationship Interrogation" : selectedNode ? "Entity Dossier" : "AI Detective Intelligence"}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {(selectedEdge || selectedNode) && (
              <button
                id="btn-clear-selection"
                type="button"
                onClick={onClearSelection}
                className="btn-ghost"
                title="Deselect edge/node"
                style={{
                  padding: '3px 8px',
                  fontSize: '11px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: 'var(--text-secondary)'
                }}
              >
                <RotateCcw size={11} /> Reset Focus
              </button>
            )}
            {onClose && (
              <button
                id="btn-close-evidence"
                type="button"
                onClick={onClose}
                className="btn-ghost"
                title="Hide panel"
                style={{
                  padding: '3px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  color: 'var(--text-muted)'
                }}
              >
                <X size={15} />
              </button>
            )}
          </div>
        </div>

        {/* Dynamic Header Info */}
        {selectedEdge ? (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13.5px',
              fontWeight: '700',
              color: '#ffffff',
              lineHeight: '1.3'
            }}>
              <span style={{ color: 'var(--accent-blue)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedEdge.source}
              </span>
              <ArrowRight size={13} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
              <span style={{ color: 'var(--accent-amber)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedEdge.target}
              </span>
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '5px',
              fontSize: '11.5px',
              color: 'var(--text-secondary)'
            }}>
              <span>Co-Occurrence Weight: <strong style={{ color: 'var(--text-gold)' }}>{selectedEdge.weight}</strong></span>
              <span>•</span>
              <span>Corroborating Passages: <strong style={{ color: '#fff' }}>{edgeEvidence.length || 1}</strong></span>
            </div>
          </div>
        ) : selectedNode ? (
          <div>
            <h3 style={{ fontSize: '15px', color: '#ffffff', fontWeight: '700', lineHeight: '1.3' }}>
              {selectedNode}
            </h3>
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>
              Inspect connected lines on the canvas to view corroborated quotes.
            </div>
          </div>
        ) : (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '4px'
            }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#ffffff' }}>
                {query ? "Investigative Findings & Deductions" : "Case Evidence Archive"}
              </span>
              {searchMetrics && (
                <span style={{ fontSize: '10.5px', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Clock size={10} /> {searchMetrics.execution_time_ms}ms
                </span>
              )}
            </div>
            {query && (
              <div style={{
                fontSize: '11.5px',
                color: 'var(--text-gold)',
                fontStyle: 'italic',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                marginBottom: '6px'
              }}>
                "{query}"
              </div>
            )}

            {/* Navigation Tabs */}
            {query && directAnswer && (
              <div style={{
                display: 'flex',
                gap: '4px',
                marginTop: '6px',
                background: 'var(--bg-primary)',
                padding: '2px',
                borderRadius: '6px'
              }}>
                <button
                  type="button"
                  onClick={() => setActiveTab('detective')}
                  style={{
                    flex: 1,
                    padding: '5px 6px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '11px',
                    fontWeight: activeTab === 'detective' ? '700' : '400',
                    background: activeTab === 'detective' ? 'var(--bg-tertiary)' : 'transparent',
                    color: activeTab === 'detective' ? 'var(--text-gold)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px'
                  }}
                >
                  <Compass size={12} /> AI Briefing
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('citations')}
                  style={{
                    flex: 1,
                    padding: '5px 6px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '11px',
                    fontWeight: activeTab === 'citations' ? '700' : '400',
                    background: activeTab === 'citations' ? 'var(--bg-tertiary)' : 'transparent',
                    color: activeTab === 'citations' ? 'var(--text-gold)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px'
                  }}
                >
                  <FileText size={12} /> Sources ({searchEvidence ? searchEvidence.length : 0})
                </button>
                {directAnswer.timeline_anchors && directAnswer.timeline_anchors.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setActiveTab('timeline')}
                    style={{
                      flex: 1,
                      padding: '5px 6px',
                      borderRadius: '4px',
                      border: 'none',
                      fontSize: '11px',
                      fontWeight: activeTab === 'timeline' ? '700' : '400',
                      background: activeTab === 'timeline' ? 'var(--bg-tertiary)' : 'transparent',
                      color: activeTab === 'timeline' ? 'var(--text-gold)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px'
                    }}
                  >
                    <Calendar size={12} /> Timeline
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Content Body */}
      <div style={{
        flex: 1,
        minHeight: 0,
        overflowY: 'auto',
        overflowX: 'hidden',
        padding: '14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        boxSizing: 'border-box'
      }}>
        {loadingEvidence ? (
          <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-secondary)' }}>
            <Sparkles size={24} className="animate-spin" color="var(--accent-amber)" style={{ margin: '0 auto 10px' }} />
            <div style={{ fontSize: '12px' }}>Interrogating relationship passages...</div>
          </div>
        ) : selectedEdge ? (
          /* Edge Specific Evidence List */
          edgeEvidence.length > 0 ? (
            edgeEvidence.map((ev, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11.5px',
                    fontWeight: '700',
                    color: 'var(--text-gold)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    <FileText size={14} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {formatDocTitle(ev.document_name)}
                    </span>
                  </div>
                  <span className="badge badge-evidence">
                    Proof #{idx + 1}
                  </span>
                </div>

                <div style={{
                  background: 'rgba(10, 13, 20, 0.85)',
                  borderLeft: '3px solid var(--accent-amber)',
                  padding: '10px 12px',
                  borderRadius: '4px',
                  fontSize: '12.5px',
                  lineHeight: '1.6',
                  color: 'var(--text-primary)',
                  fontStyle: 'italic',
                  wordBreak: 'break-word'
                }}>
                  "{ev.snippet_text}"
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Weight: <strong>{ev.weight}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={() => onViewDocument && onViewDocument(ev.document_name)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--accent-blue)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    Open Case File <ExternalLink size={11} />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '30px 16px', color: 'var(--text-muted)' }}>
              No direct sentence citations found for this specific relationship pair.
            </div>
          )
        ) : query && directAnswer && activeTab === 'detective' ? (
          /* AI DETECTIVE BRIEFING VIEW */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Lead Investigator Assessment Card */}
            <div style={{
              background: 'linear-gradient(135deg, #182235 0%, #111724 100%)',
              border: '1px solid rgba(245, 158, 11, 0.45)',
              borderRadius: '10px',
              padding: '14px 16px',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '8px'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '11px',
                  fontWeight: '800',
                  color: 'var(--text-gold)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  <ShieldCheck size={14} color="var(--accent-amber)" /> AI Detective Assessment
                </div>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  background: 'rgba(52, 211, 153, 0.15)',
                  color: '#34d399',
                  border: '1px solid rgba(52, 211, 153, 0.3)',
                  borderRadius: '4px',
                  padding: '1px 6px'
                }}>
                  {directAnswer.confidence_score || "VERIFIED"}
                </span>
              </div>

              <div style={{
                fontSize: '13px',
                lineHeight: '1.65',
                color: '#f8fafc',
                marginBottom: '10px'
              }}>
                {directAnswer.detective_briefing || directAnswer.summary}
              </div>

              {directAnswer.deductive_reasoning && (
                <div style={{
                  background: 'rgba(10, 13, 20, 0.65)',
                  borderLeft: '3px solid var(--accent-blue)',
                  padding: '8px 10px',
                  borderRadius: '4px',
                  fontSize: '11.5px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.55',
                  marginBottom: '10px'
                }}>
                  <strong style={{ color: 'var(--accent-blue)' }}>Deductive Synthesis:</strong> {directAnswer.deductive_reasoning}
                </div>
              )}

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '8px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                fontSize: '11px',
                color: 'var(--text-secondary)'
              }}>
                <span>Corroborated across <strong>{directAnswer.corroborated_sources} document(s)</strong></span>
                <button
                  type="button"
                  onClick={() => setActiveTab('citations')}
                  style={{
                    background: 'rgba(245, 158, 11, 0.15)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    color: 'var(--accent-amber)',
                    borderRadius: '4px',
                    padding: '3px 8px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}
                >
                  View Citations →
                </button>
              </div>
            </div>

            {/* Key Corroborated Findings */}
            {directAnswer.key_findings && directAnswer.key_findings.length > 0 && (
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-dim)',
                borderRadius: '10px',
                padding: '14px 16px'
              }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  color: 'var(--accent-blue)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <CheckCircle size={13} /> Corroborated Case Facts
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {directAnswer.key_findings.map((finding, idx) => (
                    <div
                      key={idx}
                      style={{
                        fontSize: '12px',
                        lineHeight: '1.55',
                        color: 'var(--text-primary)',
                        paddingLeft: '12px',
                        borderLeft: '2px solid var(--accent-blue)'
                      }}
                    >
                      {finding}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suspects & Persons of Interest Profile */}
            {directAnswer.persons_of_interest && directAnswer.persons_of_interest.length > 0 && (
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-dim)',
                borderRadius: '10px',
                padding: '12px 14px'
              }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}>
                  <UserCheck size={13} color="var(--accent-emerald)" /> Primary Individuals / Suspects
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {directAnswer.persons_of_interest.map((person, idx) => (
                    <span key={idx} className="badge badge-person" style={{ fontSize: '11px', padding: '3px 8px' }}>
                      👤 {person}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Locations & Organizations */}
            {((directAnswer.locations_identified && directAnswer.locations_identified.length > 0) ||
              (directAnswer.organizations_involved && directAnswer.organizations_involved.length > 0)) && (
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-dim)',
                borderRadius: '10px',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {directAnswer.locations_identified && directAnswer.locations_identified.length > 0 && (
                  <div>
                    <div style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={11} color="var(--accent-amber)" /> Locations Linked:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                      {directAnswer.locations_identified.map((loc, idx) => (
                        <span key={idx} className="badge badge-location" style={{ fontSize: '10.5px' }}>
                          📍 {loc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {directAnswer.organizations_involved && directAnswer.organizations_involved.length > 0 && (
                  <div>
                    <div style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Building size={11} color="var(--accent-emerald)" /> Entities & Firms:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                      {directAnswer.organizations_involved.map((org, idx) => (
                        <span key={idx} className="badge badge-organization" style={{ fontSize: '10.5px' }}>
                          🏢 {org}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : activeTab === 'timeline' && directAnswer && directAnswer.timeline_anchors ? (
          /* TIMELINE RECONSTRUCTION VIEW */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Reconstructed chronological anchors extracted from case files:
            </div>
            {directAnswer.timeline_anchors.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="badge badge-date" style={{ fontSize: '10px' }}>
                    📅 {item.time_anchor}
                  </span>
                  <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                    {item.source}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: '1.5', marginTop: '2px' }}>
                  {item.event}
                </div>
              </div>
            ))}
          </div>
        ) : searchEvidence && searchEvidence.length > 0 ? (
          /* CITATIONS / SOURCE PROOFS VIEW */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{
              fontSize: '11px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingBottom: '4px'
            }}>
              <span><strong>{searchEvidence.length}</strong> verbatim evidence passages found</span>
              <span style={{ color: 'var(--text-muted)' }}>Ranked by relevance</span>
            </div>

            {searchEvidence.map((ev, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11.5px',
                    fontWeight: '700',
                    color: 'var(--text-gold)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    <FileText size={14} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {formatDocTitle(ev.document)}
                    </span>
                  </div>
                  <span className="badge" style={{
                    background: ev.type === 'RELATIONSHIP_EVIDENCE' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                    color: ev.type === 'RELATIONSHIP_EVIDENCE' ? '#f59e0b' : '#38bdf8',
                    border: `1px solid ${ev.type === 'RELATIONSHIP_EVIDENCE' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`
                  }}>
                    Citation #{idx + 1}
                  </span>
                </div>

                <div style={{
                  background: 'rgba(10, 13, 20, 0.85)',
                  borderLeft: `3px solid ${ev.type === 'RELATIONSHIP_EVIDENCE' ? 'var(--accent-amber)' : 'var(--accent-blue)'}`,
                  padding: '10px 12px',
                  borderRadius: '4px',
                  fontSize: '12.5px',
                  lineHeight: '1.6',
                  color: 'var(--text-primary)',
                  fontStyle: 'italic',
                  wordBreak: 'break-word'
                }}>
                  "{ev.text}"
                </div>

                {ev.source_entity && (
                  <div style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    Connecting: <strong style={{ color: 'var(--accent-blue)' }}>{ev.source_entity}</strong> ↔ <strong style={{ color: 'var(--accent-amber)' }}>{ev.target_entity}</strong>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                  <button
                    type="button"
                    onClick={() => onViewDocument && onViewDocument(ev.document)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--accent-blue)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    Open Source Document <ExternalLink size={11} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* EMPTY STATE */
          <div style={{
            textAlign: 'center',
            padding: '40px 16px',
            color: 'var(--text-muted)'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '10px' }}>🕵️</div>
            <h4 style={{ color: 'var(--text-secondary)', fontSize: '13.5px', marginBottom: '6px' }}>
              AI Detective Ready for Inquiry
            </h4>
            <p style={{ fontSize: '12px', lineHeight: '1.6', maxWidth: '300px', margin: '0 auto' }}>
              Ask an investigative question above to generate an <strong>AI Detective Briefing</strong> with connected graph nodes, or <strong>click any connected line</strong> on the canvas to interrogate relationship evidence.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
