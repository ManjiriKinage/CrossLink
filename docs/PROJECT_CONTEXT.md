# Project Context: `cold_case`

This document details the project background, problem space, conceptual foundation, technology choices, and the current implementation status of `cold_case`.

---

## 1. Project Overview

### Simple Explanation
`cold_case` is an intelligent investigative workspace. When investigators, journalists, or auditors have folders full of unorganized documents (such as police statements, witness interviews, company registries, and forensic reports), `cold_case` reads every file, identifies the people, locations, companies, and dates mentioned, discovers how they are connected, and creates an interactive visual web of connections. When the user asks a question (e.g. *"What connects Sarah Rao and John Mehta?"*), the system does not guess—it acts as an **AI Lead Detective**, providing a clear briefing grounded in exact quotes from the source documents and highlighting only the relevant connected parts of the knowledge graph.

### Technical Description
`cold_case` is an evidence-traceable, multi-modal **Information Retrieval (IR) and Knowledge Graph system**. It processes unstructured text documents through a deterministic 6-stage NLP pipeline (cleaning $\to$ sliding-window chunking $\to$ spaCy Named Entity Recognition $\to$ entity canonicalization $\to$ sentence-level co-occurrence weighting $\to$ dense vector embedding). The system indexes case data across an ACID relational database (SQLAlchemy/SQLite), a graph store (NetworkX/Neo4j), and a vector database (ChromaDB with `all-MiniLM-L6-v2` 384-dimensional embeddings). Queries execute a hybrid retrieval algorithm combining semantic vector similarity with entity-anchored subgraph traversal, pruning disconnected orphan nodes and feeding retrieved context into an AI Detective Synthesizer for factual deduction and citation attribution.

---

## 2. Problem Being Solved

In complex investigations, intelligence analysis, forensic accounting, and cold case reviews:
1. **Document Fragmentation**: Evidence is scattered across multiple file formats, dates, and witnesses.
2. **Cognitive Overload**: Humans struggle to remember multi-hop connections across dozens of files (e.g. Witness A in 1995 mentioning Person X meeting Person Y at Location Z, while a Shipping Manifest in File 6 links Person Y to a chemical solvent).
3. **LLM Hallucinations**: Standard generative AI chat models frequently hallucinate facts, fabricate relationships, and lack auditable citations.
4. **Loss of Provenance**: Traditional search engines return links to full documents without pinpointing the exact corroborated sentence or explaining the relationship logic.

`cold_case` solves this by guaranteeing **strict evidence provenance**: every node and edge in the knowledge graph is linked directly to verbatim text snippets and file origins.

---

## 3. Target Users

- **Law Enforcement & Cold Case Detectives**: Reviewing historic unsolved cases, finding inconsistencies in suspect testimonies across decades.
- **Investigative Journalists**: Sifting through leaked datasets, financial records, and corporate filings to uncover hidden networks.
- **Compliance, Fraud & AML Auditors**: Analyzing transaction logs, company registrations, and communication transcripts to detect shell corporations and collusion.
- **Legal Defense & Prosecution Teams**: Organizing case discovery materials into verifiable timelines and entity dossiers.

---

## 4. Core Concept Pipeline

The workflow of `cold_case` follows an end-to-end evidence discovery pipeline:

```
[Raw Case Documents] (.txt files)
       ↓
[Text Extraction & Normalization] (cleaner.py: Unicode, whitespace, punctuation fixes)
       ↓
[Sliding Window Chunking] (chunker.py: 500-character windows, 100-character overlap)
       ↓
[Named Entity Recognition] (ner.py: spaCy en_core_web_sm extracting PERSON, LOCATION, ORG, DATE)
       ↓
[Entity Canonicalization] (canonicalizer.py: Surface-form alias resolution)
       ↓
[Relationship & Co-Occurrence Discovery] (cooccurrence.py: Sentence-level w=2.0, chunk-level w=1.0)
       ↓
[Multi-Modal Storage]
  ├── Relational DB (SQLAlchemy/SQLite: cases, documents, chunks, entities, evidence)
  ├── Graph Store (NetworkX/Neo4j: entity nodes, weighted edges, evidence snippets)
  └── Vector Store (ChromaDB: 384-d dense embeddings of text chunks)
       ↓
[Investigative Search Query] (User asks natural language question or clicks Quick Clue)
       ↓
[Hybrid Retrieval Engine] (engine.py: Query NER + Vector Search + Subgraph Traversal)
       ↓
[Pruned Connected Subgraph] (Canvas filters out disconnected nodes, displays relevant cluster)
       ↓
[AI Detective Agent Answer] (synthesizer.py: Direct briefing, deductive reasoning, key facts)
       ↓
[Verifiable Evidence Citations] (Verbatim excerpts with document tags & confidence scores)
```

---

## 5. Current Features

### Fully Implemented
- **Multi-Case Dossier Management**: Create, list, inspect, and delete distinct investigation cases with complete data isolation.
- **Dynamic File Uploading**: Single and batch upload of plain text documents (`.txt`) with universal character encoding detection (UTF-8, UTF-16, Latin-1, CP1252, ISO-8859-1).
- **6-Stage NLP Ingestion Pipeline**:
  - Text normalization (`cleaner.py`).
  - Sliding-window chunking (`chunker.py`).
  - Named Entity Recognition via spaCy (`ner.py`).
  - Canonicalization & alias resolution (`canonicalizer.py`).
  - Sentence-level bonus co-occurrence extraction (`cooccurrence.py`).
  - Dense vector indexing in ChromaDB (`chroma_store.py`).
