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


# Knowledge Base CRUD
async def create_knowledge(
    db: AsyncSession,
    tenant_id: str,
    title: str,
    knowledge_type: str,
    description: Optional[str] = None,
    content: Optional[str] = None,
    external_url: Optional[str] = None,
    tags: Optional[List[str]] = None,
    service_name: Optional[str] = None,
    incident_number: Optional[str] = None,
    investigation_id: Optional[str] = None,
    created_by: Optional[str] = None
):
    """Create knowledge base entry.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        title: Knowledge title
        knowledge_type: Type (runbook, architecture, code_snippet, investigation, external_link)
        description: Optional description
        content: Optional markdown content
        external_url: Optional external URL
        tags: Optional list of tags
        service_name: Optional service name
        incident_number: Optional incident number
        investigation_id: Optional investigation ID
        created_by: Optional creator name
        
    Returns:
        KnowledgeBase: Created knowledge entry
    """
    from app.db.models import KnowledgeBase
    
    knowledge = KnowledgeBase(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        title=title,
        type=knowledge_type,
        description=description,
        content=content,
        external_url=external_url,
        tags=tags or [],
        service_name=service_name,
        incident_number=incident_number,
        investigation_id=investigation_id,
        created_by=created_by,
    )
    
    db.add(knowledge)
    await db.commit()
    await db.refresh(knowledge)
    
    return knowledge


async def get_knowledge_list(
    db: AsyncSession,
    tenant_id: str,
    knowledge_type: Optional[str] = None,
    service_name: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """Get knowledge base entries.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        knowledge_type: Optional filter by type
        service_name: Optional filter by service
        tags: Optional filter by tags
        
    Returns:
        List[KnowledgeBase]: List of knowledge entries
    """
    from app.db.models import KnowledgeBase
    
    query = select(KnowledgeBase).where(KnowledgeBase.tenant_id == tenant_id)
    
    if knowledge_type:
        query = query.where(KnowledgeBase.type == knowledge_type)
    
    if service_name:
        query = query.where(KnowledgeBase.service_name == service_name)
    
    # Note: SQLite JSON filtering is limited, so we'll filter tags in Python
    result = await db.execute(query.order_by(KnowledgeBase.created_at.desc()))
    knowledge_list = list(result.scalars().all())
    
    # Filter by tags if provided
    if tags:
        knowledge_list = [
            k for k in knowledge_list
            if k.tags and any(tag in k.tags for tag in tags)
        ]
    
    return knowledge_list


async def get_knowledge(db: AsyncSession, knowledge_id: str):
    """Get knowledge by ID.
    
    Args:
        db: Database session
        knowledge_id: Knowledge ID
        
    Returns:
        Optional[KnowledgeBase]: Knowledge entry or None
    """
    from app.db.models import KnowledgeBase
    
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_id))
    return result.scalar_one_or_none()


async def update_knowledge(
    db: AsyncSession,
    knowledge_id: str,
    **kwargs
):
    """Update knowledge entry.
    
    Args:
        db: Database session
        knowledge_id: Knowledge ID
        **kwargs: Fields to update
        
    Returns:
        Optional[KnowledgeBase]: Updated knowledge or None
    """
    knowledge = await get_knowledge(db, knowledge_id)
    
    if not knowledge:
        return None
    
    for key, value in kwargs.items():
        if hasattr(knowledge, key) and key != 'id':
            setattr(knowledge, key, value)
    
    knowledge.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(knowledge)
    
    return knowledge


async def delete_knowledge(db: AsyncSession, knowledge_id: str) -> bool:
    """Delete knowledge entry.
    
    Args:
        db: Database session
        knowledge_id: Knowledge ID
        
    Returns:
        bool: True if deleted, False if not found
    """
    knowledge = await get_knowledge(db, knowledge_id)
    
    if not knowledge:
        return False
    
    await db.delete(knowledge)
    await db.commit()
    
    return True


