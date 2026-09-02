from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from app.graph.base import GraphStoreBase

class Neo4jGraphStore(GraphStoreBase):
    """
    Neo4j implementation of GraphStoreBase using official Bolt driver.
    """

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_node(self, node_id: str, label: str, entity_type: str, properties: Optional[Dict[str, Any]] = None):
        props = properties or {}
        query = (
            "MERGE (n:Entity {id: $id}) "
            "SET n.label = $label, n.type = $type, n += $props"
        )
        with self.driver.session() as session:
            session.run(query, id=node_id, label=label, type=entity_type, props=props)

    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0, evidence: Optional[Dict[str, Any]] = None):
        query = (
            "MATCH (a:Entity {id: $source_id}), (b:Entity {id: $target_id}) "
            "MERGE (a)-[r:CO_OCCURRED_IN]-(b) "
            "ON CREATE SET r.weight = $weight, r.evidence = [$evidence], r.documents = [$doc] "
            "ON MATCH SET r.weight = r.weight + $weight, "
            "r.evidence = CASE WHEN $evidence IN r.evidence THEN r.evidence ELSE r.evidence + $evidence END, "
            "r.documents = CASE WHEN $doc IN r.documents THEN r.documents ELSE r.documents + $doc END"
        )
        doc = evidence.get("document_name", "") if evidence else ""
        with self.driver.session() as session:
            session.run(query, source_id=source_id, target_id=target_id, weight=weight, evidence=evidence, doc=doc)

    def get_full_graph(self) -> Dict[str, Any]:
        nodes_query = "MATCH (n:Entity) RETURN n.id AS id, n.label AS label, n.type AS type"
        edges_query = (
            "MATCH (a:Entity)-[r:CO_OCCURRED_IN]->(b:Entity) "
            "WHERE a.id < b.id "
            "RETURN a.id AS source, b.id AS target, r.weight AS weight, "
            "size(r.evidence) AS evidence_count, r.documents AS documents"
        )
        with self.driver.session() as session:
            node_records = session.run(nodes_query).data()
            edge_records = session.run(edges_query).data()

        return {
            "nodes": node_records,
            "edges": edge_records,
            "total_nodes": len(node_records),
            "total_edges": len(edge_records)
        }

    def get_ego_graph(self, center_node: str, radius: int = 1) -> Dict[str, Any]:
        query = (
            "MATCH (center:Entity {id: $center}) "
            f"CALL apoc.path.subgraphAll(center, {{maxLevel: {radius}}}) "
            "YIELD nodes, relationships "
            "RETURN nodes, relationships"
        )
        # Fallback cypher if APOC is not installed
        simple_query = (
            "MATCH (center:Entity {id: $center})-[r:CO_OCCURRED_IN]-(neighbor:Entity) "
            "RETURN center, r, neighbor"
        )
        with self.driver.session() as session:
            try:
                results = session.run(simple_query, center=center_node).data()
            except Exception:
                return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}

        nodes_dict = {}
        edges = []
        for row in results:
            c = row["center"]
            n = row["neighbor"]
            r = row["r"]
            nodes_dict[c["id"]] = {"id": c["id"], "label": c.get("label", c["id"]), "type": c.get("type", "UNKNOWN")}
            nodes_dict[n["id"]] = {"id": n["id"], "label": n.get("label", n["id"]), "type": n.get("type", "UNKNOWN")}
            edges.append({
                "source": c["id"],
                "target": n["id"],
                "weight": r.get("weight", 1.0),
                "evidence_count": len(r.get("evidence", [])),
                "documents": r.get("documents", [])
            })

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges)
        }

    def get_subgraph_by_nodes(self, node_ids: List[str], expand_neighbors: bool = True) -> Dict[str, Any]:
        # Simple sub-graph fetch
        query = (
            "MATCH (a:Entity)-[r:CO_OCCURRED_IN]-(b:Entity) "
            "WHERE a.id IN $node_ids "
            "RETURN a, r, b"
        )
        with self.driver.session() as session:
            results = session.run(query, node_ids=node_ids).data()

        nodes_dict = {}
        edges = []
        for row in results:
            a = row["a"]
            b = row["b"]
            r = row["r"]
            nodes_dict[a["id"]] = {"id": a["id"], "label": a.get("label", a["id"]), "type": a.get("type", "UNKNOWN")}
            nodes_dict[b["id"]] = {"id": b["id"], "label": b.get("label", b["id"]), "type": b.get("type", "UNKNOWN")}
            edges.append({
                "source": a["id"],
                "target": b["id"],
                "weight": r.get("weight", 1.0),
                "evidence_count": len(r.get("evidence", [])),
                "documents": r.get("documents", [])
            })

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges)
        }

    def get_edge_evidence(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        query = (
            "MATCH (a:Entity {id: $source})-[r:CO_OCCURRED_IN]-(b:Entity {id: $target}) "
            "RETURN r.evidence AS evidence"
        )
        with self.driver.session() as session:
            result = session.run(query, source=source_id, target=target_id).single()
            if result and result["evidence"]:
                return result["evidence"]
        return []

    def clear(self):
        with self.driver.session() as session:
            session.run("MATCH (n:Entity) DETACH DELETE n")
