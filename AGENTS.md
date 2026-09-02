# AGENTS.md — AI Coding Agent Handbook for `cold_case`

This document is the primary entry point and persistent memory for any AI coding agent working on `cold_case`. It specifies the project architecture, operational constraints, and the mandatory workflow that must be followed before making any code modifications.

---

## 1. Project Overview & Purpose

`cold_case` is a privacy-first, multi-modal **Information Retrieval (IR) and Knowledge Graph Engine** tailored for investigative dossiers, intelligence records, compliance audits, and cold case inquiries.

Unlike generic conversational LLM chatbots, `cold_case` is **evidence-grounded and deterministic**:
1. It ingests unstructured case documents (police reports, witness testimonies, forensics, shipping manifests, corporate filings).
2. It executes an automated 6-stage NLP extraction pipeline (cleaning $\to$ sliding window chunking $\to$ spaCy Named Entity Recognition $\to$ entity canonicalization $\to$ sentence-level co-occurrence weighting $\to$ dense vector embedding).
3. It stores representations across three synchronized persistence layers (SQL relational database, ChromaDB vector store, NetworkX/Neo4j graph store) with strict **case-level data isolation**.
4. It provides hybrid retrieval (dense semantic search + entity-linked graph traversal) and generates a structured **AI Lead Detective Briefing** with direct verbatim quotes and multi-hop relationship proofs.

---

## 2. Mandatory Workflow for Future AI Agents

Before making ANY changes to the codebase, follow these steps strictly:

```
┌────────────────────────────────────────────────────────┐
│               MANDATORY AGENT WORKFLOW                  │
├────────────────────────────────────────────────────────┤
│ 1. Read AGENTS.md                                      │
│ 2. Read docs/PROJECT_CONTEXT.md                        │
│ 3. Read docs/ARCHITECTURE.md                           │
│ 4. Read docs/QUICKSTART.md                             │
│ 5. Read docs/TODO.md                                   │
│ 6. Read docs/DECISIONS.md                              │
│ 7. Check git status / working directory                │
│ 8. Inspect the relevant source code                    │
│ 9. Understand the current implementation               │
│ 10. Plan the change (Implementation Plan if non-trivial)│
│ 11. Make the smallest appropriate change               │
│ 12. Run relevant tests (tests/test_pipeline.py)        │
│ 13. Verify the application build (npm run build)       │
│ 14. Update documentation if implementation changed     │
│ 15. Report exactly what was changed and verified       │
└────────────────────────────────────────────────────────┘
```

### Critical Rules for AI Agents:
- **The source code is the ground truth**: Do not assume documentation or chat summaries override what is in the code.
- **Never rewrite working components unnecessarily**: Prefer targeted refactoring and surgical edits.
- **Never claim something works without running verification**: Execute test scripts (`tests/test_pipeline.py`) or build tools (`npm run build`).
- **Never fabricate evidence or investigative facts**: The system relies on verifiable document citations.
- **Never invent API behavior**: Inspect `backend/app/api/` and `backend/app/db/models.py`.
- **Maintain case isolation**: Every document, chunk, entity, evidence record, and vector chunk must be isolated by `case_id`.
- **Preserve evidence traceability**: Every relationship edge must link back to exact document names and text snippets.
- **Project Name**: Always use `cold_case`. Do NOT use "TraceNet" or unconfirmed trade names.

---

## 3. High-Level Architecture

```
                                  REACT + VITE FRONTEND (PORT 5173)
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         ▼                                           ▼
                   CaseList Page                              CaseDetail Page
              (Case CRUD & Directory)                 (Active Investigation Canvas)
                                                                     │
                                                      ┌──────────────┼──────────────┐
                                                      ▼              ▼              ▼
                                                 SearchBar      GraphCanvas   EvidenceSidebar
                                                 (Quick Clues)   (Vis.js)     (AI Dossier)
                                                                     │
                                                                     ▼ REST API (Port 8000)
                                                    FASTAPI BACKEND (`backend/app/main.py`)
                                                                     │
                         ┌───────────────────────────────────────────┴───────────────────────────────────────────┐
                         ▼                                                                                       ▼
             [INGESTION PIPELINE]                                                                    [HYBRID SEARCH ENGINE]
             1. Text Normalization (`cleaner.py`)                                                    1. Query NER & Intent Extraction
             2. Sliding Window Chunking (`chunker.py`)                                               2. ChromaDB Semantic Vector Search
             3. spaCy NER (`ner.py`)                                                                 3. Connected Subgraph Traversal
             4. Canonicalization (`canonicalizer.py`)                                                4. Orphan Node Pruning
             5. Co-occurrence Discovery (`cooccurrence.py`)                                          5. AI Detective Synthesizer
                         │                                                                                       │
                         └───────────────────────────────────────────┬───────────────────────────────────────────┘
                                                                     ▼
                                                          MULTI-MODAL STORAGE
                         ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
                         ▼                                           ▼                                           ▼
                 SQLAlchemy / SQLite                               Graph Store                                ChromaDB
                   (`cold_case.db`)                          (NetworkX / Neo4j)                           (`data/chroma`)
               Cases, Docs, Chunks, Evidences              Entity Nodes & Weighted Edges              384-d Dense Embeddings
```

---

## 4. Repository Structure

