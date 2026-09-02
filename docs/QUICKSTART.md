# Quick Start Guide: `cold_case`

This guide explains how to set up, configure, run, and test the `cold_case` Information Retrieval & Knowledge Graph system from scratch.

---

## 1. Prerequisites

Ensure the following tools are installed on your host machine:

| Requirement | Minimum Version | Verified Version | Notes |
|---|---|---|---|
| **Python** | 3.10+ | 3.13 / 3.11 | Required for FastAPI backend and NLP pipeline |
| **Node.js** | 18.x+ | 20.x / 22.x | Required for React 19 / Vite frontend |
| **npm** | 9.x+ | 10.x | Node package manager |
| **Git** | 2.x+ | Any modern | Version control |
| **Local Disk Space** | ~1.5 GB | — | For Python dependencies, spaCy model, and HuggingFace embeddings (`all-MiniLM-L6-v2`) |

---

## 2. Installation & Setup

### Step 1: Clone Repository
```bash
git clone <repository_url> cold_case
cd cold_case
```

### Step 2: Backend Setup (Python Virtual Environment)

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (.venv)
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (cmd.exe):
.venv\Scripts\activate.bat
# On Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download the required spaCy English language model
python -m spacy download en_core_web_sm

# Return to repository root
cd ..
```

### Step 3: Frontend Setup (Node.js / React)

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Return to repository root
cd ..
```

---

## 3. Environment Variables Configuration

Copy the sample environment file to `.env` in the project root:

```bash
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS:
cp .env.example .env
```

### `.env` File Reference

| Variable Name | Default Value | Description | Required? |
|---|---|---|---|
| `DATABASE_URL` | `sqlite:///cold_case.db` | SQLAlchemy connection string for relational storage | No (defaults to local SQLite) |
| `CHROMA_PERSIST_DIR` | `data/chroma` | Directory for persistent ChromaDB vector storage | No |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformers model for 384-d dense embeddings | No |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model for Named Entity Recognition | No |
| `CHUNK_SIZE` | `500` | Text chunk size in characters | No |
| `CHUNK_OVERLAP` | `100` | Overlapping characters between consecutive chunks | No |
| `NEO4J_URI` | `""` (empty) | Neo4j bolt URI (e.g. `bolt://localhost:7687`). If empty, uses NetworkX in-memory | No (optional) |
| `NEO4J_USER` | `neo4j` | Neo4j database username | Only if Neo4j used |
| `NEO4J_PASSWORD` | `password` | Neo4j database password | Only if Neo4j used |

---

## 4. Database Setup & Preloading Demo Data

### Option A: Automatic Initialization via CLI
The backend automatically creates all relational tables upon launch (`init_db()`). To preload the 8 demo case files (`data/demo_docs/*.txt` for the 1995 Downtown Warehouse Arson case), run:

```bash
# From repository root using the virtual environment:
.\backend\.venv\Scripts\python.exe backend/preload_data.py
# (On Linux / macOS: ./backend/.venv/bin/python backend/preload_data.py)
```

### Option B: Preload via Web Interface
You can also launch the application and click **"Quick Load Demo"** on the dashboard or inside any case.

---

## 5. Starting the Application

Launch the backend and frontend in two separate terminals.

### Terminal 1: Backend API Server
```bash
# In the cold_case root directory:
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API URL**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`

### Terminal 2: Frontend Web Application
```bash
# In the cold_case root directory:
cd frontend
npm run dev
```
- **Frontend URL**: `http://localhost:5173`

---

## 6. Running Automated Tests & Verification

### Run IR Pipeline Test Suite:
```bash
# Executes cleaner, chunker, NER, cooccurrence, ingestion, and hybrid search tests:
.\backend\.venv\Scripts\python.exe tests/test_pipeline.py
```
Expected output:
```text
Running Cold Case IR Pipeline tests...
[PASS] test_cleaner passed
[PASS] test_chunker passed (3 chunks created)
[PASS] test_ner_and_canonicalization passed
[PASS] test_cooccurrence passed
[PASS] Document ingested: test_investigation.txt, entities: 5
Search results: 6 nodes, 4 edges, 3 citations
[PASS] test_end_to_end_ingest_and_search passed

ALL PIPELINE TESTS PASSED!
```

### Verify Frontend Production Build:
```bash
cd frontend
npm run build
```
Expected output:
```text
✓ built in ~1.2s
dist/index.html
dist/assets/index-*.css
dist/assets/index-*.js
```

---

## 7. Troubleshooting Common Issues

1. **`ModuleNotFoundError: No module named 'spacy'` / `en_core_web_sm`**:
   - Ensure the virtual environment is activated.
   - Run `pip install spacy` and `python -m spacy download en_core_web_sm`.

2. **Port 8000 or 5173 in use**:
   - For backend: run on a different port: `--port 8080`.
   - For frontend: Vite automatically offers the next open port (e.g. `http://localhost:5174`).

3. **Missing `case_id` in API calls**:
   - All modern case routes require the case ID in the URL: `/api/cases/{case_id}/search` or `/api/cases/{case_id}/documents`.
