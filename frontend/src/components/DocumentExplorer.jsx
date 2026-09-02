import React, { useState, useEffect } from 'react';
import { FileText, Eye, Tag, Sparkles, Trash2, AlertCircle, CheckCircle2, UploadCloud, Plus } from 'lucide-react';

export default function DocumentExplorer({ caseId, documents, initialDocName, onDocumentDeleted, onUploadSuccess }) {
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [docDetail, setDocDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  // If initialDocName is provided, find its ID and select it
  useEffect(() => {
    if (documents && documents.length > 0) {
      if (initialDocName) {
        const found = documents.find(d => d.filename === initialDocName);
        if (found) {
          setSelectedDocId(found.id);
          return;
        }
      }
      if (!selectedDocId || !documents.some(d => d.id === selectedDocId)) {
        setSelectedDocId(documents[0].id);
      }
    } else {
      setSelectedDocId(null);
      setDocDetail(null);
    }
  }, [documents, initialDocName]);

  // Fetch full details when selectedDocId changes
  useEffect(() => {
    if (!selectedDocId) {
      setDocDetail(null);
      return;
    }

    const fetchDetail = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/documents/${selectedDocId}`);
        if (res.ok) {
          const data = await res.json();
          setDocDetail(data);
        } else {
          setDocDetail(null);
        }
      } catch (err) {
        console.error("Failed to load document details:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [selectedDocId]);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setStatusMessage(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    const uploadUrl = caseId 
      ? `http://localhost:8000/api/cases/${caseId}/documents`
      : 'http://localhost:8000/api/documents/upload';

    try {
      const res = await fetch(uploadUrl, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setStatusMessage({
          type: 'success',
          text: `Successfully ingested and indexed ${files.length} document(s)! Knowledge graph & vectors updated.`
        });
        if (onUploadSuccess) onUploadSuccess();
      } else {
        const errData = await res.json().catch(() => ({}));
        setStatusMessage({
          type: 'error',
          text: errData.detail || 'Failed to upload case documents.'
        });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: `Upload failed: ${err.message}` });
    } finally {
      setIsUploading(false);
      // Reset input value
      e.target.value = '';
    }
  };

  const handleDeleteDocument = async (docId, filename, e) => {
    if (e) e.stopPropagation();

    const confirmed = window.confirm(
      `Are you sure you want to remove "${filename}" from this case dossier?\n\nThis will remove its text chunks from the vector database and re-synchronize the knowledge graph.`
    );
    if (!confirmed) return;

    setIsDeleting(true);
    setStatusMessage(null);

    const deleteUrl = caseId 
      ? `http://localhost:8000/api/cases/${caseId}/documents/${docId}`
      : `http://localhost:8000/api/documents/${docId}`;

    try {
      const res = await fetch(deleteUrl, {
        method: 'DELETE'
      });
      if (res.ok) {
        setStatusMessage({ type: 'success', text: `Removed "${filename}". Graph and vector index re-synchronized.` });
        if (onDocumentDeleted) {
          onDocumentDeleted(docId);
        }
      } else {
        setStatusMessage({ type: 'error', text: `Failed to remove document (status ${res.status}).` });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: `Error deleting document: ${err.message}` });
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDocTitle = (filename) => {
    if (!filename) return "DOCUMENT";
    return filename
      .replace(/^\d+_/, '')
      .replace('.txt', '')
      .replace(/_/g, ' ')
      .toUpperCase();
  };

  return (
    <div style={{
      display: 'flex',
      width: '100%',
      height: '100%',
      background: 'var(--bg-primary)',
      overflow: 'hidden',
      boxSizing: 'border-box'
    }}>
      {/* Left Column: Document File List & Upload Bar */}
      <div style={{
        width: '340px',
        maxWidth: '340px',
        minWidth: '300px',
        borderRight: '1px solid var(--border-dim)',
        background: 'var(--bg-secondary)',
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box',
        flexShrink: 0
      }}>
        {/* Header with Quick Upload Action */}
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-dim)',
          background: 'var(--bg-tertiary)',
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px'
        }}>
          <h2 style={{
            fontSize: '12.5px',
            fontWeight: '700',
            color: 'var(--text-gold)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <FileText size={15} /> Case Archive ({documents ? documents.length : 0})
          </h2>

          <label
            className="btn btn-primary"
            style={{
              fontSize: '11px',
              padding: '4px 10px',
              cursor: isUploading ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
            title="Upload and ingest new plain text case files"
          >
            <input
              type="file"
              multiple
              accept=".txt"
              onChange={handleFileUpload}
              disabled={isUploading}
              style={{ display: 'none' }}
            />
            {isUploading ? <Sparkles size={12} className="animate-spin" /> : <Plus size={12} />}
            {isUploading ? "Indexing..." : "Upload Files"}
          </label>
        </div>

        {/* Status Notification */}
        {statusMessage && (
          <div style={{
            padding: '8px 12px',
            fontSize: '11px',
            background: statusMessage.type === 'success' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid var(--border-dim)',
            color: statusMessage.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            {statusMessage.type === 'success' ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
            <span style={{ flex: 1 }}>{statusMessage.text}</span>
            <button
              onClick={() => setStatusMessage(null)}
              style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer' }}
            >
              ×
            </button>
          </div>
        )}

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px', boxSizing: 'border-box' }}>
          {documents && documents.length > 0 ? (
            documents.map(doc => {
              const isSelected = doc.id === selectedDocId;
              return (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDocId(doc.id)}
                  style={{
                    background: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                    border: `1px solid ${isSelected ? 'var(--accent-amber)' : 'var(--border-dim)'}`,
                    borderRadius: '8px',
                    padding: '10px 12px',
                    marginBottom: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? '0 0 10px rgba(245, 158, 11, 0.2)' : 'none',
                    boxSizing: 'border-box'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '6px',
                    marginBottom: '4px'
                  }}>
                    <div style={{
                      fontSize: '12px',
                      fontWeight: '700',
                      color: isSelected ? 'var(--text-gold)' : 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1
                    }}>
                      {formatDocTitle(doc.filename)}
                    </div>

                    <button
                      type="button"
                      onClick={(e) => handleDeleteDocument(doc.id, doc.filename, e)}
                      title={`Remove "${doc.filename}" from dossier`}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '3px',
                        display: 'flex',
                        alignItems: 'center',
                        borderRadius: '3px',
                        transition: 'color 0.15s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>

                  <div style={{
                    fontSize: '10.5px',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                    marginBottom: '6px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {doc.filename}
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11px',
                    color: 'var(--text-secondary)'
                  }}>
                    <span>Entities: <strong style={{ color: 'var(--accent-blue)' }}>{doc.entity_count}</strong></span>
                    <span className="badge badge-evidence" style={{ fontSize: '10px' }}>
                      {doc.chunk_count} Chunks
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '36px 16px',
              color: 'var(--text-muted)',
              border: '1px dashed var(--border-dim)',
              borderRadius: '8px',
              margin: '8px'
            }}>
              <UploadCloud size={32} color="var(--accent-amber)" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontSize: '12.5px', color: '#fff', fontWeight: '600', marginBottom: '4px' }}>
                No Documents in Dossier
              </div>
              <div style={{ fontSize: '11.5px', marginBottom: '12px' }}>
                Upload plain text (.txt) case notes or witness statements.
              </div>
              <label
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '6px 12px', cursor: 'pointer' }}
              >
                <input
                  type="file"
                  multiple
                  accept=".txt"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
                Choose Files (.txt)
              </label>
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Document Details & Transcript */}
      <div style={{
        flex: 1,
        minWidth: 0,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        background: 'var(--bg-primary)',
        boxSizing: 'border-box'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
            <Sparkles size={26} className="animate-spin" color="var(--accent-amber)" style={{ margin: '0 auto 10px' }} />
            <div>Loading case document...</div>
          </div>
        ) : docDetail ? (
          <div style={{ padding: '20px 28px', maxWidth: '850px', width: '100%', boxSizing: 'border-box' }}>
            {/* Header with Document Actions */}
            <div style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-dim)',
              borderRadius: '10px',
              padding: '16px 20px',
              marginBottom: '16px',
              boxSizing: 'border-box'
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    color: 'var(--text-gold)',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    marginBottom: '4px'
                  }}>
                    <FileText size={14} /> Case Evidence Record
                  </div>
                  <h1 style={{
                    fontSize: '18px',
                    fontWeight: '800',
                    color: '#ffffff',
                    marginBottom: '6px'
                  }}>
                    {formatDocTitle(docDetail.filename)}
                  </h1>
                </div>

                <button
                  type="button"
                  onClick={() => handleDeleteDocument(docDetail.id, docDetail.filename)}
                  disabled={isDeleting}
                  className="btn btn-clear"
                  style={{ padding: '6px 12px', fontSize: '11.5px', flexShrink: 0 }}
                  title="Remove this document from the case dossier"
                >
                  <Trash2 size={13} />
                  {isDeleting ? "Removing..." : "Remove Document"}
                </button>
              </div>

              <div style={{ display: 'flex', gap: '12px', fontSize: '11.5px', color: 'var(--text-secondary)', flexWrap: 'wrap', marginTop: '6px' }}>
                <span>File: <code>{docDetail.filename}</code></span>
                <span>•</span>
                <span>Chunks: <strong>{docDetail.chunk_count}</strong></span>
                <span>•</span>
                <span>Discovered Entities: <strong>{docDetail.entity_count}</strong></span>
              </div>
            </div>

            {/* Extracted Entities Tag Cloud */}
            <div style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-dim)',
              borderRadius: '10px',
              padding: '14px 18px',
              marginBottom: '16px',
              boxSizing: 'border-box'
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
                <Tag size={13} color="var(--accent-blue)" /> Extracted Named Entities
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {docDetail.unique_entities && docDetail.unique_entities.length > 0 ? (
                  docDetail.unique_entities.map((ent, idx) => (
                    <span key={idx} className="badge badge-person" style={{ fontSize: '11px', padding: '3px 8px' }}>
                      {ent}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No entities detected.</span>
                )}
              </div>
            </div>

            {/* Verbatim Document Transcript */}
            <div style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-dim)',
              borderRadius: '10px',
              padding: '16px 20px',
              marginBottom: '20px',
              boxSizing: 'border-box'
            }}>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '10px'
              }}>
                Verbatim Document Transcript
              </div>
              <pre style={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontFamily: 'var(--font-mono)',
                fontSize: '12.5px',
                lineHeight: '1.65',
                color: '#e2e8f0',
                background: 'var(--bg-primary)',
                padding: '14px',
                borderRadius: '7px',
                border: '1px solid var(--border-dim)',
                boxSizing: 'border-box'
              }}>
                {docDetail.raw_text}
              </pre>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            Select a document from the archive list to view its transcript, or upload new files.
          </div>
        )}
      </div>
    </div>
  );
}