```
cold_case/
│
├── AGENTS.md                         # AI agent guidelines & workflow (this file)
├── README.md                         # Human-facing project overview & quickstart
├── .env.example                      # Template for backend environment variables
├── cold_case.db                      # Default SQLite database file
│
├── docs/                             # Persistent technical documentation
│   ├── PROJECT_CONTEXT.md            # Problem domain, user personas, current phase
│   ├── ARCHITECTURE.md               # In-depth architectural & data-flow specification
│   ├── QUICKSTART.md                 # Setup, run, and testing instructions
│   ├── DEVELOPMENT_LOG.md            # Chronological record of major milestones & fixes
│   ├── TODO.md                       # Active roadmap and pending tasks
│   └── DECISIONS.md                  # Architecture Decision Records (ADRs)
│
├── data/
│   ├── demo_docs/                    # 8 fictional 1995 cold case investigation documents (.txt)
│   └── chroma/                       # ChromaDB persistent vector index
│
├── backend/
│   ├── .venv/                        # Python virtual environment
│   ├── preload_data.py               # CLI utility to index demo case documents
│   ├── requirements.txt              # Backend Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI app entry point & CORS configuration
│       ├── config.py                 # Pydantic Settings & environment config
│       ├── api/
│       │   ├── __init__.py
│       │   ├── case_routes.py        # Case-scoped CRUD, document upload, search, graph & clues
│       │   └── routes.py             # Legacy / backward-compatible endpoints
│       ├── db/
│       │   ├── database.py           # SQLite / PostgreSQL engine & session setup
│       │   └── models.py             # SQLAlchemy models: Case, Document, Chunk, Entity, Evidence
│       ├── graph/
│       │   ├── base.py               # GraphStoreBase abstract interface
│       │   ├── networkx_store.py     # Default in-memory NetworkX graph engine
│       │   ├── neo4j_store.py        # Optional Neo4j Cypher-backed graph engine
│       │   └── __init__.py           # Graph store singleton factory
│       ├── vector/
│       │   ├── chroma_store.py       # ChromaDB + SentenceTransformers vector store
│       │   └── __init__.py           # Vector store singleton factory
│       ├── pipeline/
│       │   ├── cleaner.py            # Text cleaning & Unicode normalization
│       │   ├── chunker.py            # Sliding window text chunking (500 char, 100 overlap)
│       │   ├── ner.py                # spaCy Named Entity Recognition (en_core_web_sm)
│       │   ├── canonicalizer.py      # Entity alias resolution & canonicalization
│       │   ├── cooccurrence.py       # Sentence ($w=2.0$) & chunk ($w=1.0$) relationship extraction
│       │   └── ingest.py             # Master ingest_document() pipeline function
│       └── search/
│           ├── engine.py             # HybridSearchEngine (Vector + Connected Subgraph)
│           └── synthesizer.py        # AI Lead Detective briefing & deductive reasoning generator
│
├── frontend/
│   ├── package.json                  # React 19, Vite, Vis-network, Lucide-react
│   ├── vite.config.js                # Vite build configuration
│   ├── index.html                    # HTML root template
│   └── src/
│       ├── main.jsx                  # React DOM entry point
│       ├── App.jsx                   # Root application state & page switcher
│       ├── App.css                   # Global styles & resets
│       ├── index.css                 # Noir dark-mode design system & tokens
│       ├── pages/
│       │   ├── CaseList.jsx          # Case directory & management dashboard
│       │   └── CaseDetail.jsx        # Investigation canvas & tabbed case suite
│       └── components/
│           ├── Header.jsx            # Case branding & navigation tabs
│           ├── SearchBar.jsx         # Case-aware query bar with dynamic Quick Clues
│           ├── GraphCanvas.jsx       # Vis.js force-directed interactive graph canvas
│           ├── EvidenceSidebar.jsx   # AI Detective Dossier, citations & timeline
│           ├── DocumentExplorer.jsx  # Case archive, transcript viewer & direct upload
│           └── PipelineDashboard.jsx # 6-stage IR pipeline metrics & case ingestion
│
└── tests/
    └── test_pipeline.py              # Automated pipeline & search test suite
```

---

## 5. Key Technologies

| Domain | Technology | Purpose |
|---|---|---|
| **Backend API** | FastAPI / Uvicorn | High-performance asynchronous REST API |
| **Relational DB** | SQLAlchemy 2.0 / SQLite | Relational metadata, documents, chunks, entities, evidence |
| **Vector Search** | ChromaDB / SentenceTransformers (`all-MiniLM-L6-v2`) | 384-dimensional dense semantic passage embeddings |
| **Knowledge Graph** | NetworkX (default) / Neo4j (optional) | Graph nodes, relationship edges, co-occurrence weights |
| **NLP & Extraction** | spaCy (`en_core_web_sm`) | Named Entity Recognition for `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE` |
| **Frontend SPA** | React 19 / Vite 8.2 | Interactive single-page application |
| **Graph Visuals** | Vis-network (vis-data) | Force-directed physics canvas with zoom, node drag, and edge select |
| **UI Aesthetics** | Vanilla CSS (CSS Variables) | Detective Noir theme with gold, amber, and slate glassmorphism |

---

## 6. How to Run and Test

### Start Backend:
```bash
# From workspace root
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend:
```bash
cd frontend
npm run dev
```

### Run Pipeline Tests:
```bash
.\backend\.venv\Scripts\python.exe tests/test_pipeline.py
```

### Build Frontend:
```bash
cd frontend
npm run build
```

---

## 7. Development & Git Conventions

- **Code Style**: Python PEP 8 with explicit typing. React 19 functional components with hooks.
- **Paths**: Always use forward slashes in markdown documentation and relative or absolute path conventions consistent with Windows/POSIX.
- **Commit Messages**: Conventional commits (e.g., `feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- **Documentation**: If an API route, pipeline parameter, database schema, or UI component changes, update `docs/ARCHITECTURE.md`, `docs/PROJECT_CONTEXT.md`, and `docs/DEVELOPMENT_LOG.md` immediately.
