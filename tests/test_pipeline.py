import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.pipeline.cleaner import clean_text
from app.pipeline.chunker import create_chunks
from app.pipeline.ner import extract_entities
from app.pipeline.canonicalizer import canonicalize_entity
from app.pipeline.cooccurrence import extract_cooccurrences
from app.db.database import SessionLocal, init_db
from app.db.models import DocumentModel
from app.pipeline.ingest import ingest_document
from app.search.engine import get_search_engine
from app.graph import get_graph_store

def test_cleaner():
    raw = "John   Mehta\n\n\nvisited the   warehouse..."
    cleaned = clean_text(raw)
    assert "John Mehta" in cleaned
    assert "visited the warehouse..." in cleaned
    print("[PASS] test_cleaner passed")

def test_chunker():
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. Sentence six."
    chunks = create_chunks(text, chunk_size=40, overlap=10)
    assert len(chunks) > 1
    assert "chunk_index" in chunks[0]
    assert "text" in chunks[0]
    print(f"[PASS] test_chunker passed ({len(chunks)} chunks created)")

def test_ner_and_canonicalization():
    text = "John Mehta met Sarah Rao at the Downtown Warehouse in Mumbai in June 1995."
    entities = extract_entities(text)
    names = [e["canonical_name"] for e in entities]
    print(f"Extracted entities: {names}")
    assert "John Mehta" in names
    assert "Sarah Rao" in names
    assert "Downtown Warehouse" in names
    print("[PASS] test_ner_and_canonicalization passed")

def test_cooccurrence():
    text = "John Mehta met Sarah Rao at the Downtown Warehouse."
    entities = [
        {"name": "John Mehta", "canonical_name": "John Mehta", "type": "PERSON"},
        {"name": "Sarah Rao", "canonical_name": "Sarah Rao", "type": "PERSON"},
        {"name": "Downtown Warehouse", "canonical_name": "Downtown Warehouse", "type": "LOCATION"}
    ]
    cooccurrences = extract_cooccurrences(
        chunk_id=1,
        document_name="test_doc.txt",
        chunk_text=text,
        entities=entities
    )
    assert len(cooccurrences) == 3
    # Same sentence should give weight 2.0
    for c in cooccurrences:
        assert c["weight"] == 2.0
        assert "John Mehta met Sarah Rao" in c["snippet_text"]
    print("[PASS] test_cooccurrence passed")

def test_end_to_end_ingest_and_search():
    init_db()
    db = SessionLocal()
    try:
        from app.db.models import CaseModel
        test_case = db.query(CaseModel).filter(CaseModel.name == "Test Case").first()
        if not test_case:
            test_case = CaseModel(
                name="Test Case",
                description="Automated Test Case for Pipeline"
            )
            db.add(test_case)
            db.commit()
            db.refresh(test_case)

        sample_text = (
            "Investigators questioned Sarah Rao regarding the Downtown Warehouse in Mumbai. "
            "Sarah Rao confirmed that John Mehta visited the facility on June 14, 1995. "
            "Security logs placed John Mehta at the Downtown Warehouse shortly before the explosion."
        )
        result = ingest_document(
            db=db,
            case_id=test_case.id,
            filename="test_investigation.txt",
            raw_text=sample_text
        )
        assert result["chunk_count"] >= 1
        assert result["entity_count"] >= 2
        print(f"[PASS] Document ingested: {result['filename']}, entities: {result['entity_count']}")

        # Test Hybrid Search
        engine = get_search_engine()
        search_res = engine.search("Who was connected to the Downtown Warehouse in 1995?", case_id=test_case.id, db=db)
        print(f"Search results: {len(search_res['nodes'])} nodes, {len(search_res['edges'])} edges, {len(search_res['evidence'])} citations")
        
        node_ids = [n["id"] for n in search_res["nodes"]]
        assert "Downtown Warehouse" in node_ids
        assert len(search_res["evidence"]) > 0
        print("[PASS] test_end_to_end_ingest_and_search passed")
    finally:
        db.close()

if __name__ == "__main__":
    print("Running Cold Case IR Pipeline tests...")
    test_cleaner()
    test_chunker()
    test_ner_and_canonicalization()
    test_cooccurrence()
    test_end_to_end_ingest_and_search()
    print("\nALL PIPELINE TESTS PASSED!")
