"""CRUD operations for database models."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Tenant, Integration, Incident, Investigation, ChatThread, ChatMessage
from app.db.encryption import encrypt_credentials, decrypt_credentials


# Tenant CRUD
async def get_or_create_tenant(db: AsyncSession, tenant_id: str, name: str = "Default Tenant") -> Tenant:
    """Get or create tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        name: Tenant name
        
    Returns:
        Tenant: Tenant instance
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(id=tenant_id, name=name)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
    
    return tenant


# Integration CRUD
async def create_integration(
    db: AsyncSession,
    tenant_id: str,
    name: str,
    integration_type: str,
    config: dict
) -> Integration:
    """Create integration.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        name: Integration name
        integration_type: Integration type (servicenow, aws, azure, gcp)
        config: Configuration dictionary (will be encrypted)
        
    Returns:
        Integration: Created integration
    """
    # Ensure tenant exists
    await get_or_create_tenant(db, tenant_id)
    
    # Encrypt credentials
    encrypted_config = encrypt_credentials(config)
    
    integration = Integration(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        type=integration_type,
        config={"encrypted": encrypted_config},
        is_active=True,
    )
    
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    
    return integration


async def get_integrations(
    db: AsyncSession,
    tenant_id: str,
    integration_type: Optional[str] = None
) -> List[Integration]:
    """Get integrations for tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        integration_type: Optional filter by type
        
    Returns:
        List[Integration]: List of integrations
    """
    query = select(Integration).where(Integration.tenant_id == tenant_id)
    
    if integration_type:
        query = query.where(Integration.type == integration_type)
    
    result = await db.execute(query.order_by(Integration.created_at.desc()))
    return list(result.scalars().all())


async def get_integration(db: AsyncSession, integration_id: str) -> Optional[Integration]:
    """Get integration by ID.
    
    Args:
        db: Database session
        integration_id: Integration ID
        
    Returns:
        Optional[Integration]: Integration or None
    """
    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    return result.scalar_one_or_none()


async def update_integration(
    db: AsyncSession,
    integration_id: str,
    name: Optional[str] = None,
    config: Optional[dict] = None,
    is_active: Optional[bool] = None
) -> Optional[Integration]:
    """Update integration.
    
    Args:
        db: Database session
        integration_id: Integration ID
        name: Optional new name
        config: Optional new config (will be encrypted)
        is_active: Optional active status
        
    Returns:
        Optional[Integration]: Updated integration or None
    """
    integration = await get_integration(db, integration_id)
    
    if not integration:
        return None
    
    if name is not None:
        integration.name = name
    
    if config is not None:
        encrypted_config = encrypt_credentials(config)
        integration.config = {"encrypted": encrypted_config}
    
    if is_active is not None:
        integration.is_active = is_active
    
    integration.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(integration)
    
    return integration


async def delete_integration(db: AsyncSession, integration_id: str) -> bool:
    """Delete integration.
    
    Args:
        db: Database session
        integration_id: Integration ID
        
    Returns:
        bool: True if deleted, False if not found
    """
    integration = await get_integration(db, integration_id)
    
    if not integration:
        return False
    
    await db.delete(integration)
    await db.commit()
    
    return True


def decrypt_integration_config(integration: Integration) -> dict:
    """Decrypt integration config.
    
    Args:
        integration: Integration instance
        
    Returns:
        dict: Decrypted config
    """
    if "encrypted" in integration.config:
        return decrypt_credentials(integration.config["encrypted"])
    return integration.config


# Incident CRUD
async def upsert_incident(
    db: AsyncSession,
    tenant_id: str,
    integration_id: str,
    incident_data: dict
) -> Incident:
    """Create or update incident.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        integration_id: Integration ID
        incident_data: Incident data from ServiceNow
        
    Returns:
        Incident: Created or updated incident
    """
    # Check if incident exists
    result = await db.execute(
        select(Incident).where(
            Incident.tenant_id == tenant_id,
            Incident.number == incident_data["number"]
        )
    )
    incident = result.scalar_one_or_none()
    
    # Convert datetime objects to strings for JSON storage
    raw_data_for_json = {}
    for key, value in incident_data.items():
        if isinstance(value, datetime):
            raw_data_for_json[key] = value.isoformat()
        else:
            raw_data_for_json[key] = value
    
    if incident:
        # Update existing
        incident.short_description = incident_data["short_description"]
        incident.description = incident_data.get("description")
        incident.priority = incident_data["priority"]
        incident.state = incident_data["state"]
        incident.category = incident_data.get("category")
        incident.subcategory = incident_data.get("subcategory")
        incident.cmdb_ci = incident_data.get("cmdb_ci")
        incident.assignment_group = incident_data.get("assignment_group")
        incident.assigned_to = incident_data.get("assigned_to")
        incident.updated_at = incident_data["updated_at"]
        incident.resolved_at = incident_data.get("resolved_at")
        incident.raw_data = raw_data_for_json
        incident.synced_at = datetime.utcnow()
    else:
        # Create new
        incident = Incident(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            integration_id=integration_id,
            sys_id=incident_data["sys_id"],
            number=incident_data["number"],
            short_description=incident_data["short_description"],
            description=incident_data.get("description"),
            priority=incident_data["priority"],
            state=incident_data["state"],
            category=incident_data.get("category"),
            subcategory=incident_data.get("subcategory"),
            cmdb_ci=incident_data.get("cmdb_ci"),
            assignment_group=incident_data.get("assignment_group"),
            assigned_to=incident_data.get("assigned_to"),
            opened_at=incident_data["opened_at"],
            updated_at=incident_data["updated_at"],
            resolved_at=incident_data.get("resolved_at"),
            raw_data=raw_data_for_json,
        )
        db.add(incident)
    
    await db.commit()
    await db.refresh(incident)
    
    return incident


