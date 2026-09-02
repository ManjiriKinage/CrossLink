import logging
from app.config import settings
from app.graph.base import GraphStoreBase
from app.graph.networkx_store import NetworkXGraphStore

logger = logging.getLogger("cold_case.graph")

_graph_instance: GraphStoreBase = None

def get_graph_store() -> GraphStoreBase:
    global _graph_instance
    if _graph_instance is None:
        if settings.NEO4J_URI:
            try:
                from app.graph.neo4j_store import Neo4jGraphStore
                store = Neo4jGraphStore(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                # Test connectivity
                store.get_full_graph()
                logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
                _graph_instance = store
            except Exception as e:
                logger.warning(f"Neo4j connection failed ({e}). Falling back to embedded NetworkXGraphStore.")
                _graph_instance = NetworkXGraphStore()
        else:
            logger.info("Using embedded NetworkXGraphStore (zero-dependency graph engine).")
            _graph_instance = NetworkXGraphStore()

    return _graph_instance