- **Hybrid Retrieval Engine**:
  - Query entity extraction & entity linking against case nodes.
  - Case-filtered semantic vector search in ChromaDB.
  - Connected subgraph construction with automatic pruning of disconnected/orphan nodes.
- **AI Lead Detective Agent Briefing**:
  - Direct investigative answer tailored to the question intent (Who, What, Where, Why/How).
  - Deductive synthesis reasoning explaining how facts link together.
  - Corroborated case facts with bracketed document citations (`[Source: ...]`).
  - Suspects & Persons of Interest profile.
  - Reconstructed chronological timeline anchors.
  - Multi-source confidence score calculation.
- **Interactive Force-Directed Knowledge Graph**:
  - Vis.js canvas with entity-type color coding (Person: Blue, Location: Amber, Organization: Emerald, Date: Rose).
  - Whole-case graph view on initial load and search reset.
  - Question-focused connected subgraph view on query execution.
  - Interactive click-to-interrogate relationships and nodes.
- **Evidence & Dossier Sidebar**:
  - Tabbed interface: AI Briefing, Source Citations (with relevance scores), and Timeline Reconstruction.
  - Verbatim excerpt highlighting and jump-to-document action.
- **Case Archive & Explorer**:
  - Document file browser with chunk and entity statistics.
  - Verbatim transcript reader.
  - Extracted named entities tag cloud.
  - Direct document deletion and case re-synchronization.
- **Dynamic Case-Specific Quick Clues**:
  - Backend and frontend generation of contextual clue pills derived from the active case's top entity pairs, locations, and documents.
- **Demo Case Preloader**:
  - 8 interlocking case files for the 1995 Downtown Warehouse Arson & Financial Fraud cold case.
- **Automated Test Suite**:
  - `tests/test_pipeline.py` verifying cleaner, chunker, NER, co-occurrence weighting, end-to-end ingestion, and hybrid search.

### Partially Implemented
- **Neo4j Backend Support**: `neo4j_store.py` is implemented and functional if `NEO4J_URI` is provided, but currently defaults to `NetworkXGraphStore` for zero-dependency standalone operation.
- **PDF Extraction**: `pypdfium2` is installed in `backend/requirements.txt`, but frontend upload currently focuses on `.txt` plain text files.

### Planned
- **Direct PDF/DOCX Ingestion UI**: Uploading PDF and Word documents directly with OCR preprocessing.
- **Multi-Hop Path Finder**: An interface tool allowing detectives to select two arbitrary entities (e.g. Suspect A and Offshore Account B) and compute all connecting evidentiary paths up to 4 hops.
- **Exportable Investigation Report**: PDF/Markdown export of the AI Detective Briefing, complete with graph snapshot and citation appendix.
- **User Authentication & Role-Based Access**: Investigator vs Auditor permission scoping.

### Known Issues
- Large graph physics stabilization can take 1–2 seconds for cases with over 200+ entities (workaround: physics pause button is provided).
- ChromaDB SQLite locking on Windows if multiple background ingestion processes run concurrently without connection pooling.

---

## 6. Technology Stack (Actual Implementation)

| Layer | Technology | Version | Purpose in `cold_case` |
|---|---|---|---|
| **Backend Runtime** | Python | 3.10+ / 3.13 | Core backend language |
| **API Framework** | FastAPI | >=0.110.0 | High-performance asynchronous REST API with OpenAPI documentation |
| **ASGI Server** | Uvicorn | >=0.28.0 | ASGI web server for FastAPI |
| **ORM & Database** | SQLAlchemy | >=2.0.28 | Object Relational Mapper for cases, documents, chunks, entities, and evidence |
| **Relational Storage** | SQLite | 3.x | Default local database (`cold_case.db`) |
| **NLP & NER** | spaCy | >=3.7.4 | Named Entity Recognition using `en_core_web_sm` model |
| **Embeddings** | SentenceTransformers | >=2.5.0 | Generating 384-dimensional dense semantic vectors using `all-MiniLM-L6-v2` |
| **Vector Database** | ChromaDB | >=0.4.24 | Persistent HNSW cosine-distance index for semantic passage search (`data/chroma`) |
| **Graph Store** | NetworkX | >=3.2.0 | In-memory graph engine for entity nodes, relationship edges, and subgraph traversal |
| **Graph Store (Alt)** | Neo4j Python Driver | >=5.18.0 | Optional Cypher driver for enterprise graph persistence |
| **Frontend Framework** | React | 19.2.8 | Declarative component UI |
| **Build Tool** | Vite | 8.2.2 | Fast frontend development server and production bundler |
| **Graph Visualization** | Vis-network | 10.1.2 | Interactive force-directed 2D canvas with physics simulation |
| **Iconography** | Lucide React | 1.39.0 | UI iconography |
| **Styling** | Vanilla CSS | CSS3 | Custom Noir Dark-Mode design system with CSS custom properties |

---

## 7. Current Development Phase

The project is currently in **Phase 3 (Case-Isolated Multi-Dossier & AI Detective Agent)**:
- Core multi-case isolation is functional.
- Hybrid vector + graph search with connected subgraph isolation is active.
- AI Detective synthesizer provides fact-grounded briefings with verbatim citations.
- Dynamic file upload and case-specific Quick Clues are fully integrated.
