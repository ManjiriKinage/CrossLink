# 🕵️ cold_case — Information Retrieval & Knowledge Graph Engine

> **A privacy-first Information Retrieval system that analyzes unstructured investigative documents, extracts entities, discovers cross-document relationships, and provides interactive search with verifiable evidence tracing.**

---

## 🎯 What is `cold_case`?

`cold_case` is **not a generic chatbot**. It is an **evidence-based Information Retrieval (IR) and knowledge discovery engine**.

In investigative scenarios (cold cases, compliance audits, intelligence reviews), investigators typically face multiple disparate text files:
- Police incident logs
- Witness interviews
- Corporate registries
- Forensic reports
- Shipping manifests

Manually synthesizing who is connected to whom, at which location, on what date, and finding the exact documentary proof is arduous and error-prone. **`cold_case` automates this entire pipeline** while keeping every relationship linked to verbatim source citations.

---

## 📚 Complete Project Documentation

| Document | Description |
|---|---|
| 🤖 [**`AGENTS.md`**](AGENTS.md) | **Mandatory AI Coding Agent Handbook** & developer workflow instructions |
| 📖 [**`docs/PROJECT_CONTEXT.md`**](docs/PROJECT_CONTEXT.md) | Problem space, target personas, feature implementation status, and tech stack |
| 🏗️ [**`docs/ARCHITECTURE.md`**](docs/ARCHITECTURE.md) | Comprehensive system architecture, data models, pipelines, and API specifications |
| ⚡ [**`docs/QUICKSTART.md`**](docs/QUICKSTART.md) | Step-by-step setup, configuration, running, and verification guide |
| 📜 [**`docs/DEVELOPMENT_LOG.md`**](docs/DEVELOPMENT_LOG.md) | Chronological development milestones, changelogs, and bug fixes |
| 📋 [**`docs/TODO.md`**](docs/TODO.md) | Active roadmap, upcoming sprints, and task backlog |
| 💡 [**`docs/DECISIONS.md`**](docs/DECISIONS.md) | Architecture Decision Records (ADRs) and design rationale |

---

## 🏗️ System Architecture

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
                                                                     ▼ REST API (PORT 8000)
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

## 🧠 Key Information Retrieval Concepts

1. **Hybrid Retrieval**:
   - **Dense Semantic Retrieval**: Uses `SentenceTransformers` (`all-MiniLM-L6-v2`) and `ChromaDB` to retrieve passages based on conceptual meaning even if exact words differ.
   - **Graph Traversal Retrieval**: Queries the Knowledge Graph for entities mentioned in the query and extracts multi-hop neighborhoods to discover hidden indirect relationships.
2. **Entity Extraction & Canonicalization**:
   - Uses spaCy NER to identify `PERSON`, `LOCATION`, `ORGANIZATION`, and `DATE`.
   - Resolves surface variations (e.g. *"Sarah"*, *"Ms. Sarah Rao"*, *"Sarah Rao"* $\to$ `Sarah Rao`) into single canonical nodes.
3. **Co-occurrence Weighting**:
   - Entities co-occurring within the same 500-character chunk form an edge.
   - **Sentence-Level Bonus**: Entities co-occurring in the exact same sentence receive double weight ($w=2.0$).
   - Multiple documents mentioning the same pair dynamically increase the edge strength.
4. **Verifiable Evidence Tracing ("Killer Feature")**:
   - Every graph edge maintains an index of source document citations and exact sentence excerpts.
   - Clicking an edge reveals the exact corroborated quotes from the original files.
5. **AI Lead Detective Agent Briefing**:
   - Synthesizes findings into a structured detective dossier with deductive reasoning, key facts, suspects, timeline anchors, and confidence scores.

---

## 📁 The Demo Dataset: The 1995 Downtown Warehouse Cold Case

The system includes 8 interlocking fictional case files set in Mumbai, 1995 (`data/demo_docs/`):
1. `01_police_report_1995.txt` — Initial emergency response to the warehouse fire and early suspect interviews.
2. `02_newspaper_clipping_1995.txt` — Media report detailing financial irregularities at Mehta Industries.
3. `03_witness_statement_security.txt` — Gate guard's log of John Mehta and Sarah Rao arguing on the night of the fire.
4. `04_interview_sarah_rao.txt` — Interrogation transcript revealing clandestine solvent transfers.
5. `05_company_registry_mehta_ind.txt` — Corporate dossier uncovering shell entities and impending tax audits.
6. `06_warehouse_shipping_manifest.txt` — Salvaged cargo log authorizing hazardous solvent shipments.
7. `07_forensic_analysis_report.txt` — Lab findings linking accelerants to a gold pocket watch inscribed to John Mehta.
8. `08_investigator_closing_memo.txt` — Lead detective's closing theories connecting all evidence.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js v18+**

### 1. Start the Backend Server

```bash
# In the project root with the virtual environment:
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API live at `http://localhost:8000`. Interactive OpenAPI documentation at `http://localhost:8000/docs`.

### 2. Preload the Demo Case Files (Optional via CLI)

```bash
.\backend\.venv\Scripts\python.exe backend/preload_data.py
```
*(Or click **"Quick Load Demo"** in the web interface).*

### 3. Start the React Frontend

```bash
cd frontend
npm run dev
```
- Open `http://localhost:5173` in your browser.

### 4. Run Automated Tests

```bash
.\backend\.venv\Scripts\python.exe tests/test_pipeline.py
```

---

## 🎭 Step-by-Step Demo Walkthrough

1. **Open Dashboard**: Navigate to `http://localhost:5173` and click on **Demo Case** (or create a new case dossier).
2. **Execute Hybrid Search**:
   - Click any dynamic Quick Clue (e.g. *"Who was connected to the Downtown Warehouse in 1995?"* or *"What connects Sarah Rao and John Mehta?"*).
   - Observe the graph dynamically prune to the **connected subgraph** directly answering the query.
3. **Inspect AI Detective Dossier**:
   - Read the **AI Detective Assessment**, **Deductive Synthesis**, **Corroborated Case Facts**, and **Timeline Clues** in the right-hand evidence sidebar.
4. **Interrogate Relationships**:
   - Click the edge between **`Sarah Rao`** and **`Downtown Warehouse`** to view verbatim sentence citations from the source documents.
5. **Manage Case Documents**:
   - Switch to the **"Case Archive"** tab to view transcripts, extract entities, or upload new case documents with real-time graph re-indexing.
