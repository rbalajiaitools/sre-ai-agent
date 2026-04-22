"""Action models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from shared.database import Base


class ActionType(str, enum.Enum):
    """Action type enum."""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    CREATE_PR = "create_pr"
    RUN_SCRIPT = "run_script"
    MANUAL = "manual"


class ActionStatus(str, enum.Enum):
    """Action status enum."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Action(Base):
    """Action model for remediation actions."""
    
    __tablename__ = "actions"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("shared.investigations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Action details
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Status
    status: Mapped[ActionStatus] = mapped_column(
        SQLEnum(ActionStatus),
        nullable=False,
        default=ActionStatus.PENDING_APPROVAL
    )
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(default=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    investigation: Mapped[Optional["Investigation"]] = relationship()
    executions: Mapped[list["ActionExecution"]] = relationship(
        back_populates="action",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Action(id={self.id}, type={self.action_type}, status={self.status})>"


class ActionExecution(Base):
    """Action execution model."""
    
    __tablename__ = "action_executions"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    action_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shared.actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Execution details
    executor: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    action: Mapped["Action"] = relationship(back_populates="executions")
    
    def __repr__(self) -> str:
        return f"<ActionExecution(id={self.id}, status={self.status})>"
