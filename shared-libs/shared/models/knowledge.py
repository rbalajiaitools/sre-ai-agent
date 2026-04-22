"""Knowledge base models with pgvector support."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from shared.database import Base


class KnowledgeBase(Base):
    """Knowledge base model."""
    
    __tablename__ = "knowledge_base"
    __table_args__ = (
        Index("idx_knowledge_tenant_type", "tenant_id", "knowledge_type"),
        Index("idx_knowledge_service", "service_name"),
        {"schema": "shared"}
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Type: runbook, architecture, code_snippet, investigation, postmortem
    knowledge_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Tags
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Related entities
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    incident_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # External link
    external_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, title={self.title}, type={self.knowledge_type})>"


class KnowledgeEmbedding(Base):
    """Knowledge embedding model for RAG with pgvector."""
    
    __tablename__ = "knowledge_embeddings"
    __table_args__ = (
        Index(
            "idx_knowledge_embedding_vector",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
        {"schema": "shared"}
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True
    )
    
    # Chunk information
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Embedding vector (1536 dimensions for OpenAI ada-002)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeEmbedding(id={self.id}, knowledge_id={self.knowledge_id}, chunk={self.chunk_index})>"
