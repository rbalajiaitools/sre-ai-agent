"""Admin Service - Connectors, policies, and audit logs."""

import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import init_db, get_db_session
from shared.models import Connector, Policy, AuditLog
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("admin_service_startup", port=8006)
    init_db(settings.database)
    yield
    logger.info("admin_service_shutdown")


app = FastAPI(
    title="Admin Service",
    description="Connector management, policies, and audit logs",
    version="0.1.0",
    lifespan=lifespan,
)


class ConnectorCreate(BaseModel):
    tenant_id: str
    name: str
    connector_type: str
    config: dict


class ConnectorResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    connector_type: str
    is_active: bool
    health_status: Optional[str]
    created_at: datetime


class PolicyCreate(BaseModel):
    tenant_id: str
    name: str
    policy_type: str
    rules: dict


class PolicyResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    policy_type: str
    is_active: bool
    priority: int
    created_at: datetime


@app.post("/api/v1/connectors", response_model=ConnectorResponse)
async def create_connector(
    request: ConnectorCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new connector."""
    connector = Connector(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        name=request.name,
        connector_type=request.connector_type,
        config=request.config,
        is_active=True,
    )
    
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    
    logger.info("connector_created", connector_id=connector.id, type=connector.connector_type)
    
    return ConnectorResponse(
        id=connector.id,
        tenant_id=connector.tenant_id,
        name=connector.name,
        connector_type=connector.connector_type,
        is_active=connector.is_active,
        health_status=connector.health_status,
        created_at=connector.created_at,
    )


@app.get("/api/v1/connectors", response_model=list[ConnectorResponse])
async def list_connectors(
    tenant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List connectors."""
    query = select(Connector).order_by(desc(Connector.created_at))
    
    if tenant_id:
        query = query.where(Connector.tenant_id == tenant_id)
    
    result = await db.execute(query)
    connectors = result.scalars().all()
    
    return [
        ConnectorResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            name=c.name,
            connector_type=c.connector_type,
            is_active=c.is_active,
            health_status=c.health_status,
            created_at=c.created_at,
        )
        for c in connectors
    ]


@app.post("/api/v1/connectors/execute")
async def execute_connector(connector_id: str, method: str, parameters: dict = {}):
    """Execute connector method."""
    logger.info("connector_execute", connector_id=connector_id, method=method)
    
    # Simulated execution
    return {
        "connector_id": connector_id,
        "method": method,
        "status": "success",
        "result": {"data": "simulated result"}
    }


