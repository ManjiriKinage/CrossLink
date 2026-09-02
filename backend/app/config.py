import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cold Case IR Engine"
    API_V1_STR: str = "/api"
    
    # Storage settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cold_case.db'}")
    
    # Neo4j settings (optional - falls back to NetworkX embedded engine)
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # ChromaDB & Embeddings
    CHROMA_PERSIST_DIR: str = str(DATA_DIR / "chroma")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Text Chunking parameters
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # Spacy Model
    SPACY_MODEL: str = "en_core_web_sm"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
