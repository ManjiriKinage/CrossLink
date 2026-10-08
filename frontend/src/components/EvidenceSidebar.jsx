import React, { useEffect, useState } from 'react';
import { FileText, ArrowRight, Sparkles, ExternalLink, X, RotateCcw, Clock, CheckCircle2, ShieldCheck, Link2, BookOpen, Brain, Share2, Award } from 'lucide-react';

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

  const formatDocTitle = (filename) => {
    if (!filename) return "CASE RECORD";
    return filename
      .replace(/^\d+_/, '')
      .replace('.txt', '')
      .replace('.md', '')
      .replace(/_/g, ' ')
      .toUpperCase();
  };

  // Extract answer, dot connections, and AI conclusion cleanly
  const answerText = directAnswer?.answer || directAnswer?.detective_briefing || directAnswer?.summary || "";
  const dotConnections = directAnswer?.dot_connections || [];
  const aiConclusion = directAnswer?.ai_conclusion || "";
  const graphAnalysis = directAnswer?.graph_analysis || "";
  const metrics = directAnswer?.evidentiary_metrics || null;
  const citations = (directAnswer?.key_evidence && directAnswer.key_evidence.length > 0)
    ? directAnswer.key_evidence
    : (searchEvidence || []);

  return (
    <aside style={{
      width: '450px',
      maxWidth: '450px',
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
      {/* Sidebar Top Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-dim)',
        background: 'var(--bg-tertiary)',
        boxSizing: 'border-box',
        flexShrink: 0
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: selectedEdge || selectedNode || query ? '6px' : '0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            fontWeight: '800',
            color: 'var(--text-gold)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em'
          }}>
            <span style={{ fontSize: '14px' }}>🕵️</span>
            {selectedEdge ? "Relationship Proof" : selectedNode ? "Entity Dossier" : "Case Findings & AI Intelligence"}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {(selectedEdge || selectedNode) && (
              <button
                id="btn-clear-selection"
                type="button"
                onClick={onClearSelection}
                className="btn-ghost"
                title="Reset selection to search answer"
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
                <RotateCcw size={11} /> Reset
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

        {/* Dynamic header info */}
        {selectedEdge ? (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
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
              fontSize: '11px',
              color: 'var(--text-secondary)',
              marginTop: '4px'
            }}>
              Weight: <strong style={{ color: 'var(--text-gold)' }}>{selectedEdge.weight}</strong> • Passages: <strong>{edgeEvidence.length || 1}</strong>
            </div>
          </div>
        ) : selectedNode ? (
          <div>
            <h3 style={{ fontSize: '14px', color: '#ffffff', fontWeight: '700', lineHeight: '1.3' }}>
              {selectedNode}
            </h3>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Click connected lines on the canvas to view exact relationship quotes.
            </div>
          </div>
        ) : query ? (
          <div>
            <div style={{
              fontSize: '12px',
              color: 'var(--text-gold)',
              fontStyle: 'italic',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              "{query}"
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '10.5px',
              color: 'var(--text-secondary)',
              marginTop: '4px'
            }}>
              <span>Corroborated across <strong>{directAnswer?.corroborated_sources || 1} document(s)</strong></span>
              {searchMetrics && (
                <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Clock size={10} /> {searchMetrics.execution_time_ms}ms
                </span>
              )}
            </div>
          </div>
        ) : null}
      </div>

      {/* Main Content Scroll Area */}
      <div style={{
        flex: 1,
        minHeight: 0,
        overflowY: 'auto',
        overflowX: 'hidden',
        padding: '14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxSizing: 'border-box'
      }}>
        {loadingEvidence ? (
          <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-secondary)' }}>
            <Sparkles size={24} className="animate-spin" color="var(--accent-amber)" style={{ margin: '0 auto 10px' }} />
            <div style={{ fontSize: '12px' }}>Retrieving relationship evidence...</div>
          </div>
        ) : selectedEdge ? (
          /* Edge Relationship Evidence */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              Supporting Excerpts ({edgeEvidence.length})
            </div>

            {edgeEvidence.length > 0 ? (
              edgeEvidence.map((ev, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-dim)',
                    borderRadius: '8px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      fontSize: '11px',
                      fontWeight: '700',
                      color: 'var(--text-gold)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      <FileText size={13} style={{ flexShrink: 0 }} />
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {formatDocTitle(ev.document_name)}
                      </span>
                    </div>
                    <span className="badge badge-evidence" style={{ fontSize: '10px' }}>
                      Weight {ev.weight}
                    </span>
                  </div>

                  <div style={{
                    background: 'rgba(10, 13, 20, 0.85)',
                    borderLeft: '3px solid var(--accent-amber)',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    lineHeight: '1.55',
                    color: 'var(--text-primary)',
                    fontStyle: 'italic',
                    wordBreak: 'break-word'
                  }}>
                    "{ev.snippet_text}"
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
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
                      Open File <ExternalLink size={11} />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 16px', color: 'var(--text-muted)', fontSize: '12px' }}>
                No direct sentence quotes found for this connection.
              </div>
            )}
          </div>
        ) : query && answerText ? (
          /* SEARCH RESULTS: DIRECT ANSWER + CONNECTING THE DOTS + AI CONCLUSION + EVIDENCE */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* 1. Clear Direct Answer Card */}
            <div style={{
              background: 'linear-gradient(135deg, #182235 0%, #111724 100%)',
              border: '1px solid rgba(245, 158, 11, 0.45)',
              borderRadius: '10px',
              padding: '14px 16px',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)'
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
                  <ShieldCheck size={14} color="var(--accent-amber)" /> Direct Answer
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

              <div
                style={{
                  fontSize: '13.5px',
                  lineHeight: '1.65',
                  color: '#f8fafc',
                  fontWeight: '400'
                }}
                dangerouslySetInnerHTML={{
                  __html: answerText
                    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #fbbf24">$1</strong>')
                }}
              />
            </div>

            {/* 2. Connecting the Dots Section */}
            {dotConnections && dotConnections.length > 0 && (
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-dim)',
                borderRadius: '10px',
                padding: '14px 16px'
              }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  color: 'var(--accent-amber)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <Link2 size={13} /> Connecting the Dots
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {dotConnections.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        fontSize: '12px',
                        lineHeight: '1.55',
                        color: 'var(--text-primary)',
                        paddingLeft: '10px',
                        borderLeft: '2px solid var(--accent-amber)'
                      }}
                      dangerouslySetInnerHTML={{
                        __html: item.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #f1f5f9">$1</strong>')
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* 3. NEW SECTION: AI Final Conclusion & Graph Analysis */}
            {(aiConclusion || graphAnalysis) && (
              <div style={{
                background: 'linear-gradient(135deg, rgba(24, 34, 53, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                borderRadius: '10px',
                padding: '14px 16px',
                boxShadow: '0 4px 18px rgba(0, 0, 0, 0.35)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  paddingBottom: '8px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    fontWeight: '800',
                    color: 'var(--accent-blue)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    <Brain size={14} color="var(--accent-blue)" /> AI Final Conclusion & Graph Analysis
                  </div>
                  {metrics && (
                    <span style={{
                      fontSize: '10px',
                      fontWeight: '700',
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      borderRadius: '4px',
                      padding: '1px 6px'
                    }}>
                      {metrics.corroboration_score} Score
                    </span>
                  )}
                </div>

                {/* AI Deductive Verdict */}
                {aiConclusion && (
                  <div style={{
                    fontSize: '12.5px',
                    lineHeight: '1.6',
                    color: '#f1f5f9',
                    borderLeft: '3px solid var(--accent-blue)',
                    paddingLeft: '10px'
                  }}>
                    <strong style={{ color: 'var(--accent-blue)' }}>AI Conclusion: </strong>
                    {aiConclusion}
                  </div>
                )}

                {/* Graph & Multi-Hop Network Analysis */}
                {graphAnalysis && (
                  <div style={{
                    background: 'rgba(10, 13, 20, 0.65)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.55',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '6px'
                  }}>
                    <Share2 size={13} color="var(--accent-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>
                      <strong style={{ color: 'var(--text-gold)' }}>Graph Topology: </strong>
                      {graphAnalysis}
                    </span>
                  </div>
                )}

                {/* Evidentiary Metrics summary */}
                {metrics && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '6px',
                    fontSize: '10.5px',
                    color: 'var(--text-muted)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <span>Central Nexus: <strong style={{ color: '#fff' }}>{metrics.central_nexus}</strong></span>
                    <span>Status: <strong style={{ color: 'var(--accent-emerald)' }}>{metrics.verdict_status}</strong></span>
                  </div>
                )}
              </div>
            )}

            {/* 4. Supporting Evidence Only */}
            {citations && citations.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <BookOpen size={12} color="var(--accent-blue)" /> Supporting Evidence ({citations.length})
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Direct Document Proof</span>
                </div>

                {citations.map((ev, idx) => {
                  const docName = ev.document || ev.document_name || "Case Document";
                  return (
                    <div
                      key={idx}
                      style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-dim)',
                        borderRadius: '8px',
                        padding: '10px 12px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          fontSize: '11px',
                          fontWeight: '700',
                          color: 'var(--text-gold)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          <FileText size={12} style={{ flexShrink: 0 }} />
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {formatDocTitle(docName)}
                          </span>
                        </div>
                        <span className="badge" style={{
                          fontSize: '9.5px',
                          background: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                          border: '1px solid rgba(56, 189, 248, 0.3)'
                        }}>
                          Proof #{idx + 1}
                        </span>
                      </div>

                      <div style={{
                        background: 'rgba(10, 13, 20, 0.85)',
                        borderLeft: '3px solid var(--accent-blue)',
                        padding: '8px 10px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        lineHeight: '1.55',
                        color: 'var(--text-primary)',
                        fontStyle: 'italic',
                        wordBreak: 'break-word'
                      }}>
                        "{ev.text || ev.snippet_text}"
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                        <button
                          type="button"
                          onClick={() => onViewDocument && onViewDocument(docName)}
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
                          Open Document <ExternalLink size={11} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          /* Clean Empty State */
          <div style={{
            textAlign: 'center',
            padding: '48px 16px',
            color: 'var(--text-muted)'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '10px' }}>🕵️</div>
            <h4 style={{ color: 'var(--text-secondary)', fontSize: '13.5px', marginBottom: '6px', fontWeight: '700' }}>
              Ready to Solve Inquiry
            </h4>
            <p style={{ fontSize: '12px', lineHeight: '1.6', maxWidth: '300px', margin: '0 auto' }}>
              Ask any question above to get a <strong>clear direct answer</strong> with <strong>connected evidence dots</strong> and <strong>AI conclusion analysis</strong>.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