async def get_incidents(db: AsyncSession, tenant_id: str) -> List[Incident]:
    """Get incidents for tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        
    Returns:
        List[Incident]: List of incidents
    """
    result = await db.execute(
        select(Incident)
        .where(Incident.tenant_id == tenant_id)
        .order_by(Incident.opened_at.desc())
    )
    return list(result.scalars().all())


async def get_incident_by_number(
    db: AsyncSession,
    tenant_id: str,
    incident_number: str
) -> Optional[Incident]:
    """Get incident by number.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        incident_number: Incident number
        
    Returns:
        Optional[Incident]: Incident or None
    """
    result = await db.execute(
        select(Incident).where(
            Incident.tenant_id == tenant_id,
            Incident.number == incident_number
        )
    )
    return result.scalar_one_or_none()


# Investigation CRUD
async def create_investigation(
    db: AsyncSession,
    tenant_id: str,
    incident_number: str,
    status: str = "started"
) -> Investigation:
    """Create investigation.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        incident_number: Incident number
        status: Investigation status
        
    Returns:
        Investigation: Created investigation
    """
    investigation = Investigation(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        incident_number=incident_number,
        status=status,
    )
    
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)
    
    return investigation


async def get_investigation(db: AsyncSession, investigation_id: str) -> Optional[Investigation]:
    """Get investigation by ID.
    
    Args:
        db: Database session
        investigation_id: Investigation ID
        
    Returns:
        Optional[Investigation]: Investigation or None
    """
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    return result.scalar_one_or_none()


async def update_investigation(
    db: AsyncSession,
    investigation_id: str,
    **kwargs
) -> Optional[Investigation]:
    """Update investigation.
    
    Args:
        db: Database session
        investigation_id: Investigation ID
        **kwargs: Fields to update
        
    Returns:
        Optional[Investigation]: Updated investigation or None
    """
    investigation = await get_investigation(db, investigation_id)
    
    if not investigation:
        return None
    
    for key, value in kwargs.items():
        if hasattr(investigation, key):
            setattr(investigation, key, value)
    
    await db.commit()
    await db.refresh(investigation)
    
    return investigation


# Chat CRUD
async def create_chat_thread(
    db: AsyncSession,
    tenant_id: str,
    title: str,
    context: Optional[dict] = None,
    investigation_id: Optional[str] = None,
    incident_number: Optional[str] = None
) -> ChatThread:
    """Create chat thread.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        title: Thread title
        context: Optional context (service, incident, etc.)
        investigation_id: Optional investigation ID
        incident_number: Optional incident number
        
    Returns:
        ChatThread: Created thread
    """
    thread = ChatThread(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        title=title,
        context=context,
        investigation_id=investigation_id,
        incident_number=incident_number,
    )
    
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    
    return thread


async def get_chat_threads(db: AsyncSession, tenant_id: str) -> List[ChatThread]:
    """Get chat threads for tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        
    Returns:
        List[ChatThread]: List of threads
    """
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.tenant_id == tenant_id)
        .order_by(ChatThread.last_message_at.desc())
    )
    return list(result.scalars().all())


async def delete_chat_thread(db: AsyncSession, thread_id: str, tenant_id: str) -> None:
    """Delete chat thread.
    
    Args:
        db: Database session
        thread_id: Thread ID
        tenant_id: Tenant ID (for security check)
    """
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.id == thread_id)
        .where(ChatThread.tenant_id == tenant_id)
    )
    thread = result.scalar_one_or_none()
    
    if thread:
        await db.delete(thread)
        await db.commit()


async def update_chat_thread_title(db: AsyncSession, thread_id: str, title: str) -> None:
    """Update chat thread title.
    
    Args:
        db: Database session
        thread_id: Thread ID
        title: New title
    """
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    
    if thread:
        thread.title = title
        await db.commit()


async def create_chat_message(
    db: AsyncSession,
    thread_id: str,
    role: str,
    content: str,
    message_type: str = "text",
    message_metadata: Optional[dict] = None
) -> ChatMessage:
    """Create chat message.
    
    Args:
        db: Database session
        thread_id: Thread ID
        role: Message role (user, assistant)
        content: Message content
        message_type: Message type
        message_metadata: Optional metadata
        
    Returns:
        ChatMessage: Created message
    """
    message = ChatMessage(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        role=role,
        content=content,
        message_type=message_type,
        message_metadata=message_metadata,
    )
    
    db.add(message)
    
    # Update thread last_message_at
    result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
    thread = result.scalar_one_or_none()
    if thread:
        thread.last_message_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return message


async def get_chat_messages(db: AsyncSession, thread_id: str) -> List[ChatMessage]:
    """Get messages for thread.
    
    Args:
        db: Database session
        thread_id: Thread ID
        
    Returns:
        List[ChatMessage]: List of messages
    """
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())
