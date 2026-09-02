import time
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from app.pipeline.ner import extract_entities
from app.graph import get_graph_store
from app.vector import get_vector_store
from app.db.database import SessionLocal
from app.db.models import EvidenceModel, EntityModel, DocumentModel

class HybridSearchEngine:
    """
    Executes hybrid Information Retrieval combining:
    1. Semantic Vector Search (ChromaDB)
    2. Case-Scoped Connected Subgraph Discovery (pruning unrelated/disconnected nodes)
    3. AI Detective Evidence Extraction & Direct Investigative Synthesis
    """

    def __init__(self):
        self.graph_store = get_graph_store()
        self.vector_store = get_vector_store()

    def search(self, query: str, top_k: int = 6, case_id: Optional[int] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Execute hybrid search with connected subgraph isolation.
        
        Args:
            query: User's investigation question
            top_k: Number of top results to return
            case_id: If specified, filter results to this case only
            db: Database session (will create one if not provided)
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

            entity_type_map = {e.canonical_name: e.entity_type for e in case_entities}
            entity_names = list(entity_type_map.keys())

            # If query is empty, return the complete case graph
            if not query_strip:
                full_nodes = []
                seen_nodes = set()
                for ent in case_entities:
                    if ent.canonical_name not in seen_nodes:
                        seen_nodes.add(ent.canonical_name)
                        full_nodes.append({
                            "id": ent.canonical_name,
                            "label": ent.canonical_name,
                            "type": ent.entity_type
                        })
                
                full_edges = []
                seen_edges = set()
                for ev in case_evidence_all:
                    edge_key = tuple(sorted([ev.source_entity, ev.target_entity]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        full_edges.append({
                            "source": ev.source_entity,
                            "target": ev.target_entity,
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

            # 2. Query Processing: Extract entities via spaCy NER
            query_entities = extract_entities(query_strip)
            detected_names = {e["canonical_name"] for e in query_entities}

            # 3. Entity Linking: Match against known entities in this case
            linked_entities = set()
            for ent_name in entity_names:
                ent_lower = ent_name.lower()
                # Direct match or substring match
                if (len(ent_name) >= 3 and ent_lower in query_lower) or (len(query_lower) >= 3 and query_lower in ent_lower):
                    linked_entities.add(ent_name)
                elif entity_type_map.get(ent_name) == "DATE":
                    for token in query_lower.split():
                        if len(token) == 4 and token.isdigit() and token in ent_name:
                            linked_entities.add(ent_name)

            # 4. Semantic Vector Search
            vector_hits = self.vector_store.search(query_strip, top_k=top_k)
            if case_id is not None:
                vector_hits = [hit for hit in vector_hits if hit.get("case_id") == case_id]

            vector_entities = set()
            top_doc_names = list({h["document_name"] for h in vector_hits if h.get("document_name")})
            if top_doc_names:
                matching_ev = [ev for ev in case_evidence_all if ev.document_name in top_doc_names]
                for ev in matching_ev[:20]:
                    vector_entities.add(ev.source_entity)
                    vector_entities.add(ev.target_entity)

            # 5. Connected Subgraph Construction (display ONLY connected nodes related to question)
            primary_targets = detected_names.union(linked_entities)
            if not primary_targets and vector_entities:
                primary_targets = set(list(vector_entities)[:4])

            # Gather connected edges involving primary targets
            subgraph_edges = []
            seen_edge_keys = set()
            connected_node_ids = set()

            if primary_targets:
                for ev in case_evidence_all:
                    s_in = ev.source_entity in primary_targets
                    t_in = ev.target_entity in primary_targets
                    if s_in or t_in:
                        edge_key = tuple(sorted([ev.source_entity, ev.target_entity]))
                        if edge_key not in seen_edge_keys:
                            seen_edge_keys.add(edge_key)
                            subgraph_edges.append({
                                "source": ev.source_entity,
                                "target": ev.target_entity,
                                "weight": ev.weight,
                                "relationship": ev.relationship_type,
                                "document": ev.document_name
                            })
                            connected_node_ids.add(ev.source_entity)
                            connected_node_ids.add(ev.target_entity)
            else:
                # Semantic match across vector passages
                for ev in case_evidence_all[:15]:
                    edge_key = tuple(sorted([ev.source_entity, ev.target_entity]))
                    if edge_key not in seen_edge_keys:
                        seen_edge_keys.add(edge_key)
                        subgraph_edges.append({
                            "source": ev.source_entity,
                            "target": ev.target_entity,
                            "weight": ev.weight,
                            "relationship": ev.relationship_type,
                            "document": ev.document_name
                        })
                        connected_node_ids.add(ev.source_entity)
                        connected_node_ids.add(ev.target_entity)

            # Add primary targets to connected nodes
            all_target_nodes = connected_node_ids.union(primary_targets)

            # Build filtered node list (strictly prune disconnected / unlinked entities)
            subgraph_nodes = []
            for n_id in all_target_nodes:
                # Include node if it is connected by at least 1 edge OR is an explicit query target
                is_connected = any(e["source"] == n_id or e["target"] == n_id for e in subgraph_edges)
                if is_connected or n_id in primary_targets:
                    ntype = entity_type_map.get(n_id, "UNKNOWN")
                    subgraph_nodes.append({
                        "id": n_id,
                        "label": n_id,
                        "type": ntype
                    })

            # Ensure edges only connect existing nodes
            valid_node_ids = {n["id"] for n in subgraph_nodes}
            final_edges = [
                e for e in subgraph_edges
                if e["source"] in valid_node_ids and e["target"] in valid_node_ids
            ]

            subgraph = {
                "nodes": subgraph_nodes,
                "edges": final_edges,
                "total_nodes": len(subgraph_nodes),
                "total_edges": len(final_edges)
            }

            # 6. Gather Verbatim Evidence Passages & Source Citations
            evidence_list = []
            seen_snippets = set()

            # High-scoring semantic vector passages
            for hit in vector_hits:
                snippet = hit["text"][:320].strip() + ("..." if len(hit["text"]) > 320 else "")
                key = (hit["document_name"], snippet)
                if key not in seen_snippets:
                    seen_snippets.add(key)
                    evidence_list.append({
                        "document": hit["document_name"],
                        "text": snippet,
                        "score": hit.get("score", 0.9),
                        "type": "SEMANTIC_PASSAGE"
                    })

            # Corroborated relationship co-occurrence evidence
            for edge in final_edges:
                s = edge["source"]
                t = edge["target"]
                matching = [
                    ev for ev in case_evidence_all
                    if (ev.source_entity == s and ev.target_entity == t) or (ev.source_entity == t and ev.target_entity == s)
                ]
                for ev in matching:
                    key = (ev.document_name, ev.snippet_text)
                    if key not in seen_snippets:
                        seen_snippets.add(key)
                        evidence_list.append({
                            "document": ev.document_name,
                            "text": ev.snippet_text,
                            "score": round(min(1.0, float(ev.weight) * 0.5), 2),
                            "source_entity": s,
                            "target_entity": t,
                            "type": "RELATIONSHIP_EVIDENCE"
                        })

            evidence_list.sort(key=lambda x: x.get("score", 0), reverse=True)
            elapsed_ms = round((time.time() - start_time) * 1000, 1)

            # 7. AI Detective Agent Direct Investigative Synthesis
            from app.search.synthesizer import synthesize_investigative_answer
            direct_answer = synthesize_investigative_answer(
                query=query_strip,
                query_entities=[e["canonical_name"] for e in query_entities],
                subgraph=subgraph,
                evidence_list=evidence_list
            )

            return {
                "query": query_strip,
                "query_entities": [e["canonical_name"] for e in query_entities],
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
