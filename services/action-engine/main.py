"""Action Engine - Remediation workflows and approvals."""

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
from shared.models import Action, ActionExecution, ActionType, ActionStatus
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("action_engine_startup", port=8005)
    init_db(settings.database)
    yield
    logger.info("action_engine_shutdown")


app = FastAPI(
    title="Action Engine",
    description="Remediation workflows with approval and execution",
    version="0.1.0",
    lifespan=lifespan,
)


class ActionCreate(BaseModel):
    investigation_id: Optional[str] = None
    action_type: ActionType
    title: str
    description: Optional[str] = None
    config: dict = {}
    requires_approval: bool = True


class ActionResponse(BaseModel):
    id: str
    investigation_id: Optional[str]
    action_type: ActionType
    title: str
    description: Optional[str]
    status: ActionStatus
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime


class ActionApproval(BaseModel):
    approved_by: str
    approved: bool
    rejection_reason: Optional[str] = None


@app.post("/api/v1/actions", response_model=ActionResponse)
async def create_action(
    request: ActionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new remediation action."""
    action = Action(
        id=str(uuid.uuid4()),
        investigation_id=request.investigation_id,
        action_type=request.action_type,
        title=request.title,
        description=request.description,
        config=request.config,
        status=ActionStatus.PENDING_APPROVAL if request.requires_approval else ActionStatus.APPROVED,
        requires_approval=request.requires_approval,
    )
    
    db.add(action)
    await db.commit()
    await db.refresh(action)
    
    logger.info("action_created", action_id=action.id, action_type=action.action_type)
    
    return ActionResponse(
        id=action.id,
        investigation_id=action.investigation_id,
        action_type=action.action_type,
        title=action.title,
        description=action.description,
        status=action.status,
        requires_approval=action.requires_approval,
        approved_by=action.approved_by,
        approved_at=action.approved_at,
        created_at=action.created_at,
    )


@app.get("/api/v1/actions/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get action by ID."""
    result = await db.execute(
        select(Action).where(Action.id == action_id)
    )
    action = result.scalar_one_or_none()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    return ActionResponse(
        id=action.id,
        investigation_id=action.investigation_id,
        action_type=action.action_type,
        title=action.title,
        description=action.description,
        status=action.status,
        requires_approval=action.requires_approval,
        approved_by=action.approved_by,
        approved_at=action.approved_at,
        created_at=action.created_at,
    )


@app.get("/api/v1/actions", response_model=list[ActionResponse])
async def list_actions(
    status: Optional[ActionStatus] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List actions."""
    query = select(Action).order_by(desc(Action.created_at)).limit(limit)
    
    if status:
        query = query.where(Action.status == status)
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    return [
        ActionResponse(
            id=action.id,
            investigation_id=action.investigation_id,
            action_type=action.action_type,
            title=action.title,
            description=action.description,
            status=action.status,
            requires_approval=action.requires_approval,
            approved_by=action.approved_by,
            approved_at=action.approved_at,
            created_at=action.created_at,
        )
        for action in actions
    ]


@app.post("/api/v1/actions/{action_id}/approve")
async def approve_action(
    action_id: str,
    request: ActionApproval,
    db: AsyncSession = Depends(get_db_session)
):
    """Approve or reject action."""
    result = await db.execute(
        select(Action).where(Action.id == action_id)
    )
    action = result.scalar_one_or_none()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    if request.approved:
        action.status = ActionStatus.APPROVED
        action.approved_by = request.approved_by
        action.approved_at = datetime.now(timezone.utc)
        logger.info("action_approved", action_id=action.id, approved_by=request.approved_by)
    else:
        action.status = ActionStatus.REJECTED
        action.rejection_reason = request.rejection_reason
        logger.info("action_rejected", action_id=action.id, rejected_by=request.approved_by)
    
    await db.commit()
    
    return {"status": "approved" if request.approved else "rejected"}


@app.post("/api/v1/actions/{action_id}/execute")
async def execute_action(
    action_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Execute approved action."""
    result = await db.execute(
        select(Action).where(Action.id == action_id)
    )
    action = result.scalar_one_or_none()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    if action.status != ActionStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be approved before execution"
        )
    
    # Create execution record
    execution = ActionExecution(
        id=str(uuid.uuid4()),
        action_id=action.id,
        executor="system",
        status="running",
    )
    
    db.add(execution)
    action.status = ActionStatus.EXECUTING
    await db.commit()
    
    # Simulate execution
    execution.status = "completed"
    execution.result = {"message": "Action executed successfully"}
    execution.completed_at = datetime.now(timezone.utc)
    action.status = ActionStatus.COMPLETED
    await db.commit()
    
    logger.info("action_executed", action_id=action.id, execution_id=execution.id)
    
    return {"status": "completed", "execution_id": execution.id}


@app.post("/api/v1/actions/suggest")
async def suggest_actions(investigation_id: str):
    """Suggest remediation actions for investigation."""
    logger.info("suggest_actions", investigation_id=investigation_id)
    
    return {
        "investigation_id": investigation_id,
        "suggestions": [
            {
                "action_type": "restart_service",
                "title": "Restart user-service",
                "description": "Restart to clear memory leak",
                "confidence": 0.9
            },
            {
                "action_type": "scale_up",
                "title": "Scale up user-service",
                "description": "Add 2 more instances",
                "confidence": 0.7
            }
        ]
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "action-engine"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
