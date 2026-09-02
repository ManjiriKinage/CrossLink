import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    documents = relationship("DocumentModel", back_populates="case", cascade="all, delete-orphan")
    entities = relationship("EntityModel", back_populates="case", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceModel", back_populates="case", cascade="all, delete-orphan")


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint('case_id', 'filename', name='uq_case_document'),)

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False)
    raw_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    entity_count = Column(Integer, default=0)

    case = relationship("CaseModel", back_populates="documents")
    chunks = relationship("ChunkModel", back_populates="document", cascade="all, delete-orphan")


class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    case = relationship("CaseModel")
    document = relationship("DocumentModel", back_populates="chunks")
    evidence_items = relationship("EvidenceModel", back_populates="chunk", cascade="all, delete-orphan")


class EntityModel(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint('case_id', 'canonical_name', name='uq_case_entity'),)

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    canonical_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)  # PERSON, LOCATION, ORGANIZATION, DATE

    case = relationship("CaseModel", back_populates="entities")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    document_name = Column(String(255), index=True, nullable=False)
    source_entity = Column(String(255), index=True, nullable=False)
    target_entity = Column(String(255), index=True, nullable=False)
    relationship_type = Column(String(64), default="CO_OCCURRED_IN")
    snippet_text = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("CaseModel", back_populates="evidence_items")
    chunk = relationship("ChunkModel", back_populates="evidence_items")
