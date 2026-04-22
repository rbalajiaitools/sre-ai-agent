"""Event schemas for Kafka."""

from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event type enum."""
    # Alert events
    ALERT_INGESTED = "alert.ingested"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    
    # Investigation events
    INVESTIGATION_REQUESTED = "investigation.requested"
    INVESTIGATION_STARTED = "investigation.started"
    INVESTIGATION_UPDATED = "investigation.updated"
    INVESTIGATION_COMPLETED = "investigation.completed"
    INVESTIGATION_FAILED = "investigation.failed"
    
    # Notification events
    NOTIFICATION_DISPATCH = "notification.dispatch"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    
    # Action events
    ACTION_REQUESTED = "action.requested"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_EXECUTED = "action.executed"


class BaseEvent(BaseModel):
    """Base event schema."""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: EventType = Field(..., description="Event type")
    tenant_id: str = Field(..., description="Tenant ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AlertEvent(BaseEvent):
    """Alert event schema."""
    
    alert_id: str = Field(..., description="Alert ID")
    severity: str = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    source: str = Field(..., description="Alert source")
    fingerprint: str = Field(..., description="Alert fingerprint")
    labels: dict[str, str] = Field(default_factory=dict, description="Alert labels")


class InvestigationEvent(BaseEvent):
    """Investigation event schema."""
    
    investigation_id: str = Field(..., description="Investigation ID")
    status: str = Field(..., description="Investigation status")
    incident_id: Optional[str] = Field(None, description="Related incident ID")
    title: str = Field(..., description="Investigation title")
    trigger_source: Optional[str] = Field(None, description="What triggered the investigation")


class NotificationEvent(BaseEvent):
    """Notification event schema."""
    
    notification_id: str = Field(..., description="Notification ID")
    channel: str = Field(..., description="Notification channel")
    recipient: str = Field(..., description="Recipient")
    subject: Optional[str] = Field(None, description="Subject")
    message: str = Field(..., description="Message content")
    context_type: Optional[str] = Field(None, description="Context type")
    context_id: Optional[str] = Field(None, description="Context ID")


class ActionEvent(BaseEvent):
    """Action event schema."""
    
    action_id: str = Field(..., description="Action ID")
    action_type: str = Field(..., description="Action type")
    status: str = Field(..., description="Action status")
    investigation_id: Optional[str] = Field(None, description="Related investigation ID")
    approved_by: Optional[str] = Field(None, description="Approver")
