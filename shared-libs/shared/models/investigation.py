"""Investigation models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from shared.database import Base


class InvestigationStatus(str, enum.Enum):
    """Investigation status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConfidenceLevel(str, enum.Enum):
    """Confidence level enum."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Investigation(Base):
    """Investigation model."""
    
    __tablename__ = "investigations"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Context
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("shared.incidents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Status
    status: Mapped[InvestigationStatus] = mapped_column(
        SQLEnum(InvestigationStatus),
        nullable=False,
        default=InvestigationStatus.PENDING
    )
    
    # Results
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence_level: Mapped[Optional[ConfidenceLevel]] = mapped_column(
        SQLEnum(ConfidenceLevel),
        nullable=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="investigations")
    incident: Mapped[Optional["Incident"]] = relationship(back_populates="investigations")
    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Investigation(id={self.id}, status={self.status})>"


class Hypothesis(Base):
    """Hypothesis model."""
    
    __tablename__ = "hypotheses"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Validation
    is_validated: Mapped[bool] = mapped_column(default=False, nullable=False)
    validation_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="hypotheses")
    
    def __repr__(self) -> str:
        return f"<Hypothesis(id={self.id}, validated={self.is_validated})>"


class EvidenceItem(Base):
    """Evidence item model."""
    
    __tablename__ = "evidence_items"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Analysis
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    supports_hypothesis_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="evidence_items")
    
    def __repr__(self) -> str:
        return f"<EvidenceItem(id={self.id}, source={self.source}, type={self.evidence_type})>"