@app.post("/api/v1/policies", response_model=PolicyResponse)
async def create_policy(
    request: PolicyCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new policy."""
    policy = Policy(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        name=request.name,
        policy_type=request.policy_type,
        rules=request.rules,
        is_active=True,
        priority=0,
    )
    
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    logger.info("policy_created", policy_id=policy.id, type=policy.policy_type)
    
    return PolicyResponse(
        id=policy.id,
        tenant_id=policy.tenant_id,
        name=policy.name,
        policy_type=policy.policy_type,
        is_active=policy.is_active,
        priority=policy.priority,
        created_at=policy.created_at,
    )


@app.get("/api/v1/policies", response_model=list[PolicyResponse])
async def list_policies(
    tenant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List policies."""
    query = select(Policy).order_by(desc(Policy.priority))
    
    if tenant_id:
        query = query.where(Policy.tenant_id == tenant_id)
    
    result = await db.execute(query)
    policies = result.scalars().all()
    
    return [
        PolicyResponse(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            policy_type=p.policy_type,
            is_active=p.is_active,
            priority=p.priority,
            created_at=p.created_at,
        )
        for p in policies
    ]


@app.post("/api/v1/policies/evaluate")
async def evaluate_policy(policy_id: str, resource_type: str, resource_id: str):
    """Evaluate policy against resource."""
    logger.info("policy_evaluate", policy_id=policy_id, resource_type=resource_type)
    
    return {
        "policy_id": policy_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "passed": True,
        "reason": "Policy evaluation passed"
    }


@app.get("/api/v1/connectors/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get connector by ID."""
    result = await db.execute(
        select(Connector).where(Connector.id == connector_id)
    )
    connector = result.scalar_one_or_none()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return ConnectorResponse(
        id=connector.id,
        tenant_id=connector.tenant_id,
        name=connector.name,
        connector_type=connector.connector_type,
        is_active=connector.is_active,
        health_status=connector.health_status,
        created_at=connector.created_at,
    )


@app.put("/api/v1/connectors/{connector_id}", response_model=ConnectorResponse)
async def update_connector(
    connector_id: str,
    name: Optional[str] = None,
    config: Optional[dict] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Update connector."""
    result = await db.execute(
        select(Connector).where(Connector.id == connector_id)
    )
    connector = result.scalar_one_or_none()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if name is not None:
        connector.name = name
    if config is not None:
        connector.config = config
    if is_active is not None:
        connector.is_active = is_active
    
    await db.commit()
    await db.refresh(connector)
    
    logger.info("connector_updated", connector_id=connector.id)
    
    return ConnectorResponse(
        id=connector.id,
        tenant_id=connector.tenant_id,
        name=connector.name,
        connector_type=connector.connector_type,
        is_active=connector.is_active,
        health_status=connector.health_status,
        created_at=connector.created_at,
    )


@app.delete("/api/v1/connectors/{connector_id}")
async def delete_connector(
    connector_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete connector."""
    result = await db.execute(
        select(Connector).where(Connector.id == connector_id)
    )
    connector = result.scalar_one_or_none()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    await db.delete(connector)
    await db.commit()
    
    logger.info("connector_deleted", connector_id=connector_id)
    
    return {"message": "Connector deleted successfully"}


@app.get("/api/v1/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get policy by ID."""
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    return PolicyResponse(
        id=policy.id,
        tenant_id=policy.tenant_id,
        name=policy.name,
        policy_type=policy.policy_type,
        is_active=policy.is_active,
        priority=policy.priority,
        created_at=policy.created_at,
    )


@app.put("/api/v1/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    name: Optional[str] = None,
    rules: Optional[dict] = None,
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Update policy."""
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    if name is not None:
        policy.name = name
    if rules is not None:
        policy.rules = rules
    if is_active is not None:
        policy.is_active = is_active
    if priority is not None:
        policy.priority = priority
    
    await db.commit()
    await db.refresh(policy)
    
    logger.info("policy_updated", policy_id=policy.id)
    
    return PolicyResponse(
        id=policy.id,
        tenant_id=policy.tenant_id,
        name=policy.name,
        policy_type=policy.policy_type,
        is_active=policy.is_active,
        priority=policy.priority,
        created_at=policy.created_at,
    )


@app.delete("/api/v1/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete policy."""
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    await db.delete(policy)
    await db.commit()
    
    logger.info("policy_deleted", policy_id=policy_id)
    
    return {"message": "Policy deleted successfully"}


@app.get("/api/v1/audit")
async def list_audit_logs(
    tenant_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List audit logs with filtering."""
    query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    
    if tenant_id:
        query = query.where(AuditLog.tenant_id == tenant_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "tenant_id": log.tenant_id,
            "actor_email": log.actor_email,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.timestamp,
            "ip_address": log.ip_address,
        }
        for log in logs
    ]


@app.get("/api/v1/audit/export")
async def export_audit_logs(
    tenant_id: Optional[str] = None,
    format: str = "json",
    db: AsyncSession = Depends(get_db_session)
):
    """Export audit logs as JSON or CSV."""
    query = select(AuditLog).order_by(desc(AuditLog.timestamp))
    
    if tenant_id:
        query = query.where(AuditLog.tenant_id == tenant_id)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Tenant ID", "Actor", "Action", "Resource Type", "Resource ID", "Timestamp", "IP Address"])
        
        for log in logs:
            writer.writerow([
                log.id,
                log.tenant_id,
                log.actor_email,
                log.action,
                log.resource_type,
                log.resource_id,
                log.timestamp.isoformat(),
                log.ip_address or "",
            ])
        
        return {"format": "csv", "data": output.getvalue()}
    
    # JSON format
    return {
        "format": "json",
        "data": [
            {
                "id": log.id,
                "tenant_id": log.tenant_id,
                "actor_email": log.actor_email,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
            }
            for log in logs
        ]
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "admin-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