async def search_relevant_knowledge(
    db: AsyncSession,
    tenant_id: str,
    service_name: Optional[str] = None,
    incident_number: Optional[str] = None,
    search_text: Optional[str] = None,
    limit: int = 5
):
    """Search for relevant knowledge based on service, incident, or text.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        service_name: Optional service name
        incident_number: Optional incident number
        search_text: Optional search text
        limit: Maximum results
        
    Returns:
        List[KnowledgeBase]: Relevant knowledge entries
    """
    from app.db.models import KnowledgeBase
    
    query = select(KnowledgeBase).where(KnowledgeBase.tenant_id == tenant_id)
    
    result = await db.execute(query.order_by(KnowledgeBase.usage_count.desc()).limit(limit * 3))
    knowledge_list = list(result.scalars().all())
    
    if not knowledge_list:
        return []
    
    # Score each knowledge entry based on relevance
    scored_results = []
    
    for k in knowledge_list:
        score = 0
        
        # Exact service name match (highest priority)
        if service_name and k.service_name:
            if k.service_name.lower() == service_name.lower():
                score += 10
            # Partial service name match
            elif service_name.lower() in k.service_name.lower() or k.service_name.lower() in service_name.lower():
                score += 5
            # Check for common keywords (s3, lambda, ec2, etc.)
            service_keywords = set(service_name.lower().split('-'))
            kb_keywords = set(k.service_name.lower().split('-'))
            common_keywords = service_keywords & kb_keywords
            if common_keywords:
                score += len(common_keywords) * 2
        
        # Search text matching
        if search_text:
            search_lower = search_text.lower()
            
            # Title match
            if k.title and search_lower in k.title.lower():
                score += 3
            
            # Description match
            if k.description and search_lower in k.description.lower():
                score += 2
            
            # Content match
            if k.content and search_lower in k.content.lower():
                score += 1
            
            # Root cause match
            if k.root_cause and search_lower in k.root_cause.lower():
                score += 2
            
            # Check for technology keywords (s3, bucket, lambda, etc.)
            tech_keywords = ['s3', 'bucket', 'lambda', 'ec2', 'rds', 'dynamodb', 'cloudfront', 
                           'website', 'static', 'api', 'database', 'cache', 'redis']
            for keyword in tech_keywords:
                if keyword in search_lower:
                    # Check if this keyword appears in knowledge
                    kb_text = f"{k.title} {k.description} {k.content} {k.root_cause}".lower()
                    if keyword in kb_text:
                        score += 4  # Strong match for technology keywords
        
        # Tags matching
        if k.tags and (service_name or search_text):
            search_terms = []
            if service_name:
                search_terms.extend(service_name.lower().split('-'))
            if search_text:
                search_terms.extend(search_text.lower().split())
            
            for tag in k.tags:
                if any(term in tag.lower() for term in search_terms):
                    score += 2
        
        # Only include if there's some relevance
        if score > 0:
            scored_results.append((score, k))
    
    # Sort by score (descending) and return top results
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # Return only if score is meaningful (at least 2)
    relevant_results = [(score, k) for score, k in scored_results if score >= 2]
    
    return [k for _, k in relevant_results[:limit]]


async def track_knowledge_usage(
    db: AsyncSession,
    knowledge_id: str,
    investigation_id: str,
    relevance_score: Optional[float] = None,
    used_in_rca: bool = False,
    used_in_resolution: bool = False
):
    """Track knowledge usage in investigation.
    
    Args:
        db: Database session
        knowledge_id: Knowledge ID
        investigation_id: Investigation ID
        relevance_score: Optional relevance score (0-100)
        used_in_rca: Whether used in RCA
        used_in_resolution: Whether used in resolution
        
    Returns:
        KnowledgeUsage: Created usage record
    """
    from app.db.models import KnowledgeUsage
    
    usage = KnowledgeUsage(
        id=str(uuid.uuid4()),
        knowledge_id=knowledge_id,
        investigation_id=investigation_id,
        relevance_score=relevance_score,
        used_in_rca=used_in_rca,
        used_in_resolution=used_in_resolution,
    )
    
    db.add(usage)
    
    # Update knowledge usage count and last_used_at
    knowledge = await get_knowledge(db, knowledge_id)
    if knowledge:
        knowledge.usage_count += 1
        knowledge.last_used_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(usage)
    
    return usage


async def get_knowledge_usage_for_investigation(
    db: AsyncSession,
    investigation_id: str
):
    """Get knowledge used in investigation.
    
    Args:
        db: Database session
        investigation_id: Investigation ID
        
    Returns:
        List[tuple]: List of (KnowledgeUsage, KnowledgeBase) tuples
    """
    from app.db.models import KnowledgeUsage, KnowledgeBase
    
    result = await db.execute(
        select(KnowledgeUsage, KnowledgeBase)
        .join(KnowledgeBase, KnowledgeUsage.knowledge_id == KnowledgeBase.id)
        .where(KnowledgeUsage.investigation_id == investigation_id)
        .order_by(KnowledgeUsage.relevance_score.desc())
    )
    
    return list(result.all())
