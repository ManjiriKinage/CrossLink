import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))

from app.db.database import SessionLocal, init_db
from app.db.models import CaseModel, DocumentModel, ChunkModel, EntityModel, EvidenceModel
from app.pipeline.ingest import ingest_document
from app.graph import get_graph_store
from app.vector import get_vector_store

def preload():
    print("Initializing Cold Case IR database...")
    init_db()
    db = SessionLocal()

    # Create or get default demo case
    demo_case = db.query(CaseModel).filter(CaseModel.name == "Demo Case").first()
    if not demo_case:
        demo_case = CaseModel(
            name="Demo Case",
            description="Default demonstration case with sample investigative documents"
        )
        db.add(demo_case)
        db.commit()
        db.refresh(demo_case)
        print(f"Created new Demo Case (ID: {demo_case.id})")
    else:
        print(f"Using existing Demo Case (ID: {demo_case.id})")

    demo_dir = Path(__file__).resolve().parent.parent / "data" / "demo_docs"
    files = sorted(list(demo_dir.glob("*.txt")))
    print(f"Found {len(files)} case documents in {demo_dir}\n")

    total_chunks = 0
    total_entities = set()

    for idx, f in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Processing {f.name}...")
        with open(f, "r", encoding="utf-8") as fp:
            text = fp.read()
        res = ingest_document(
            db=db,
            case_id=demo_case.id,
            filename=f.name,
            raw_text=text
        )
        total_chunks += res["chunk_count"]
        total_entities.update(res["unique_entities"])
        print(f"     -> {res['chunk_count']} chunks | {res['entity_count']} entities: {', '.join(res['unique_entities'][:4])}...")

    graph = get_graph_store().get_full_graph()
    print("\n" + "="*50)
    print("[SUCCESS] COLD CASE CASE FILES INDEXED SUCCESSFULLY!")
    print(f"Case:                   {demo_case.name}")
    print(f"Total Documents:        {len(files)}")
    print(f"Total Text Chunks:      {total_chunks}")
    print(f"Total Discovered Nodes: {graph['total_nodes']}")
    print(f"Total Relationships:    {graph['total_edges']}")
    print("="*50 + "\n")

    db.close()

if __name__ == "__main__":
    preload()
