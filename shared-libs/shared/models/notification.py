"""Notification model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from shared.database import Base


class NotificationChannel(str, enum.Enum):
    """Notification channel enum."""
    SLACK = "slack"
    EMAIL = "email"
    TEAMS = "teams"
    JIRA = "jira"
    SERVICENOW = "servicenow"
    WEBHOOK = "webhook"


class NotificationStatus(str, enum.Enum):
    """Notification status enum."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class Notification(Base):
    """Notification model."""
    
    __tablename__ = "notifications"
    __table_args__ = {"schema": "shared"}
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Channel
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel),
        nullable=False,
        index=True
    )
    
    # Recipient
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Context
    context_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    context_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Status
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING
    )
    
    # Retry
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
    
    # Result
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, channel={self.channel}, status={self.status})>"
