"""Connector models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Connector(Base):
    """Connector model for integrations."""
    
    __tablename__ = "connectors"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Connector details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Configuration (encrypted credentials)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    health_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="connectors")
    executions: Mapped[list["ConnectorExecution"]] = relationship(
        back_populates="connector",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Connector(id={self.id}, name={self.name}, type={self.connector_type})>"


class ConnectorExecution(Base):
    """Connector execution model."""
    
    __tablename__ = "connector_executions"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connector_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.connectors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Execution details
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Result
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance
    duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    
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
    connector: Mapped["Connector"] = relationship(back_populates="executions")
    
    def __repr__(self) -> str:
        return f"<ConnectorExecution(id={self.id}, method={self.method}, status={self.status})>"
