import networkx as nx
from typing import Dict, Any, List, Optional
from app.graph.base import GraphStoreBase

class NetworkXGraphStore(GraphStoreBase):
    """
    Embedded graph store powered by NetworkX.
    Requires zero external services and provides instant graph operations.
    """

    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node_id: str, label: str, entity_type: str, properties: Optional[Dict[str, Any]] = None):
        props = properties or {}
        if self.graph.has_node(node_id):
            # Update attributes if needed
            self.graph.nodes[node_id].update({
                "label": label,
                "type": entity_type,
                **props
            })
        else:
            self.graph.add_node(
                node_id,
                id=node_id,
                label=label,
                type=entity_type,
                **props
            )

    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0, evidence: Optional[Dict[str, Any]] = None):
        # Guarantee node existence
        if not self.graph.has_node(source_id):
            self.add_node(source_id, source_id, "UNKNOWN")
        if not self.graph.has_node(target_id):
            self.add_node(target_id, target_id, "UNKNOWN")

        if self.graph.has_edge(source_id, target_id):
            edge_data = self.graph[source_id][target_id]
            edge_data["weight"] += weight
            if evidence:
                # Check for duplicate snippet in evidence list
                existing = [e for e in edge_data.get("evidence", []) if e.get("snippet_text") == evidence.get("snippet_text")]
                if not existing:
                    edge_data["evidence"].append(evidence)
            if evidence and "document_name" in evidence:
                edge_data["documents"].add(evidence["document_name"])
        else:
            evidence_list = [evidence] if evidence else []
            docs = {evidence["document_name"]} if evidence and "document_name" in evidence else set()
            self.graph.add_edge(
                source_id,
                target_id,
                weight=weight,
                relationship="CO_OCCURRED_IN",
                evidence=evidence_list,
                documents=docs
            )

    def _format_graph(self, g: nx.Graph) -> Dict[str, Any]:
        nodes = []
        for n, data in g.nodes(data=True):
            degree = g.degree(n)
            nodes.append({
                "id": n,
                "label": data.get("label", n),
                "type": data.get("type", "UNKNOWN"),
                "degree": degree
            })

        edges = []
        for u, v, data in g.edges(data=True):
            docs = list(data.get("documents", []))
            edges.append({
                "source": u,
                "target": v,
                "weight": round(float(data.get("weight", 1.0)), 1),
                "relationship": data.get("relationship", "CO_OCCURRED_IN"),
                "evidence_count": len(data.get("evidence", [])),
                "documents": docs
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    def get_full_graph(self) -> Dict[str, Any]:
        return self._format_graph(self.graph)

    def get_ego_graph(self, center_node: str, radius: int = 1) -> Dict[str, Any]:
        if not self.graph.has_node(center_node):
            return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
        sub = nx.ego_graph(self.graph, center_node, radius=radius)
        return self._format_graph(sub)

    def get_subgraph_by_nodes(self, node_ids: List[str], expand_neighbors: bool = True) -> Dict[str, Any]:
        valid_nodes = [n for n in node_ids if self.graph.has_node(n)]
        if not valid_nodes:
            return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}

        if expand_neighbors:
            target_nodes = set(valid_nodes)
            for n in valid_nodes:
                target_nodes.update(self.graph.neighbors(n))
            sub = self.graph.subgraph(target_nodes)
        else:
            sub = self.graph.subgraph(valid_nodes)

        return self._format_graph(sub)

    def get_edge_evidence(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        if self.graph.has_edge(source_id, target_id):
            edge_data = self.graph[source_id][target_id]
            return edge_data.get("evidence", [])
        elif self.graph.has_edge(target_id, source_id):
            edge_data = self.graph[target_id][source_id]
            return edge_data.get("evidence", [])
        return []

    def clear(self):
        self.graph.clear()
