"""
Knowledge Base API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db import crud


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Request/Response Models
class KnowledgeCreate(BaseModel):
    """Create knowledge request."""
    title: str
    type: str  # runbook, architecture, code_snippet, investigation, external_link
    description: Optional[str] = None
    content: Optional[str] = None
    external_url: Optional[str] = None
    tags: Optional[List[str]] = None
    service_name: Optional[str] = None
    incident_number: Optional[str] = None
    investigation_id: Optional[str] = None
    created_by: Optional[str] = None


class KnowledgeUpdate(BaseModel):
    """Update knowledge request."""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    external_url: Optional[str] = None
    tags: Optional[List[str]] = None
    service_name: Optional[str] = None


class KnowledgeResponse(BaseModel):
    """Knowledge response."""
    id: str
    tenant_id: str
    title: str
    type: str
    description: Optional[str]
    content: Optional[str]
    external_url: Optional[str]
    tags: Optional[List[str]]
    service_name: Optional[str]
    incident_number: Optional[str]
    investigation_id: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str
    usage_count: int
    last_used_at: Optional[str]

    class Config:
        from_attributes = True


class ConvertInvestigationRequest(BaseModel):
    """Convert investigation to knowledge request."""
    investigation_id: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class SearchKnowledgeRequest(BaseModel):
    """Search knowledge request."""
    service_name: Optional[str] = None
    incident_number: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = 5


# Endpoints
@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge(
    request: KnowledgeCreate,
    tenant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create new knowledge base entry."""
    knowledge = await crud.create_knowledge(
        db=db,
        tenant_id=tenant_id,
        title=request.title,
        knowledge_type=request.type,
        description=request.description,
        content=request.content,
        external_url=request.external_url,
        tags=request.tags,
        service_name=request.service_name,
        incident_number=request.incident_number,
        investigation_id=request.investigation_id,
        created_by=request.created_by,
    )
    
    return KnowledgeResponse(
        id=knowledge.id,
        tenant_id=knowledge.tenant_id,
        title=knowledge.title,
        type=knowledge.type,
        description=knowledge.description,
        content=knowledge.content,
        external_url=knowledge.external_url,
        tags=knowledge.tags,
        service_name=knowledge.service_name,
        incident_number=knowledge.incident_number,
        investigation_id=knowledge.investigation_id,
        created_by=knowledge.created_by,
        created_at=knowledge.created_at.isoformat(),
        updated_at=knowledge.updated_at.isoformat(),
        usage_count=knowledge.usage_count,
        last_used_at=knowledge.last_used_at.isoformat() if knowledge.last_used_at else None,
    )


