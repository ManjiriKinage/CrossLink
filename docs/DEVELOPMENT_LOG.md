# Development Log: `cold_case`

This log documents the chronological progress, architectural milestones, and bug fixes implemented during the development of `cold_case`.

---

## 2026-09-02 — Milestone: Dynamic Case-Scoped Quick Clues & AI Investigation Suite

### Changes & Additions:
1. **Dynamic Case Quick Clues**:
   - Implemented `GET /api/cases/{case_id}/quick-clues` in `backend/app/api/case_routes.py` to dynamically inspect case entities, high-weight relationships, and documents.
   - Updated `frontend/src/components/SearchBar.jsx` and `frontend/src/pages/CaseDetail.jsx` to fetch and compute dynamic clue suggestions for active cases instead of static demo prompts.
2. **AI Detective Agent Synthesis Overhaul**:
   - Upgraded `backend/app/search/synthesizer.py` with the AI Lead Detective persona:
     - Direct investigative assessment answering the specific question intent (Who, What, Where, Why/How).
     - Deductive reasoning breakdown linking co-occurring entities.
     - Corroborated case facts with bracketed citations (`[Source: ...]`).
     - Suspects & Persons of Interest profile.
     - Extracted chronological timeline anchors (`extract_timeline_anchors`).
     - Multi-source confidence score calculation.
3. **Whole-Case vs Question-Connected Subgraph Isolation**:
   - Updated `backend/app/search/engine.py` to prune all disconnected/unrelated orphan nodes when a question is submitted, rendering only the connected subgraph answering the query.
   - When search is cleared, the system displays the complete whole-case knowledge graph.
4. **Direct Dynamic File Uploading**:
   - Enhanced `POST /api/cases/{case_id}/documents` in `case_routes.py` to accept single or multiple files with universal character decoding (UTF-8, Latin-1, CP1252, ISO-8859-1, UTF-16).
   - Added direct drag-and-drop / file picker in `DocumentExplorer.jsx` and updated `PipelineDashboard.jsx` for case-scoped ingestion.
5. **AI Detective Dossier UI**:
   - Upgraded `frontend/src/components/EvidenceSidebar.jsx` with tabbed AI Briefing, Source Proofs (ranked with relevance scores), and Chronological Timeline.

### Verification:
- `python tests/test_pipeline.py` passed with 0 errors (cleaner, chunker, NER, co-occurrence, ingestion, connected subgraph retrieval).
- `npm run build` executed cleanly in 1.12s.

---

## 2026-09-01 — Milestone: Multi-Case Isolation & Pipeline Bug Fixes

### Changes & Additions:
1. **Pipeline Test Fix**:
   - Resolved `TypeError: ingest_document() missing 1 required positional argument: 'case_id'` in `tests/test_pipeline.py` by provisioning test case models.
2. **Frontend Multi-Case Pages**:
   - Created `frontend/src/pages/CaseList.jsx` for case directory management, case creation modal, and aggregate metrics.
   - Created `frontend/src/pages/CaseDetail.jsx` for active case navigation across Investigation Canvas, Case Archive, and IR Pipeline tabs.
3. **Database Cascading & Constraints**:
   - Updated `backend/app/db/models.py` with `CaseModel` foreign keys across `DocumentModel`, `ChunkModel`, `EntityModel`, and `EvidenceModel` with `ondelete="CASCADE"`.

---

## Initial Prototype Development

### Core Subsystems Created:
- Text cleaner (`cleaner.py`) with Unicode normalization and whitespace standardizing.
- Sliding window chunker (`chunker.py`) with 500-char window and 100-char overlap.
- spaCy Named Entity Recognition (`ner.py`) configured for English `en_core_web_sm`.
- Canonicalizer (`canonicalizer.py`) for entity alias merging.
- Co-occurrence matrix generator (`cooccurrence.py`) with sentence-level bonus weighting ($w=2.0$).
- Vector store (`chroma_store.py`) backed by ChromaDB and SentenceTransformers (`all-MiniLM-L6-v2`).
- Embedded in-memory graph store (`networkx_store.py`) and optional Neo4j adapter (`neo4j_store.py`).
- 8 fictional 1995 cold case demo files (`data/demo_docs/`) set in Mumbai.
