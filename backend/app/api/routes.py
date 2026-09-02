import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import CaseModel, DocumentModel, ChunkModel, EntityModel, EvidenceModel
from app.graph import get_graph_store
from app.vector import get_vector_store
from app.search import get_search_engine
from app.pipeline.ingest import ingest_document

router = APIRouter()

# ==================== Helper Functions ====================

def get_or_create_default_case(db: Session) -> CaseModel:
    """
    Get or create the default case for backward compatibility.
    This allows old endpoints to work with the new case-based schema.
    """
    default_case = db.query(CaseModel).filter(CaseModel.name == "Default Case").first()
    if not default_case:
        default_case = CaseModel(
            name="Default Case",
            description="Default case for backward-compatible API endpoints"
        )
        db.add(default_case)
        db.commit()
        db.refresh(default_case)
    return default_case

# ==================== Pydantic Schemas ====================

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6

# ==================== Search & Graph Endpoints ====================

@router.post("/search")
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/search instead]
    Hybrid Search endpoint (uses default case for backward compatibility).
    Combines Vector Search (ChromaDB) + Graph Traversal (Neo4j/NetworkX) + Evidence Tracing.
    """
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    default_case = get_or_create_default_case(db)
    engine = get_search_engine()
    return engine.search(query=payload.query, top_k=payload.top_k, case_id=default_case.id, db=db)

@router.get("/graph")
def get_graph(db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/graph instead]
    Returns the complete knowledge graph (uses default case for backward compatibility).
    """
    default_case = get_or_create_default_case(db)
    
    # Get all entities for default case
    entities = db.query(EntityModel).filter(EntityModel.case_id == default_case.id).all()
    evidence_items = db.query(EvidenceModel).filter(EvidenceModel.case_id == default_case.id).all()
    
    # Build graph representation
    nodes = []
    edges = []
    node_ids = set()
    
    for entity in entities:
        if entity.canonical_name not in node_ids:
            nodes.append({
                "id": entity.canonical_name,
                "label": entity.canonical_name,
                "type": entity.entity_type,
                "title": f"{entity.name} ({entity.entity_type})"
            })
            node_ids.add(entity.canonical_name)
    
    for evidence in evidence_items:
        edges.append({
            "source": evidence.source_entity,
            "target": evidence.target_entity,
            "relationship_type": evidence.relationship_type,
            "weight": evidence.weight,
            "document": evidence.document_name
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }

@router.get("/evidence/{source}/{target}")
def get_evidence(source: str, target: str, db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/evidence/{source}/{target} instead]
    Retrieves all direct evidence snippets (uses default case for backward compatibility).
    """
    default_case = get_or_create_default_case(db)
    
    db_evidence = db.query(EvidenceModel).filter(
        EvidenceModel.case_id == default_case.id,
        (
            ((EvidenceModel.source_entity == source) & (EvidenceModel.target_entity == target)) |
            ((EvidenceModel.source_entity == target) & (EvidenceModel.target_entity == source))
        )
    ).all()
    
    evidence_from_graph = [
        {
            "document_name": ev.document_name,
            "chunk_id": ev.chunk_id,
            "snippet_text": ev.snippet_text,
            "weight": ev.weight
        }
        for ev in db_evidence
    ]
        
    return {
        "source": source,
        "target": target,
        "evidence_count": len(evidence_from_graph),
        "evidence": evidence_from_graph
    }

# ==================== Document Management ====================

@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/documents instead]
    Lists documents in the default case.
    """
    default_case = get_or_create_default_case(db)
    docs = db.query(DocumentModel).filter(
        DocumentModel.case_id == default_case.id
    ).order_by(DocumentModel.id.asc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "chunk_count": d.chunk_count,
            "entity_count": d.entity_count,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None
        }
        for d in docs
    ]

