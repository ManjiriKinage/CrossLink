# Roadmap & TODO List: `cold_case`

This document tracks active tasks, planned features, architectural improvements, and pending enhancements for `cold_case`.

---

## 1. High Priority (Upcoming Sprint)

- [ ] **Direct PDF/DOCX Ingestion**:
  - Implement PDF text extraction using `pypdfium2` (already present in `requirements.txt`) in `backend/app/pipeline/ingest.py`.
  - Add support for `.docx` and `.pdf` file types in the `DocumentExplorer.jsx` and `PipelineDashboard.jsx` file pickers.
- [ ] **Multi-Hop Path Finder**:
  - Add an investigative path-finding tool in the UI allowing users to select two entities (e.g. `Suspect A` and `Company B`) and calculate shortest/all connecting paths in the knowledge graph.
  - Implement `get_paths(case_id, source_id, target_id, max_hops=4)` in `NetworkXGraphStore` and `engine.py`.
- [ ] **Dossier Export (PDF/Markdown)**:
  - Add an **"Export Briefing"** button in `EvidenceSidebar.jsx` that compiles the AI Detective Assessment, Key Corroborated Facts, Timeline, and Verbatim Citations into a downloadable Markdown / PDF summary report.

---

## 2. Medium Priority (Architecture & Performance)

- [ ] **Asynchronous Background Ingestion with Progress Bar**:
  - For large document sets (20+ files), offload ingestion to background worker tasks using FastAPI `BackgroundTasks` or Celery.
  - Add WebSocket or polling endpoint for real-time ingestion progress percentage in `PipelineDashboard.jsx`.
- [ ] **Enhanced Canonicalization & Cross-Document Coreference**:
  - Integrate fuzzy string matching (Levenshtein distance) or lightweight LLM coreference resolution to group nickname aliases (e.g., *"Bobby"* $\leftrightarrow$ *"Robert"*).
- [ ] **Neo4j Enterprise Connector Integration**:
  - Provide a toggle in `PipelineDashboard` to switch between embedded in-memory `NetworkX` and external `Neo4j` with connection status indicator.

---

## 3. Low Priority / Future Enhancements

- [ ] **Investigator Timeline Visualizer**:
  - Dedicated interactive timeline UI component displaying chronological events plotted along an interactive slider.
- [ ] **User Roles & Investigation Access Scoping**:
  - Authentication (JWT / OAuth2) restricting cases to specific investigator teams or clearance tiers.
- [ ] **Geospatial Location Map**:
  - Extract GPS coordinates or address geocodes for `LOCATION` nodes and render on an embedded Leaflet map.

---

## 4. Completed Tasks

- [x] Multi-case database schema with cascade deletion (`CaseModel`, `DocumentModel`, `ChunkModel`, `EntityModel`, `EvidenceModel`).
- [x] Case-isolated hybrid search (vector retrieval in ChromaDB filtered by `case_id`).
- [x] Connected subgraph isolation (pruning disconnected/unrelated orphan nodes upon search inquiry).
- [x] AI Lead Detective Agent Synthesizer with deductive reasoning, key facts, and timeline anchors.
- [x] Universal text file upload handling (UTF-8, Latin-1, CP1252, ISO-8859-1, UTF-16).
- [x] Direct file drag-and-drop ingestion in `DocumentExplorer.jsx`.
- [x] Dynamic case-scoped Quick Clues generation (`GET /api/cases/{case_id}/quick-clues`).
- [x] Automated test pipeline verification (`tests/test_pipeline.py`).
