# Architecture Decision Records (ADRs): `cold_case`

This document records the architectural and design decisions made for `cold_case`, including context, rationale, consequences, and alternatives considered.

---

## ADR-001: Multi-Modal Persistence Architecture (SQLAlchemy + ChromaDB + Graph)

### Status: Accepted
### Context:
Investigative analysis requires three distinct retrieval modalities:
1. **Relational metadata & transcript storage** (auditable, ACID-compliant, case-isolated).
2. **Dense semantic vector search** (concept-based similarity across text chunks).
3. **Entity relationship graphs** (multi-hop traversal, co-occurrences, network visualization).

### Decision:
Implement a tri-modal storage layer:
- **SQLite (SQLAlchemy)** for relational entities: `cases`, `documents`, `chunks`, `entities`, and `evidence`.
- **ChromaDB** with `SentenceTransformers` (`all-MiniLM-L6-v2`) for 384-dimensional dense semantic vectors.
- **NetworkX / Neo4j** for entity-relationship graph traversal and co-occurrence weighting.

### Consequences:
- **Pros**: Complete query flexibility—can perform semantic similarity, relational joins, and multi-hop graph traversals without forcing a single database engine to handle mismatched paradigms.
- **Cons**: Requires synchronization across the three storage engines during document ingestion and deletion.

---

## ADR-002: Embedded Graph Engine (NetworkX) with Optional Neo4j Adapter

### Status: Accepted
### Context:
Requiring an external running Neo4j database server increases setup friction for local developer quickstart and standalone offline desktop environments.

### Decision:
Provide an abstract `GraphStoreBase` interface with:
1. **`NetworkXGraphStore` (Default)**: Zero-dependency in-memory graph store backed by `networkx.Graph`, requiring zero external processes.
2. **`Neo4jGraphStore` (Optional)**: Cypher-backed graph store activated if `NEO4J_URI` is provided in `.env`.

### Consequences:
- **Pros**: Instant out-of-the-box local development with no Docker or external database service required.
- **Cons**: NetworkX graphs reside in memory and rebuild from the relational `EvidenceModel` on startup.

---

## ADR-003: Sentence-Level Co-Occurrence Weighting ($w=2.0$ Bonus)

### Status: Accepted
### Context:
In natural language documents, two entities appearing in the exact same sentence indicate a much stronger direct connection (e.g. *"John Mehta handed the key to Sarah Rao"*) than two entities appearing 400 characters apart in different paragraphs of the same sliding window.

### Decision:
When parsing entity pairs within a chunk:
- If both entities co-occur within the **same sentence**, assign weight $w=2.0$.
- If they co-occur within the **same chunk but different sentences**, assign weight $w=1.0$.
- Multiple documents or chunks mentioning the same pair accumulate additive weights.

### Consequences:
- **Pros**: High-relevance relationships automatically bubble to the top of graph visualization and evidence ranking.

---

## ADR-004: Strict Case-Level Data Isolation

### Status: Accepted
### Context:
Investigative and intelligence systems must strictly prevent cross-case data contamination. Evidence from "Case A" must never leak into graph searches or vector retrieval for "Case B".

### Decision:
- Every table (`documents`, `chunks`, `entities`, `evidence`) contains a `case_id` foreign key with cascade deletion.
- ChromaDB vector queries filter chunks by `case_id` metadata.
- Graph search and evidence endpoints are scoped to `/api/cases/{case_id}/*`.

### Consequences:
- **Pros**: Complete data separation and safe multi-dossier operations.

---

## ADR-005: Query-Connected Subgraph Pruning

### Status: Accepted
### Context:
When an investigator queries a case with 100+ entities, displaying the entire graph causes visual clutter and obscures the answer. However, displaying a blank canvas loses the relationship context.

### Decision:
- On initial case load or search reset, display the **full case graph**.
- When an investigative query is submitted, extract query entities, vector hits, and their immediate relationship edges, and **prune all disconnected/unrelated orphan nodes**, displaying only the focused connected cluster that answers the query.

### Consequences:
- **Pros**: Clear, focused graph visualization directly supporting the AI Detective briefing.

---

## ADR-006: Dedicated AI Lead Detective Persona in Search Synthesis

### Status: Accepted
### Context:
Standard search responses that merely return raw text fragments force the investigator to assemble the narrative manually.

### Decision:
Structure search synthesis (`synthesizer.py`) into an auditable **AI Detective Dossier**:
1. **Lead Investigator Assessment**: Clear direct answer answering the query intent.
2. **Deductive Reasoning**: Explaining how the evidence connects suspects and firms.
3. **Corroborated Facts**: Bulleted statements with bracketed citations (`[Source: ...]`).
4. **Suspects & Persons of Interest Profile**: Highlighting key individuals.
5. **Timeline Clues**: Extracted date and time anchors.
6. **Confidence Score**: Quantitative evaluation of multi-source corroboration.

### Consequences:
- **Pros**: Delivers immediate actionable intelligence while preserving 100% verifiable citations.

---

## ADR-007: Working Project Name Policy (`cold_case`)

### Status: Accepted
### Context:
The final commercial trade name for the product has not been finalized.

### Decision:
The repository and all technical documentation shall strictly use the project identifier `cold_case`. No speculative or unauthorized commercial product names (e.g. "TraceNet") shall be used in code or documentation.
