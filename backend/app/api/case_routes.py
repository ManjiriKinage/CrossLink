from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import CaseModel, DocumentModel, ChunkModel, EntityModel, EvidenceModel
from app.pipeline.ingest import ingest_document
from app.graph import get_graph_store
from app.vector import get_vector_store

router = APIRouter(prefix="/cases", tags=["cases"])

# ==================== Pydantic Schemas ====================

class CaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    document_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: str
    chunk_count: int
    entity_count: int

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6

class EvidenceItem(BaseModel):
    document_name: str
    chunk_id: int
    snippet_text: str
    weight: float

# ==================== Case Management Endpoints ====================

@router.post("", response_model=CaseResponse)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    """Create a new investigation case"""
    new_case = CaseModel(
        name=payload.name,
        description=payload.description
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    return {
        "id": new_case.id,
        "name": new_case.name,
        "description": new_case.description,
        "created_at": new_case.created_at.isoformat(),
        "updated_at": new_case.updated_at.isoformat(),
        "document_count": 0,
        "entity_count": 0,
        "relationship_count": 0
    }

@router.get("", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    """List all investigation cases with metadata"""
    cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).all()
    
    results = []
    for case in cases:
        doc_count = db.query(DocumentModel).filter(DocumentModel.case_id == case.id).count()
        entity_count = db.query(EntityModel).filter(EntityModel.case_id == case.id).count()
        evidence_count = db.query(EvidenceModel).filter(EvidenceModel.case_id == case.id).count()
        
        results.append({
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "document_count": doc_count,
            "entity_count": entity_count,
            "relationship_count": evidence_count
        })
    
    return results

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get a specific case with metadata"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    doc_count = db.query(DocumentModel).filter(DocumentModel.case_id == case.id).count()
    entity_count = db.query(EntityModel).filter(EntityModel.case_id == case.id).count()
    evidence_count = db.query(EvidenceModel).filter(EvidenceModel.case_id == case.id).count()
    
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "document_count": doc_count,
        "entity_count": entity_count,
        "relationship_count": evidence_count
    }

@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db)):
    """Update case metadata"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if payload.name is not None:
        case.name = payload.name
    if payload.description is not None:
        case.description = payload.description
    
    db.commit()
    db.refresh(case)
    
    doc_count = db.query(DocumentModel).filter(DocumentModel.case_id == case.id).count()
    entity_count = db.query(EntityModel).filter(EntityModel.case_id == case.id).count()
    evidence_count = db.query(EvidenceModel).filter(EvidenceModel.case_id == case.id).count()
    
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "document_count": doc_count,
        "entity_count": entity_count,
        "relationship_count": evidence_count
    }

@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Delete an entire case and all associated data"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    db.delete(case)
    db.commit()
    
    return {"message": f"Case {case_id} deleted successfully"}

# ==================== Document Management ====================

def decode_uploaded_bytes(content: bytes) -> str:
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1", "utf-16"]:
        try:
            decoded = content.decode(enc)
            if decoded.strip():
                return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="ignore")

@router.post("/{case_id}/documents")
async def upload_documents(
    case_id: int,
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    """Upload single or multiple documents to a case and ingest into IR pipeline"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
    
    if not upload_list:
        raise HTTPException(status_code=400, detail="No files provided for upload")
    
    ingested = []
    errors = []

    for f in upload_list:
        try:
            content = await f.read()
            text_content = decode_uploaded_bytes(content)
            if not text_content.strip():
                errors.append(f"File '{f.filename}' is empty")
                continue

            result = ingest_document(
                db=db,
                case_id=case_id,
                filename=f.filename,
                raw_text=text_content
            )

            doc = db.query(DocumentModel).filter(
                DocumentModel.case_id == case_id,
                DocumentModel.filename == f.filename
            ).first()

            if doc:
                ingested.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else "",
                    "chunk_count": doc.chunk_count,
                    "entity_count": doc.entity_count
                })
        except Exception as e:
            errors.append(f"Failed '{f.filename}': {str(e)}")

    if not ingested and errors:
        raise HTTPException(status_code=500, detail="; ".join(errors))

    first = ingested[0] if ingested else {}
    return {
        "message": f"Successfully processed {len(ingested)} document(s)",
        "documents": ingested,
        "errors": errors if errors else None,
        "id": first.get("id"),
        "filename": first.get("filename", ""),
        "uploaded_at": first.get("uploaded_at", ""),
        "chunk_count": first.get("chunk_count", 0),
        "entity_count": first.get("entity_count", 0)
    }