@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use case-scoped document endpoints instead]
    Retrieves full text and chunks of a document.
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunks = db.query(ChunkModel).filter(ChunkModel.document_id == doc_id).order_by(ChunkModel.chunk_index.asc()).all()
    evidence = db.query(EvidenceModel).filter(EvidenceModel.document_name == doc.filename).all()
    
    entities = set()
    for ev in evidence:
        entities.add(ev.source_entity)
        entities.add(ev.target_entity)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "raw_text": doc.raw_text,
        "chunk_count": doc.chunk_count,
        "entity_count": doc.entity_count,
        "unique_entities": list(entities),
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "start_char": c.start_char,
                "end_char": c.end_char
            }
            for c in chunks
        ]
    }

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/documents/{doc_id} instead]
    Removes a document from the case system.
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    filename = doc.filename
    
    # 1. Delete chunks from ChromaDB
    vector_store = get_vector_store()
    vector_store.delete_document(filename)
    
    # 2. Delete Evidence records associated with this document
    db.query(EvidenceModel).filter(EvidenceModel.document_name == filename).delete()
    
    # 3. Delete Document (cascades to chunks)
    db.delete(doc)
    db.commit()
    
    # 4. Re-synchronize GraphStore from remaining evidence
    graph_store = get_graph_store()
    graph_store.clear()
    
    remaining_evidence = db.query(EvidenceModel).all()
    for ev in remaining_evidence:
        graph_store.add_node(ev.source_entity, ev.source_entity, "UNKNOWN")
        graph_store.add_node(ev.target_entity, ev.target_entity, "UNKNOWN")
        graph_store.add_edge(
            source_id=ev.source_entity,
            target_id=ev.target_entity,
            weight=ev.weight,
            evidence={
                "document_name": ev.document_name,
                "chunk_id": ev.chunk_id,
                "snippet_text": ev.snippet_text,
                "weight": ev.weight
            }
        )
        
    # Re-apply entity types
    all_entities = db.query(EntityModel).all()
    for ent in all_entities:
        if hasattr(graph_store, 'graph') and graph_store.graph.has_node(ent.canonical_name):
            graph_store.graph.nodes[ent.canonical_name]["type"] = ent.entity_type
            
    updated_graph = graph_store.get_full_graph()
    
    return {
        "message": f"Document '{filename}' successfully removed",
        "deleted_filename": filename,
        "remaining_nodes": updated_graph["total_nodes"],
        "remaining_edges": updated_graph["total_edges"]
    }

@router.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use /cases/{case_id}/documents instead]
    Uploads and processes documents through the IR pipeline (uses default case).
    """
    default_case = get_or_create_default_case(db)
    
    results = []
    for file in files:
        content_bytes = await file.read()
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="ignore")
            
        result = ingest_document(
            db=db,
            case_id=default_case.id,
            filename=file.filename,
            raw_text=text
        )
        results.append(result)

    return {
        "message": f"Successfully processed {len(results)} document(s)",
        "documents": results
    }

@router.post("/demo/load")
def load_demo_dataset(db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use case-scoped document endpoints instead]
    Preloads demo documents into the default case.
    """
    default_case = get_or_create_default_case(db)
    
    demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo_docs"
    if not demo_dir.exists():
        raise HTTPException(status_code=404, detail=f"Demo folder not found at {demo_dir}")

    files = sorted(list(demo_dir.glob("*.txt")))
    if not files:
        raise HTTPException(status_code=404, detail="No demo files found in directory")

    processed = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            text = fp.read()
        res = ingest_document(
            db=db,
            case_id=default_case.id,
            filename=f.name,
            raw_text=text
        )
        processed.append(res)

    graph_store = get_graph_store()
    full_graph = graph_store.get_full_graph()

    return {
        "message": f"Loaded {len(processed)} demo case documents",
        "processed_documents": len(processed),
        "total_nodes": full_graph["total_nodes"],
        "total_edges": full_graph["total_edges"],
        "documents": processed
    }

@router.post("/demo/reset")
def reset_system(db: Session = Depends(get_db)):
    """
    [DEPRECATED: Use case deletion instead]
    Wipes all data from the default case.
    """
    default_case = get_or_create_default_case(db)
    
    # Delete all documents in the default case (cascades to chunks and evidence)
    db.query(DocumentModel).filter(DocumentModel.case_id == default_case.id).delete()
    db.query(EntityModel).filter(EntityModel.case_id == default_case.id).delete()
    db.query(EvidenceModel).filter(EvidenceModel.case_id == default_case.id).delete()
    db.commit()
    
    # Clear graph store
    graph_store = get_graph_store()
    graph_store.clear()
    
    return {
        "message": "System reset successfully",
        "nodes": 0,
        "edges": 0
    }
