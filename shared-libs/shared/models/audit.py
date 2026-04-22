"""Audit log model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class AuditLog(Base):
    """Audit log model for tracking all mutations."""
    
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_audit_actor_timestamp", "actor_id", "timestamp"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        {"schema": "shared"}
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Actor information
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Request details
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Changes
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Result
    status_code: Mapped[int] = mapped_column(nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
