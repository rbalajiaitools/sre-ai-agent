"""Alert and Incident models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from shared.database import Base


class AlertSeverity(str, enum.Enum):
    """Alert severity enum."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    """Alert status enum."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentState(str, enum.Enum):
    """Incident state enum."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Alert(Base):
    """Alert model."""
    
    __tablename__ = "alerts"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Source
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    severity: Mapped[AlertSeverity] = mapped_column(
        SQLEnum(AlertSeverity),
        nullable=False,
        index=True
    )
    status: Mapped[AlertStatus] = mapped_column(
        SQLEnum(AlertStatus),
        nullable=False,
        default=AlertStatus.OPEN
    )
    
    # Deduplication
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Correlation
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("shared.incidents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    labels: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    annotations: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Timestamps
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="alerts")
    incident: Mapped[Optional["Incident"]] = relationship(back_populates="alerts")
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, severity={self.severity}, status={self.status})>"


class Incident(Base):
    """Incident model."""
    
    __tablename__ = "incidents"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Identification
    number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    state: Mapped[IncidentState] = mapped_column(
        SQLEnum(IncidentState),
        nullable=False,
        default=IncidentState.NEW
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assignment_group: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Impact
    affected_services: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    affected_users_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="incidents")
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    investigations: Mapped[list["Investigation"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, number={self.number}, state={self.state})>"