@router.get("/", response_model=List[KnowledgeResponse])
async def list_knowledge(
    tenant_id: str,
    type: Optional[str] = None,
    service_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List knowledge base entries."""
    knowledge_list = await crud.get_knowledge_list(
        db=db,
        tenant_id=tenant_id,
        knowledge_type=type,
        service_name=service_name,
    )
    
    return [
        KnowledgeResponse(
            id=k.id,
            tenant_id=k.tenant_id,
            title=k.title,
            type=k.type,
            description=k.description,
            content=k.content,
            external_url=k.external_url,
            tags=k.tags,
            service_name=k.service_name,
            incident_number=k.incident_number,
            investigation_id=k.investigation_id,
            created_by=k.created_by,
            created_at=k.created_at.isoformat(),
            updated_at=k.updated_at.isoformat(),
            usage_count=k.usage_count,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in knowledge_list
    ]


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get knowledge by ID."""
    knowledge = await crud.get_knowledge(db, knowledge_id)
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return KnowledgeResponse(
        id=knowledge.id,
        tenant_id=knowledge.tenant_id,
        title=knowledge.title,
        type=knowledge.type,
        description=knowledge.description,
        content=knowledge.content,
        external_url=knowledge.external_url,
        tags=knowledge.tags,
        service_name=knowledge.service_name,
        incident_number=knowledge.incident_number,
        investigation_id=knowledge.investigation_id,
        created_by=knowledge.created_by,
        created_at=knowledge.created_at.isoformat(),
        updated_at=knowledge.updated_at.isoformat(),
        usage_count=knowledge.usage_count,
        last_used_at=knowledge.last_used_at.isoformat() if knowledge.last_used_at else None,
    )


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    request: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update knowledge entry."""
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    knowledge = await crud.update_knowledge(db, knowledge_id, **update_data)
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return KnowledgeResponse(
        id=knowledge.id,
        tenant_id=knowledge.tenant_id,
        title=knowledge.title,
        type=knowledge.type,
        description=knowledge.description,
        content=knowledge.content,
        external_url=knowledge.external_url,
        tags=knowledge.tags,
        service_name=knowledge.service_name,
        incident_number=knowledge.incident_number,
        investigation_id=knowledge.investigation_id,
        created_by=knowledge.created_by,
        created_at=knowledge.created_at.isoformat(),
        updated_at=knowledge.updated_at.isoformat(),
        usage_count=knowledge.usage_count,
        last_used_at=knowledge.last_used_at.isoformat() if knowledge.last_used_at else None,
    )


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete knowledge entry."""
    success = await crud.delete_knowledge(db, knowledge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return {"message": "Knowledge deleted successfully"}


@router.post("/convert-investigation", response_model=KnowledgeResponse)
async def convert_investigation_to_knowledge(
    request: ConvertInvestigationRequest,
    tenant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Convert completed investigation to knowledge base entry."""
    # Get investigation
    investigation = await crud.get_investigation(db, request.investigation_id)
    
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Allow conversion for resolved or rca_complete investigations
    if investigation.status not in ["resolved", "rca_complete", "completed"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Investigation must be completed (current status: {investigation.status})"
        )
    
    # Create knowledge content from investigation
    content_parts = []
    
    # Add RCA
    if investigation.rca:
        rca_data = investigation.rca
        if isinstance(rca_data, dict):
            root_cause = rca_data.get('root_cause', '')
            content_parts.append(f"## Root Cause Analysis\n\n{root_cause}")
            
            # Add contributing factors if available
            contributing_factors = rca_data.get('contributing_factors', [])
            if contributing_factors:
                content_parts.append("### Contributing Factors\n")
                for factor in contributing_factors:
                    content_parts.append(f"- {factor}")
    
    # Add Resolution
    if investigation.resolution:
        resolution_data = investigation.resolution
        if isinstance(resolution_data, dict):
            recommended_fix = resolution_data.get('recommended_fix', '')
            content_parts.append(f"## Resolution\n\n{recommended_fix}")
            
            # Add fix steps if available
            fix_steps = resolution_data.get('fix_steps', [])
            if fix_steps:
                content_parts.append("### Steps to Resolve\n")
                for i, step in enumerate(fix_steps, 1):
                    content_parts.append(f"{i}. {step}")
    
    # Add Agent Findings
    if investigation.agent_results:
        content_parts.append("## Investigation Findings\n")
        for agent in investigation.agent_results:
            if isinstance(agent, dict) and agent.get('success'):
                agent_type = agent.get('agent_type', 'Unknown')
                evidence = agent.get('evidence', [])
                if evidence:
                    content_parts.append(f"### {agent_type.title()} Agent\n")
                    for item in evidence[:5]:  # Limit to top 5 findings
                        content_parts.append(f"- {item}")
    
    content = "\n\n".join(content_parts)
    
    # Create knowledge entry
    knowledge = await crud.create_knowledge(
        db=db,
        tenant_id=tenant_id,
        title=request.title,
        knowledge_type="investigation",
        description=request.description or f"Investigation for {investigation.incident_number}",
        content=content,
        tags=request.tags or ["investigation", investigation.incident_number],
        service_name=investigation.service_name,
        incident_number=investigation.incident_number,
        investigation_id=investigation.id,
        created_by="system",
    )
    
    return KnowledgeResponse(
        id=knowledge.id,
        tenant_id=knowledge.tenant_id,
        title=knowledge.title,
        type=knowledge.type,
        description=knowledge.description,
        content=knowledge.content,
        external_url=knowledge.external_url,
        tags=knowledge.tags,
        service_name=knowledge.service_name,
        incident_number=knowledge.incident_number,
        investigation_id=knowledge.investigation_id,
        created_by=knowledge.created_by,
        created_at=knowledge.created_at.isoformat(),
        updated_at=knowledge.updated_at.isoformat(),
        usage_count=knowledge.usage_count,
        last_used_at=knowledge.last_used_at.isoformat() if knowledge.last_used_at else None,
    )


@router.post("/search", response_model=List[KnowledgeResponse])
async def search_knowledge(
    request: SearchKnowledgeRequest,
    tenant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Search for relevant knowledge."""
    knowledge_list = await crud.search_relevant_knowledge(
        db=db,
        tenant_id=tenant_id,
        service_name=request.service_name,
        incident_number=request.incident_number,
        search_text=request.search_text,
        limit=request.limit,
    )
    
    return [
        KnowledgeResponse(
            id=k.id,
            tenant_id=k.tenant_id,
            title=k.title,
            type=k.type,
            description=k.description,
            content=k.content,
            external_url=k.external_url,
            tags=k.tags,
            service_name=k.service_name,
            incident_number=k.incident_number,
            investigation_id=k.investigation_id,
            created_by=k.created_by,
            created_at=k.created_at.isoformat(),
            updated_at=k.updated_at.isoformat(),
            usage_count=k.usage_count,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in knowledge_list
    ]
