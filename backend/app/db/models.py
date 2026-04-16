"""Database models."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Tenant(Base):
    """Tenant model."""
    
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
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
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
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
    related_knowledge: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Related knowledge base entries
    
    # Approval
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    thread: Mapped["ChatThread"] = relationship(back_populates="messages")


class KnowledgeBase(Base):
    """Knowledge Base model - stores runbooks, architecture docs, code snippets, investigations."""
    
    __tablename__ = "knowledge_base"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type: runbook, architecture, code_snippet, investigation, external_link
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Markdown content
    
    # External link (for GitHub, Confluence, etc.)
    external_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Tags for search and categorization
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Related entities
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship()


class KnowledgeUsage(Base):
    """Track when knowledge base items are used in investigations."""
    
    __tablename__ = "knowledge_usage"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_base.id"), nullable=False)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), nullable=False)
    
    # How it was used
    relevance_score: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)  # 0-100
    used_in_rca: Mapped[bool] = mapped_column(Boolean, default=False)
    used_in_resolution: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    knowledge: Mapped["KnowledgeBase"] = relationship()
    investigation: Mapped["Investigation"] = relationship()

