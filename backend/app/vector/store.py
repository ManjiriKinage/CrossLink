import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger("cold_case.vector")

class VectorStore:
    """
    Manages vector embeddings and ChromaDB persistent storage for semantic search.
    """

    def __init__(self):
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.collection = self.client.get_or_create_collection(
            name="case_evidence",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Embeds chunks and inserts into ChromaDB with case_id in metadata.
        """
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
        
        ids = [
            f"chunk_case{int(c.get('case_id') or 0)}_{c['document_name']}_{c['chunk_id']}"
            for c in chunks
        ]
        metadatas = [
            {
                "case_id": int(c.get("case_id") or 0),
                "document_name": c["document_name"],
                "chunk_id": c["chunk_id"],
                "start_char": c.get("start_char", 0),
                "end_char": c.get("end_char", 0)
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 5, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search across document chunks with optional case_id filtering.
        """
        query_embedding = self.model.encode([query], convert_to_numpy=True).tolist()
        
        query_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": min(top_k * 2, max(1, self.collection.count()))
        }
        if case_id is not None and case_id > 0:
            query_kwargs["where"] = {"case_id": int(case_id)}

        try:
            results = self.collection.query(**query_kwargs)
        except Exception:
            # Fallback without where clause if metadata filter encounters issue
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k * 2, max(1, self.collection.count()))
            )

        hits = []
        if not results or not results["documents"] or not results["documents"][0]:
            return hits

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

        for doc_text, meta, dist in zip(docs, metas, distances):
            hit_case_id = meta.get("case_id")
            # If case_id filter specified, enforce it
            if case_id is not None and case_id > 0 and hit_case_id is not None:
                if int(hit_case_id) != int(case_id):
                    continue
            similarity = round(max(0.0, 1.0 - float(dist)), 4)
            hits.append({
                "case_id": hit_case_id,
                "document_name": meta.get("document_name", "unknown"),
                "chunk_id": meta.get("chunk_id", 0),
                "text": doc_text,
                "score": similarity
            })

        return hits[:top_k]

    def delete_document(self, document_name: str):
        """
        Deletes all chunks belonging to the specified document from ChromaDB.
        """
        try:
            self.collection.delete(where={"document_name": document_name})
            logger.info(f"Deleted vector chunks for document: {document_name}")
        except Exception as e:
            logger.warning(f"Error deleting chunks for {document_name} from ChromaDB: {e}")

    def clear(self):
        try:
            self.client.delete_collection("case_evidence")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name="case_evidence",
            metadata={"hnsw:space": "cosine"}
        )

_vector_store = None

def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
