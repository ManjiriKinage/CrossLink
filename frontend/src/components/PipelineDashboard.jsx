import React, { useState } from 'react';
import { Database, CheckCircle2, Cpu, HardDrive, Share2, Layers, UploadCloud, RefreshCw, AlertCircle, Trash2, RotateCcw } from 'lucide-react';

export default function PipelineDashboard({ caseId, stats, documents, onReloadDemo, isReloading, onUploadSuccess, onDocumentDeleted, onResetSystem }) {
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadMessage(null);

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
        setUploadMessage({ type: 'success', text: `Uploaded and indexed ${files.length} document(s)! Knowledge graph & vectors updated.` });
        if (onUploadSuccess) onUploadSuccess();
      } else {
        const errData = await res.json().catch(() => ({}));
        setUploadMessage({ type: 'error', text: errData.detail || 'Failed to process uploaded files.' });
      }
    } catch (err) {
      setUploadMessage({ type: 'error', text: `Upload failed: ${err.message}` });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDeleteSingle = async (docId, filename) => {
    const confirmed = window.confirm(`Remove "${filename}" from this case dossier?`);
    if (!confirmed) return;

    const deleteUrl = caseId
      ? `http://localhost:8000/api/cases/${caseId}/documents/${docId}`
      : `http://localhost:8000/api/documents/${docId}`;

    try {
      const res = await fetch(deleteUrl, {
        method: 'DELETE'
      });
      if (res.ok) {
        if (onDocumentDeleted) onDocumentDeleted(docId);
      }
    } catch (err) {
      console.error("Error deleting:", err);
    }
  };

  const handleResetAll = async () => {
    const confirmed = window.confirm("Are you sure you want to remove ALL documents and reset data for this case?");
    if (!confirmed) return;

    try {
      const res = await fetch('http://localhost:8000/api/demo/reset', { method: 'POST' });
      if (res.ok) {
        if (onResetSystem) onResetSystem();
      }
    } catch (err) {
      console.error("Reset failed:", err);
    }
  };

  const PIPELINE_STEPS = [
    { title: "1. Text Normalization", desc: "Cleans Unicode, smart quotes, carriage returns and whitespace", icon: Layers },
    { title: "2. Sliding Window Chunking", desc: "Segments text into 500-character windows with 100-character overlap", icon: HardDrive },
    { title: "3. Named Entity Recognition (spaCy)", desc: "Extracts PERSON, LOCATION, ORGANIZATION, and DATE entities", icon: Cpu },
    { title: "4. Relationship Discovery", desc: "Discovers co-occurrences with sentence-level bonus weighting & verbatim evidence quotes", icon: Share2 },
    { title: "5. Dense Vector Embeddings", desc: "SentenceTransformers (all-MiniLM-L6-v2) generates 384-dimensional dense vectors", icon: Database },
    { title: "6. ChromaDB Persistent HNSW Index", desc: "Stores cosine-distance semantic index for hybrid vector retrieval", icon: CheckCircle2 }
  ];

  return (
    <div style={{
      width: '100%',
      maxWidth: '100%',
      height: '100%',
      overflowY: 'auto',
      background: 'var(--bg-primary)',
      padding: '24px',
      boxSizing: 'border-box'
    }}>
      <div style={{ maxWidth: '960px', margin: '0 auto', boxSizing: 'border-box' }}>
        {/* Overview Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #131c2e 0%, #0f1624 100%)',
          border: '1px solid var(--border-dim)',
          borderRadius: '12px',
          padding: '20px 24px',
          marginBottom: '20px',
          boxShadow: 'var(--shadow-md)',
          boxSizing: 'border-box'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                color: 'var(--accent-amber)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                marginBottom: '4px'
              }}>
                Under The Hood • Information Retrieval Architecture
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#ffffff', marginBottom: '6px' }}>
                Cold Case Ingestion & Search Pipeline
              </h2>
              <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', maxWidth: '600px', lineHeight: '1.5' }}>
                Every investigative file is ingested through an automated 6-stage NLP and indexing pipeline,
                generating multi-modal representations across relational tables, graph structures, and dense vector spaces.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={onReloadDemo}
                disabled={isReloading}
                className="btn btn-primary"
                style={{ padding: '10px 18px', fontSize: '12.5px' }}
              >
                <RefreshCw size={14} className={isReloading ? "animate-spin" : ""} />
                {isReloading ? "Ingesting Files..." : "Re-Index Demo (8 Files)"}
              </button>

              <button
                type="button"
                onClick={handleResetAll}
                className="btn btn-clear"
                style={{ padding: '10px 14px', fontSize: '12.5px' }}
                title="Wipe all documents and clear system for new case"
              >
                <Trash2 size={14} /> Clear All Files
              </button>
            </div>
          </div>

          {/* Live Metrics Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '12px',
            marginTop: '18px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-dim)'
          }}>
            <div style={{ background: 'var(--bg-primary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Documents</div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text-gold)', marginTop: '2px' }}>
                {stats.totalDocs}
              </div>
            </div>
            <div style={{ background: 'var(--bg-primary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Entity Nodes</div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--accent-blue)', marginTop: '2px' }}>
                {stats.totalNodes}
              </div>
            </div>
            <div style={{ background: 'var(--bg-primary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Relationships</div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                {stats.totalEdges}
              </div>
            </div>
            <div style={{ background: 'var(--bg-primary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Vector Chunks</div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--accent-purple)', marginTop: '2px' }}>
                {stats.totalChunks || stats.totalDocs * 4}
              </div>
            </div>
          </div>
        </div>

        {/* Upload Custom Files Section */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px dashed var(--border-dim)',
          borderRadius: '12px',
          padding: '22px',
          textAlign: 'center',
          marginBottom: '24px',
          boxSizing: 'border-box'
        }}>
          <UploadCloud size={36} color="var(--accent-amber)" style={{ margin: '0 auto 8px' }} />
          <h3 style={{ fontSize: '15px', color: '#ffffff', fontWeight: '700', marginBottom: '4px' }}>
            Ingest New Case Documents (Reuse System)
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Upload plain text (.txt) case notes or witness statements to dynamically build a new knowledge graph and vector index.
          </p>

          <label className="btn btn-secondary" style={{ cursor: 'pointer', display: 'inline-flex' }}>
            <input
              type="file"
              multiple
              accept=".txt"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
            {uploading ? "Ingesting Files..." : "Choose Case Files (.txt)"}
          </label>

          {uploadMessage && (
            <div style={{
              marginTop: '12px',
              fontSize: '12px',
              color: uploadMessage.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}>
              {uploadMessage.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
              {uploadMessage.text}
            </div>
          )}
        </div>

        {/* Currently Indexed Documents Management Table */}
        {documents && documents.length > 0 && (
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-dim)',
            borderRadius: '10px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <h3 style={{
              fontSize: '13px',
              fontWeight: '700',
              color: 'var(--text-gold)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom: '12px'
            }}>
              Manage Active Case Documents ({documents.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.map(doc => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: 'var(--bg-primary)',
                    borderRadius: '6px',
                    border: '1px solid var(--border-dim)',
                    fontSize: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <code style={{ color: '#fff', fontWeight: '600' }}>{doc.filename}</code>
                    <span style={{ color: 'var(--text-muted)' }}>({doc.chunk_count} chunks, {doc.entity_count} entities)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteSingle(doc.id, doc.filename)}
                    className="btn-ghost"
                    style={{ color: '#f87171', padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title="Remove this document"
                  >
                    <Trash2 size={12} /> Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pipeline Stage Cards */}
        <h3 style={{
          fontSize: '13px',
          fontWeight: '700',
          color: 'var(--text-gold)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          marginBottom: '12px'
        }}>
          Ingestion Architecture Stages
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {PIPELINE_STEPS.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxSizing: 'border-box'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '7px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    flexShrink: 0
                  }}>
                    <Icon size={16} color="var(--accent-amber)" />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '13.5px', fontWeight: '700', color: '#ffffff', marginBottom: '1px' }}>
                      {step.title}
                    </h4>
                    <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                      {step.desc}
                    </p>
                  </div>
                </div>

                <span className="badge" style={{
                  background: 'rgba(52, 211, 153, 0.15)',
                  color: '#34d399',
                  border: '1px solid rgba(52, 211, 153, 0.3)'
                }}>
                  ● Ready
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
