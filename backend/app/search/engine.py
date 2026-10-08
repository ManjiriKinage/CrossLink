import time
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from app.pipeline.ner import extract_entities
from app.pipeline.canonicalizer import canonicalize_entity
from app.graph import get_graph_store
from app.vector import get_vector_store
from app.db.database import SessionLocal
from app.db.models import EvidenceModel, EntityModel, DocumentModel, ChunkModel

class HybridSearchEngine:
    """
    Executes hybrid Information Retrieval combining:
    1. Semantic Vector Search (ChromaDB)
    2. Situation-Connected Subgraph Construction (connected evidence web, no starbursts)
    3. Person-Accurate Investigative Synthesis
    """

    def __init__(self):
        self.graph_store = get_graph_store()
        self.vector_store = get_vector_store()

    def search(self, query: str, top_k: int = 6, case_id: Optional[int] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Execute hybrid search with situation-connected subgraph and accurate answer synthesis.
        """
        start_time = time.time()
        query_strip = query.strip() if query else ""
        query_lower = query_strip.lower()
        
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        try:
            # 1. Fetch all known entities and evidence for this case
            case_entities_query = db.query(EntityModel)
            case_evidence_query = db.query(EvidenceModel)
            if case_id is not None:
                case_entities_query = case_entities_query.filter(EntityModel.case_id == case_id)
                case_evidence_query = case_evidence_query.filter(EvidenceModel.case_id == case_id)
            
            case_entities = case_entities_query.all()
            case_evidence_all = case_evidence_query.all()

            # Deduplicate entity map by canonical name
            entity_type_map = {}
            for e in case_entities:
                c_name = canonicalize_entity(e.canonical_name, e.entity_type)
                if c_name not in entity_type_map:
                    entity_type_map[c_name] = e.entity_type

            entity_names = list(entity_type_map.keys())

            # If query is empty, return the complete deduplicated case graph
            if not query_strip:
                full_nodes = []
                seen_nodes = set()
                for ent_name, ent_type in entity_type_map.items():
                    if ent_name not in seen_nodes:
                        seen_nodes.add(ent_name)
                        full_nodes.append({
                            "id": ent_name,
                            "label": ent_name,
                            "type": ent_type
                        })
                
                full_edges = []
                seen_edges = set()
                for ev in case_evidence_all:
                    s = canonicalize_entity(ev.source_entity, "UNKNOWN")
                    t = canonicalize_entity(ev.target_entity, "UNKNOWN")
                    if not s or not t or s == t:
                        continue
                    edge_key = tuple(sorted([s, t]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        full_edges.append({
                            "source": s,
                            "target": t,
                            "weight": ev.weight,
                            "relationship": ev.relationship_type,
                            "document": ev.document_name
                        })
                
                elapsed_ms = round((time.time() - start_time) * 1000, 1)
                return {
                    "query": "",
                    "query_entities": [],
                    "direct_answer": None,
                    "nodes": full_nodes,
                    "edges": full_edges,
                    "evidence": [],
                    "metrics": {
                        "execution_time_ms": elapsed_ms,
                        "total_nodes": len(full_nodes),
                        "total_edges": len(full_edges),
                        "total_evidence": 0,
                        "vector_hits_count": 0
                    }
                }

            # 2. Query Processing: Extract entities via spaCy NER & Canonicalize
            raw_query_entities = extract_entities(query_strip)
            detected_names = {canonicalize_entity(e["canonical_name"], e["type"]) for e in raw_query_entities if e.get("canonical_name")}

            # 3. Entity Linking: Substring and token matching against case entities
            linked_entities = set()
            for ent_name in entity_names:
                ent_lower = ent_name.lower()
                # Direct match or multi-token substring match
                if len(ent_name) >= 3 and ent_lower in query_lower:
                    linked_entities.add(ent_name)
                elif any(word in ent_lower for word in query_lower.split() if len(word) >= 4):
                    # Check individual meaningful tokens (e.g. "kulkarni", "bakshi", "verma", "sarah")
                    for token in query_lower.split():
                        if len(token) >= 4 and token in ent_lower:
                            linked_entities.add(ent_name)

            # Combined primary entities explicitly mentioned or queried
            primary_targets = detected_names.union(linked_entities)

            # 4. Hybrid Semantic Vector Search (Case-Scoped)
            vector_hits = self.vector_store.search(query_strip, top_k=top_k * 2, case_id=case_id)
            case_docs = set()
            if case_id is not None:
                case_docs = {d.filename for d in db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()}
                vector_hits = [hit for hit in vector_hits if (hit.get("case_id") == case_id or hit.get("document_name") in case_docs)]

            # 5. Extract Evidence Passages (Ranked by Relevance)
            evidence_list = []
            seen_snippets = set()

            # Add vector semantic hits with generous text length
            for hit in vector_hits:
                snippet = hit["text"].strip()
                key = (hit["document_name"], snippet[:120])
                if key not in seen_snippets:
                    seen_snippets.add(key)
                    evidence_list.append({
                        "document": hit["document_name"],
                        "text": snippet,
                        "score": hit.get("score", 0.9),
                        "type": "SEMANTIC_PASSAGE"
                    })

            # Also search SQL chunks directly for keyword recall within the case
            query_words = {w for w in re.findall(r'\b\w+\b', query_lower) if len(w) > 2 and w not in {
                'what', 'who', 'where', 'when', 'why', 'how', 'the', 'and', 'was', 'were',
                'are', 'with', 'from', 'for', 'this', 'that', 'does', 'did', 'have', 'been',
                'about', 'show', 'tell', 'give', 'please', 'can', 'his', 'her', 'their', 'which'
            }}
            if query_words:
                case_chunks_query = db.query(ChunkModel, DocumentModel.filename).join(DocumentModel, ChunkModel.document_id == DocumentModel.id)
                if case_id is not None:
                    case_chunks_query = case_chunks_query.filter(ChunkModel.case_id == case_id)
                all_chunks = case_chunks_query.all()
                for chunk_rec, doc_name in all_chunks:
                    c_text_lower = chunk_rec.text.lower()
                    match_count = sum(1 for w in query_words if w in c_text_lower)
                    if match_count >= 1:
                        snippet = chunk_rec.text.strip()
                        key = (doc_name, snippet[:120])
                        if key not in seen_snippets:
                            seen_snippets.add(key)
                            evidence_list.append({
                                "document": doc_name,
                                "text": snippet,
                                "score": round(0.75 + min(0.2, match_count * 0.05), 2),
                                "type": "KEYWORD_CHUNK"
                            })

            # Add relationship co-occurrence evidence for target entities or query terms
            for ev in case_evidence_all:
                s = canonicalize_entity(ev.source_entity, "UNKNOWN")
                t = canonicalize_entity(ev.target_entity, "UNKNOWN")
                include_ev = False
                if primary_targets and (s in primary_targets or t in primary_targets):
                    include_ev = True
                elif query_words and any(w in s.lower() or w in t.lower() or w in ev.snippet_text.lower() for w in query_words):
                    include_ev = True

                if include_ev:
                    key = (ev.document_name, ev.snippet_text[:120])
                    if key not in seen_snippets:
                        seen_snippets.add(key)
                        evidence_list.append({
                            "document": ev.document_name,
                            "text": ev.snippet_text,
                            "score": round(min(1.0, float(ev.weight) * 0.45 + 0.5), 2),
                            "source_entity": s,
                            "target_entity": t,
                            "type": "RELATIONSHIP_EVIDENCE"
                        })

            # Score and sort evidence by relevance
            def score_evidence(item):
                base_score = item.get("score", 0.8)
                t_lower = item.get("text", "").lower()
                matches = sum(1 for w in query_words if w in t_lower)
                return base_score + matches * 0.25

            evidence_list.sort(key=score_evidence, reverse=True)

            # 6. Situation-Connected Subgraph Construction (No Starbursts, Cross-Connected Network)
            # Find entities mentioned across the top evidence passages
            evidence_entities = set()
            for ev in evidence_list[:6]:
                t_lower = ev.get("text", "").lower()
                for ent_name in entity_names:
                    if ent_name.lower() in t_lower:
                        evidence_entities.add(ent_name)

            # Narrative node set = Primary queried entities + Top evidence participants
            narrative_nodes = primary_targets.union(evidence_entities)
            if not narrative_nodes and entity_names:
                narrative_nodes = set(entity_names[:5])

            # Limit narrative nodes to 8 most relevant to avoid clutter
            ranked_nodes = list(primary_targets) + [n for n in evidence_entities if n not in primary_targets]
            selected_nodes_set = set(ranked_nodes[:8])

            # Gather ALL cross-edges among selected narrative nodes (Induced Subgraph)
            subgraph_edges = []
            seen_edge_keys = set()
            connected_node_ids = set()

            for ev in case_evidence_all:
                s = canonicalize_entity(ev.source_entity, "UNKNOWN")
                t = canonicalize_entity(ev.target_entity, "UNKNOWN")
                if not s or not t or s == t:
                    continue

                # Include edge if BOTH nodes are in the situation narrative
                if s in selected_nodes_set and t in selected_nodes_set:
                    edge_key = tuple(sorted([s, t]))
                    if edge_key not in seen_edge_keys:
                        seen_edge_keys.add(edge_key)
                        subgraph_edges.append({
                            "source": s,
                            "target": t,
                            "weight": ev.weight,
                            "relationship": ev.relationship_type,
                            "document": ev.document_name
                        })
                        connected_node_ids.add(s)
                        connected_node_ids.add(t)

            # If not enough cross-edges found, add direct 1-hop connections from primary targets
            if len(subgraph_edges) < 3 and primary_targets:
                for ev in case_evidence_all:
                    s = canonicalize_entity(ev.source_entity, "UNKNOWN")
                    t = canonicalize_entity(ev.target_entity, "UNKNOWN")
                    if not s or not t or s == t:
                        continue
                    if (s in primary_targets or t in primary_targets) and (s in entity_names and t in entity_names):
                        edge_key = tuple(sorted([s, t]))
                        if edge_key not in seen_edge_keys:
                            seen_edge_keys.add(edge_key)
                            subgraph_edges.append({
                                "source": s,
                                "target": t,
                                "weight": ev.weight,
                                "relationship": ev.relationship_type,
                                "document": ev.document_name
                            })
                            connected_node_ids.add(s)
                            connected_node_ids.add(t)
                            if len(subgraph_edges) >= 7:
                                break

            # Build final clean node list
            all_valid_node_ids = connected_node_ids.union(primary_targets).union(selected_nodes_set)
            subgraph_nodes = []
            seen_n = set()
            for n_id in all_valid_node_ids:
                if n_id not in seen_n:
                    seen_n.add(n_id)
                    ntype = entity_type_map.get(n_id, "UNKNOWN")
                    subgraph_nodes.append({
                        "id": n_id,
                        "label": n_id,
                        "type": ntype
                    })

            # Ensure edges only connect existing nodes
            valid_ids = {n["id"] for n in subgraph_nodes}
            final_edges = [
                e for e in subgraph_edges
                if e["source"] in valid_ids and e["target"] in valid_ids
            ]

            subgraph = {
                "nodes": subgraph_nodes,
                "edges": final_edges,
                "total_nodes": len(subgraph_nodes),
                "total_edges": len(final_edges)
            }

            elapsed_ms = round((time.time() - start_time) * 1000, 1)

            # 7. AI Detective Agent Accurate Investigative Synthesis
            from app.search.synthesizer import synthesize_investigative_answer
            direct_answer = synthesize_investigative_answer(
                query=query_strip,
                query_entities=list(primary_targets),
                subgraph=subgraph,
                evidence_list=evidence_list
            )

            return {
                "query": query_strip,
                "query_entities": list(primary_targets),
                "direct_answer": direct_answer,
                "nodes": subgraph_nodes,
                "edges": final_edges,
                "evidence": evidence_list,
                "metrics": {
                    "execution_time_ms": elapsed_ms,
                    "total_nodes": len(subgraph_nodes),
                    "total_edges": len(final_edges),
                    "total_evidence": len(evidence_list),
                    "vector_hits_count": len(vector_hits)
                }
            }
        finally:
            if close_db:
                db.close()

_search_engine = None

def get_search_engine() -> HybridSearchEngine:
    global _search_engine
    if _search_engine is None:
        _search_engine = HybridSearchEngine()
    return _search_engine
