import time
import re
import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from app.pipeline.ner import extract_entities
from app.pipeline.canonicalizer import canonicalize_entity, resolve_alias_in_case, is_valid_entity
from app.graph import get_graph_store
from app.vector import get_vector_store
from app.db.database import SessionLocal
from app.db.models import EvidenceModel, EntityModel, DocumentModel, ChunkModel
from app.search.intent import analyze_query_intent, QueryIntent, IntentProfile
from app.search.synthesizer import synthesize_investigative_answer

class HybridSearchEngine:
    """
    Executes intent-aware hybrid Information Retrieval combining:
    1. Intent Classification & Sub-facet Decomposition (intent.py)
    2. Multi-Facet Semantic Vector Search (ChromaDB) + Keyword Recall (SQLite)
    3. Dynamic Multi-Hop Graph Traversal & Subgraph Construction (NetworkX)
    4. Evidence Reranking & Coverage Validation
    5. AI Lead Detective Investigative Synthesis (synthesizer.py + validator.py)
    """

    def __init__(self):
        self.graph_store = get_graph_store()
        self.vector_store = get_vector_store()

    def search(
        self,
        query: str,
        top_k: int = 6,
        case_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Execute intent-aware hybrid search with multi-hop reasoning and accurate answer synthesis.
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

            # Deduplicate entity map by canonical name, filtering out junk entities
            entity_type_map = {}
            for e in case_entities:
                c_name = canonicalize_entity(e.canonical_name, e.entity_type)
                if c_name and is_valid_entity(c_name, e.entity_type):
                    if c_name not in entity_type_map:
                        entity_type_map[c_name] = e.entity_type

            entity_names = list(entity_type_map.keys())

            # Empty query returns full case graph
            if not query_strip:
                full_nodes = [
                    {"id": ent_name, "label": ent_name, "type": ent_type}
                    for ent_name, ent_type in entity_type_map.items()
                ]
                full_edges = []
                seen_edges = set()
                for ev in case_evidence_all:
                    s = canonicalize_entity(ev.source_entity)
                    t = canonicalize_entity(ev.target_entity)
                    if not s or not t or s == t or s not in entity_type_map or t not in entity_type_map:
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

            # 2. Intent Analysis & Sub-facet Decomposition
            intent_profile = analyze_query_intent(query_strip, entity_names)

            # 3. Dynamic Entity Linking (Maximal Non-overlapping Entities)
            primary_targets = set(intent_profile.target_entities)

            # If no entities were detected from case entities, attempt spaCy extraction
            if not primary_targets:
                raw_query_entities = extract_entities(query_strip)
                for e in raw_query_entities:
                    cname = canonicalize_entity(e.get("canonical_name", ""), e.get("type"))
                    if cname and cname in entity_type_map:
                        primary_targets.add(cname)
                        intent_profile.target_entities.append(cname)

            # 4. Multi-Facet Iterative Vector & Keyword Retrieval
            case_docs = set()
            if case_id is not None:
                case_docs = {d.filename for d in db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()}

            vector_hits = []
            seen_chunk_ids = set()

            # Search main query and all sub-facets
            for facet in intent_profile.query_facets[:4]:
                hits = self.vector_store.search(facet, top_k=top_k, case_id=case_id)
                for h in hits:
                    cid = (h.get("document_name"), h.get("chunk_id", h.get("text", "")[:40]))
                    if cid not in seen_chunk_ids:
                        if case_id is None or h.get("case_id") == case_id or h.get("document_name") in case_docs:
                            seen_chunk_ids.add(cid)
                            vector_hits.append(h)

            # 5. Extract Evidence Passages
            evidence_list = []
            seen_snippets = set()

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

            # Exact keyword and identifier chunk retrieval from SQL
            query_words = {
                w for w in re.findall(r"\b\w+\b", query_lower)
                if len(w) > 2 and w not in {
                    "what", "who", "where", "when", "why", "how", "the", "and", "was", "were",
                    "are", "with", "from", "for", "this", "that", "does", "did", "have", "been",
                    "about", "show", "tell", "give", "please", "can", "his", "her", "their", "which"
                }
            }

            if query_words or intent_profile.is_chronological_question:
                case_chunks_query = db.query(ChunkModel, DocumentModel.filename).join(
                    DocumentModel, ChunkModel.document_id == DocumentModel.id
                )
                if case_id is not None:
                    case_chunks_query = case_chunks_query.filter(ChunkModel.case_id == case_id)
                all_chunks = case_chunks_query.all()

                for chunk_rec, doc_name in all_chunks:
                    c_text_lower = chunk_rec.text.lower()
                    match_count = sum(1 for w in query_words if w in c_text_lower)

                    # Boost for timeline queries
                    has_date = bool(re.search(r"\b(?:\d{1,2}\s+[A-Z][a-z]+|\d{4})\b", chunk_rec.text))
                    if intent_profile.is_chronological_question and has_date:
                        match_count += 2

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

            # Add relationship evidence from EvidenceModel
            for ev in case_evidence_all:
                s = canonicalize_entity(ev.source_entity)
                t = canonicalize_entity(ev.target_entity)
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
                base = item.get("score", 0.8)
                t_low = item.get("text", "").lower()
                matches = sum(1.5 for w in query_words if w in t_low)
                # Boost if matches any target entity
                for tgt in primary_targets:
                    if tgt.lower() in t_low:
                        matches += 2.0
                return base + matches * 0.2

            evidence_list.sort(key=score_evidence, reverse=True)

            # 6. Build In-Memory NetworkX Graph for Dynamic Multi-Hop Traversal
            nx_graph = nx.Graph()
            for ent_name, ent_type in entity_type_map.items():
                nx_graph.add_node(ent_name, type=ent_type)

            for ev in case_evidence_all:
                s = canonicalize_entity(ev.source_entity)
                t = canonicalize_entity(ev.target_entity)
                if s and t and s != t and s in entity_type_map and t in entity_type_map:
                    if nx_graph.has_edge(s, t):
                        nx_graph[s][t]["weight"] += ev.weight
                    else:
                        nx_graph.add_edge(s, t, weight=ev.weight, document=ev.document_name, relationship=ev.relationship_type)

            # 7. Dynamic Multi-Hop Path Discovery and Subgraph Construction
            selected_nodes_set: Set[str] = set()
            connecting_edges_list = []
            seen_edge_keys = set()

            # Add primary targets
            for pt in primary_targets:
                if pt in entity_type_map:
                    selected_nodes_set.add(pt)

            # If 2 or more targets, find all multi-hop paths up to 3 hops between every pair
            target_list = [t for t in primary_targets if t in nx_graph]
            if len(target_list) >= 2:
                for i in range(len(target_list)):
                    for j in range(i + 1, len(target_list)):
                        u, v = target_list[i], target_list[j]
                        try:
                            # Find all simple paths up to 3 hops
                            for path in nx.all_simple_paths(nx_graph, source=u, target=v, cutoff=3):
                                for node_in_path in path:
                                    selected_nodes_set.add(node_in_path)
                                for k in range(len(path) - 1):
                                    e_u, e_v = path[k], path[k + 1]
                                    e_key = tuple(sorted([e_u, e_v]))
                                    if e_key not in seen_edge_keys:
                                        seen_edge_keys.add(e_key)
                                        edata = nx_graph.get_edge_data(e_u, e_v, {})
                                        connecting_edges_list.append({
                                            "source": e_u,
                                            "target": e_v,
                                            "weight": edata.get("weight", 1.0),
                                            "relationship": edata.get("relationship", "CO_OCCURRED_IN"),
                                            "document": edata.get("document", "Case Record")
                                        })
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            pass

            # If "who" question or broad entity identification, add neighbors of target nodes
            if intent_profile.is_who_question or len(selected_nodes_set) < 4:
                for pt in list(selected_nodes_set):
                    if pt in nx_graph:
                        for nbr in nx_graph.neighbors(pt):
                            nbr_type = entity_type_map.get(nbr, "UNKNOWN")
                            # Prioritize PERSON or meaningful entities
                            if intent_profile.is_who_question:
                                if nbr_type == "PERSON" or len(selected_nodes_set) < 8:
                                    selected_nodes_set.add(nbr)
                            else:
                                if len(selected_nodes_set) < 10:
                                    selected_nodes_set.add(nbr)

            # Add top participants from top evidence passages
            for ev in evidence_list[:6]:
                t_lower = ev.get("text", "").lower()
                for ent_name in entity_names:
                    if ent_name.lower() in t_lower and len(selected_nodes_set) < 12:
                        selected_nodes_set.add(ent_name)

            # Fallback if selected set is still sparse
            if not selected_nodes_set and entity_names:
                selected_nodes_set = set(entity_names[:6])

            # Gather all cross-edges among selected nodes
            for u in selected_nodes_set:
                for v in selected_nodes_set:
                    if u < v and nx_graph.has_edge(u, v):
                        e_key = (u, v)
                        if e_key not in seen_edge_keys:
                            seen_edge_keys.add(e_key)
                            edata = nx_graph[u][v]
                            connecting_edges_list.append({
                                "source": u,
                                "target": v,
                                "weight": edata.get("weight", 1.0),
                                "relationship": edata.get("relationship", "CO_OCCURRED_IN"),
                                "document": edata.get("document", "Case Record")
                            })

            # Clean subgraph nodes: only retain nodes that have at least one edge or are primary targets
            connected_node_ids = set()
            for e in connecting_edges_list:
                connected_node_ids.add(e["source"])
                connected_node_ids.add(e["target"])

            final_node_ids = connected_node_ids.union(primary_targets)
            if not final_node_ids:
                final_node_ids = selected_nodes_set

            subgraph_nodes = []
            seen_n = set()
            for nid in final_node_ids:
                if nid in entity_type_map and nid not in seen_n:
                    seen_n.add(nid)
                    subgraph_nodes.append({
                        "id": nid,
                        "label": nid,
                        "type": entity_type_map.get(nid, "UNKNOWN")
                    })

            valid_ids = {n["id"] for n in subgraph_nodes}
            final_edges = [
                e for e in connecting_edges_list
                if e["source"] in valid_ids and e["target"] in valid_ids
            ]

            subgraph = {
                "nodes": subgraph_nodes,
                "edges": final_edges,
                "total_nodes": len(subgraph_nodes),
                "total_edges": len(final_edges)
            }

            elapsed_ms = round((time.time() - start_time) * 1000, 1)

            # 8. AI Lead Detective Synthesis
            direct_answer = synthesize_investigative_answer(
                query=query_strip,
                query_entities=list(primary_targets),
                subgraph=subgraph,
                evidence_list=evidence_list,
                intent_profile=intent_profile
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
