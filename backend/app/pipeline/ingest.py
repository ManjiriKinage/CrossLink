import hashlib
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models import DocumentModel, ChunkModel, EntityModel, EvidenceModel
from app.pipeline.cleaner import clean_text
from app.pipeline.chunker import create_chunks
from app.pipeline.ner import extract_entities
from app.pipeline.cooccurrence import extract_cooccurrences
from app.graph import get_graph_store
from app.vector import get_vector_store

logger = logging.getLogger("cold_case.ingest")

def ingest_document(
    db: Session,
    case_id: int,
    filename: str,
    raw_text: str,
    graph_store=None,
    vector_store=None
) -> Dict[str, Any]:
    """
    Ingests a single document through the end-to-end IR pipeline:
    1. Cleaning
    2. Chunking
    3. NER & Canonicalization
    4. Database Storage (Docs, Chunks, Entities, Evidence) - with case isolation
    5. Knowledge Graph Population (Nodes & Edges)
    6. Vector Store Indexing (SentenceTransformers + ChromaDB)
    
    Args:
        db: Database session
        case_id: Investigation case ID - ensures data isolation
        filename: Document filename
        raw_text: Raw document text
        graph_store: Graph storage backend (optional)
        vector_store: Vector store backend (optional)
    """
    if graph_store is None:
        graph_store = get_graph_store()
    if vector_store is None:
        vector_store = get_vector_store()

    # 1. Clean
    cleaned = clean_text(raw_text)
    content_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    # Check if document already exists in this case; if so, delete old one to re-index
    existing_doc = db.query(DocumentModel).filter(
        DocumentModel.case_id == case_id,
        DocumentModel.filename == filename
    ).first()
    if existing_doc:
        db.delete(existing_doc)
        db.commit()

    # 2. Save Document record with case_id
    doc_record = DocumentModel(
        case_id=case_id,
        filename=filename,
        content_hash=content_hash,
        raw_text=cleaned,
        chunk_count=0,
        entity_count=0
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 3. Chunk
    raw_chunks = create_chunks(cleaned, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
    chunk_records = []
    vector_chunks = []
    all_doc_entities = []
    created_entities_in_session = set()  # Track entities created in this ingestion

    for rc in raw_chunks:
        chunk_rec = ChunkModel(
            case_id=case_id,
            document_id=doc_record.id,
            chunk_index=rc["chunk_index"],
            text=rc["text"],
            start_char=rc["start_char"],
            end_char=rc["end_char"]
        )
        db.add(chunk_rec)
        db.commit()
        db.refresh(chunk_rec)
        chunk_records.append(chunk_rec)

        # 4. NER per chunk
        chunk_entities = extract_entities(rc["text"])
        all_doc_entities.extend(chunk_entities)

        # Add to Graph Store nodes
        for ent in chunk_entities:
            graph_store.add_node(
                node_id=ent["canonical_name"],
                label=ent["canonical_name"],
                entity_type=ent["type"]
            )
            # Record entity in DB if not yet recorded for this case
            canonical_name = ent["canonical_name"]
            if canonical_name not in created_entities_in_session:
                existing_ent = db.query(EntityModel).filter(
                    EntityModel.case_id == case_id,
                    EntityModel.canonical_name == canonical_name
                ).first()
                if not existing_ent:
                    new_ent = EntityModel(
                        case_id=case_id,
                        name=ent["name"],
                        canonical_name=canonical_name,
                        entity_type=ent["type"]
                    )
                    db.add(new_ent)
                    created_entities_in_session.add(canonical_name)

        # 5. Co-occurrence & Relationships
        cooccurrences = extract_cooccurrences(
            chunk_id=chunk_rec.id,
            document_name=filename,
            chunk_text=rc["text"],
            entities=chunk_entities
        )

        for cooc in cooccurrences:
            # Add to database evidence with case_id
            ev_rec = EvidenceModel(
                case_id=case_id,
                chunk_id=chunk_rec.id,
                document_name=filename,
                source_entity=cooc["source_entity"],
                target_entity=cooc["target_entity"],
                relationship_type=cooc["relationship_type"],
                snippet_text=cooc["snippet_text"],
                weight=cooc["weight"]
            )
            db.add(ev_rec)

            # Add to Graph Store edges
            graph_store.add_edge(
                source_id=cooc["source_entity"],
                target_id=cooc["target_entity"],
                weight=cooc["weight"],
                evidence={
                    "document_name": filename,
                    "chunk_id": chunk_rec.id,
                    "snippet_text": cooc["snippet_text"],
                    "weight": cooc["weight"]
                }
            )

        # Prepare for vector indexing
        vector_chunks.append({
            "chunk_id": chunk_rec.id,
            "case_id": case_id,
            "document_name": filename,
            "text": rc["text"],
            "start_char": rc["start_char"],
            "end_char": rc["end_char"]
        })

    db.commit()

    # 6. Index into Vector Store
    vector_store.add_chunks(vector_chunks)

    # Deduplicate entities for document summary count
    unique_entities = {e["canonical_name"] for e in all_doc_entities}
    doc_record.chunk_count = len(chunk_records)
    doc_record.entity_count = len(unique_entities)
    db.commit()

    logger.info(f"Ingested {filename}: {len(chunk_records)} chunks, {len(unique_entities)} unique entities")

    return {
        "filename": filename,
        "chunk_count": len(chunk_records),
        "entity_count": len(unique_entities),
        "unique_entities": list(unique_entities)
    }
