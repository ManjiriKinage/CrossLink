from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class GraphStoreBase(ABC):
    """
    Abstract interface for Cold Case graph storage and retrieval.
    Can be backed by embedded NetworkX or Neo4j.
    """

    @abstractmethod
    def add_node(self, node_id: str, label: str, entity_type: str, properties: Optional[Dict[str, Any]] = None):
        """Add or update an entity node."""
        pass

    @abstractmethod
    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0, evidence: Optional[Dict[str, Any]] = None):
        """Add or increment a relationship edge with attached evidence."""
        pass

    @abstractmethod
    def get_full_graph(self) -> Dict[str, Any]:
        """Returns all nodes and edges formatted for the UI graph."""
        pass

    @abstractmethod
    def get_ego_graph(self, center_node: str, radius: int = 1) -> Dict[str, Any]:
        """Returns a subgraph centered on a specific entity within N hops."""
        pass

    @abstractmethod
    def get_subgraph_by_nodes(self, node_ids: List[str], expand_neighbors: bool = True) -> Dict[str, Any]:
        """Returns subgraph containing given nodes and their direct connections."""
        pass

    @abstractmethod
    def get_edge_evidence(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """Returns all evidence items linking two entities."""
        pass

    @abstractmethod
    def clear(self):
        """Wipes the graph."""
        pass