@router.get("/{case_id}/documents", response_model=List[DocumentResponse])
def list_case_documents(case_id: int, db: Session = Depends(get_db)):
    """List all documents in a case"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(DocumentModel).filter(
        DocumentModel.case_id == case_id
    ).order_by(DocumentModel.uploaded_at.desc()).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "chunk_count": doc.chunk_count,
            "entity_count": doc.entity_count
        }
        for doc in docs
    ]

@router.delete("/{case_id}/documents/{doc_id}")
def delete_document(case_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Remove a document from a case"""
    doc = db.query(DocumentModel).filter(
        DocumentModel.id == doc_id,
        DocumentModel.case_id == case_id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in this case")
    
    db.delete(doc)
    db.commit()
    
    return {"message": f"Document {doc_id} removed from case {case_id}"}

# ==================== Case-Scoped Search & Graph ====================

@router.post("/{case_id}/search")
def search_case(case_id: int, payload: SearchRequest, db: Session = Depends(get_db)):
    """
    Search within a specific case.
    Combines vector search + graph traversal + evidence retrieval.
    Results are scoped to the case only.
    """
    # Verify case exists
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    from app.search import get_search_engine
    engine = get_search_engine()
    
    # Perform search with case_id filter
    results = engine.search(
        query=payload.query,
        top_k=payload.top_k,
        case_id=case_id,
        db=db
    )
    
    return results

@router.get("/{case_id}/graph")
def get_case_graph(case_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the complete knowledge graph for a specific case.
    Shows all entities and relationships discovered in that case.
    """
    # Verify case exists
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    store = get_graph_store()
    
    # Get all entities for this case
    entities = db.query(EntityModel).filter(EntityModel.case_id == case_id).all()
    
    # Get all evidence/relationships for this case
    evidence_items = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id).all()
    
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
        "case_id": case_id,
        "case_name": case.name,
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }

@router.get("/{case_id}/evidence/{source}/{target}")
def get_case_evidence(
    case_id: int,
    source: str,
    target: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all evidence supporting a relationship within a specific case.
    Shows all document snippets that mention both entities in connection.
    """
    # Verify case exists
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Query evidence scoped to this case
    evidence_items = db.query(EvidenceModel).filter(
        EvidenceModel.case_id == case_id,
        (
            ((EvidenceModel.source_entity == source) & (EvidenceModel.target_entity == target)) |
            ((EvidenceModel.source_entity == target) & (EvidenceModel.target_entity == source))
        )
    ).all()
    
    return {
        "case_id": case_id,
        "source": source,
        "target": target,
        "evidence_count": len(evidence_items),
        "evidence": [
            {
                "document_name": ev.document_name,
                "chunk_id": ev.chunk_id,
                "snippet_text": ev.snippet_text,
                "weight": ev.weight,
                "relationship_type": ev.relationship_type
            }
            for ev in evidence_items
        ]
    }

@router.get("/{case_id}/quick-clues", response_model=List[str])
def get_case_quick_clues(case_id: int, db: Session = Depends(get_db)):
    """Generate dynamic investigative clue questions tailored specifically to this case"""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    entities = db.query(EntityModel).filter(EntityModel.case_id == case_id).all()
    evidence_items = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id).order_by(EvidenceModel.weight.desc()).all()
    docs = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    
    persons = [e.canonical_name for e in entities if e.entity_type == "PERSON"]
    locations = [e.canonical_name for e in entities if e.entity_type == "LOCATION"]
    orgs = [e.canonical_name for e in entities if e.entity_type == "ORGANIZATION"]
    dates = [e.canonical_name for e in entities if e.entity_type == "DATE"]
    
    clues = []
    
    # 1. Top connected pair
    if evidence_items:
        top_ev = evidence_items[0]
        clues.append(f"What connects {top_ev.source_entity} and {top_ev.target_entity}?")
    
    # 2. Location inquiry
    if locations:
        date_str = f" in {dates[0]}" if dates else ""
        clues.append(f"Who was connected to {locations[0]}{date_str}?")
    
    # 3. Key Person inquiry
    if persons:
        clues.append(f"What was the role of {persons[0]}?")
    
    # 4. Organization inquiry
    if orgs:
        clues.append(f"Show connections for {orgs[0]}")
    
    # 5. Second pair or second person/location
    if len(evidence_items) > 1 and len(clues) < 5:
        second_ev = evidence_items[1]
        pair_q = f"What links {second_ev.source_entity} to {second_ev.target_entity}?"
        if pair_q not in clues and second_ev.source_entity != second_ev.target_entity:
            clues.append(pair_q)
            
    if len(persons) > 1 and len(clues) < 5:
        p2_q = f"What evidence mentions {persons[1]}?"
        if p2_q not in clues:
            clues.append(p2_q)
            
    if len(docs) > 0 and len(clues) < 5:
        doc_name = docs[0].filename.replace(".txt", "").replace("_", " ").title()
        clues.append(f"What evidence is detailed in {doc_name}?")
        
    if not clues:
        clues = [
            f"Who is involved in {case.name}?",
            "What incident occurred in this case?",
            "What evidence has been discovered?"
        ]
        
    return clues[:6]

