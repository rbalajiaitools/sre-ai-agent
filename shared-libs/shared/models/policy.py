"""Policy models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Policy(Base):
    """Policy model for governance."""
    
    __tablename__ = "policies"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Policy details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Policy type: action_approval, blast_radius, risk_threshold, etc.
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Policy rules (JSON schema)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Priority (higher number = higher priority)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    
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
    tenant: Mapped["Tenant"] = relationship(back_populates="policies")
    evaluations: Mapped[list["PolicyEvaluation"]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.name}, type={self.policy_type})>"


class PolicyEvaluation(Base):
    """Policy evaluation model."""
    
    __tablename__ = "policy_evaluations"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Evaluation context
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Result
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Timestamps
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    policy: Mapped["Policy"] = relationship(back_populates="evaluations")
    
    def __repr__(self) -> str:
        return f"<PolicyEvaluation(id={self.id}, passed={self.passed})>"
