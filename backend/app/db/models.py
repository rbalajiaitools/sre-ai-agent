"""Database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Tenant(Base):
    """Tenant model."""
    
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integrations: Mapped[list["Integration"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    chat_threads: Mapped[list["ChatThread"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class Integration(Base):
    """Integration model for ServiceNow, AWS, Azure, GCP, etc."""
    
    __tablename__ = "integrations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # User-friendly name
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # servicenow, aws, azure, gcp
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Encrypted credentials
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="integrations")


class Incident(Base):
    """Incident model - stores incidents from ServiceNow."""
    
    __tablename__ = "incidents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(36), ForeignKey("integrations.id"), nullable=False)
    
    # ServiceNow fields
    sys_id: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cmdb_ci: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assignment_group: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Investigation tracking
    investigation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Metadata
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="incidents")
    integration: Mapped["Integration"] = relationship()


class Investigation(Base):
    """Investigation model - stores RCA investigations."""
    
    __tablename__ = "investigations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    incident_number: Mapped[str] = mapped_column(String(50), nullable=False)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Investigation status
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # started, analyzing, completed, failed
    
    # Results
    selected_agents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    agent_results: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    rca: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resolution: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Approval
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="investigations")


class ChatThread(Base):
    """Chat thread model."""
    
    __tablename__ = "chat_threads"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Context (service, incident, etc.)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Investigation link
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    incident_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="chat_threads")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model."""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_threads.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), default="text")  # text, investigation_start, rca_result
    message_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thread: Mapped["ChatThread"] = relationship(back_populates="messages")
