"""Investigation Engine - AI-driven investigation orchestration."""

import uuid
import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import init_db, get_db_session
from shared.models import Investigation, Hypothesis, EvidenceItem, InvestigationStatus, ConfidenceLevel
from shared.events import EventProducer, InvestigationEvent, EventType
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("investigation_engine_startup", port=8002)
    init_db(settings.database)
    yield
    logger.info("investigation_engine_shutdown")


app = FastAPI(
    title="Investigation Engine",
    description="AI-driven investigation orchestration with SSE streaming",
    version="0.1.0",
    lifespan=lifespan,
)


# Schemas
class InvestigationCreate(BaseModel):
    tenant_id: str
    title: str
    description: Optional[str] = None
    incident_id: Optional[str] = None


class InvestigationResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: Optional[str]
    incident_id: Optional[str]
    status: InvestigationStatus
    root_cause: Optional[str]
    recommendations: Optional[list]
    confidence_level: Optional[ConfidenceLevel]
    confidence_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]


class HypothesisCreate(BaseModel):
    investigation_id: str
    hypothesis: str
    reasoning: Optional[str] = None


class HypothesisResponse(BaseModel):
    id: str
    investigation_id: str
    hypothesis: str
    reasoning: Optional[str]
    is_validated: bool
    confidence_score: Optional[float]
    created_at: datetime


class EvidenceCreate(BaseModel):
    investigation_id: str
    source: str
    evidence_type: str
    content: str
    metadata: dict = {}


class EvidenceResponse(BaseModel):
    id: str
    investigation_id: str
    source: str
    evidence_type: str
    content: str
    relevance_score: Optional[float]
    collected_at: datetime


async def run_investigation_pipeline(investigation_id: str, db: AsyncSession):
    """Run the 6-step investigation pipeline."""
    # Get investigation
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    
    if not investigation:
        return
    
    try:
        # Update status to running
        investigation.status = InvestigationStatus.RUNNING
        await db.commit()
        
        # Publish started event
        event = InvestigationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.INVESTIGATION_STARTED,
            tenant_id=investigation.tenant_id,
            timestamp=datetime.utcnow(),
            investigation_id=investigation.id,
            status="running",
            incident_id=investigation.incident_id,
            title=investigation.title,
            trigger_source="manual",
        )
        
        with EventProducer(settings.kafka) as producer:
            await producer.publish("investigations.requested", event)
        
        logger.info("investigation_started", investigation_id=investigation.id)
        
        # Step 1: Collect Data (simulated)
        await asyncio.sleep(2)
        evidence = EvidenceItem(
            id=str(uuid.uuid4()),
            investigation_id=investigation.id,
            source="cloudwatch",
            evidence_type="metrics",
            content="CPU usage spiked to 95% at 14:30 UTC",
            relevance_score=0.9,
            extra_data={"timestamp": "2024-01-15T14:30:00Z"},
        )
        db.add(evidence)
        await db.commit()
        
        # Step 2: Topology Context (simulated)
        await asyncio.sleep(1)
        
        # Step 3: Generate Hypotheses (simulated)
        await asyncio.sleep(2)
        hypothesis = Hypothesis(
            id=str(uuid.uuid4()),
            investigation_id=investigation.id,
            hypothesis="High CPU usage caused by memory leak in application",
            reasoning="CPU spike correlates with memory growth pattern",
            is_validated=False,
            confidence_score=0.85,
        )
        db.add(hypothesis)
        await db.commit()
        
        # Step 4: Analyze Evidence (simulated)
        await asyncio.sleep(2)
        hypothesis.is_validated = True
        hypothesis.validation_result = "Confirmed: Memory leak detected in service logs"
        await db.commit()
        
        # Step 5: Synthesize RCA (simulated)
        await asyncio.sleep(2)
        investigation.root_cause = "Memory leak in user-service causing CPU exhaustion"
        investigation.recommendations = [
            "Restart user-service to clear memory",
            "Deploy hotfix for memory leak",
            "Increase memory limits temporarily",
        ]
        investigation.confidence_level = ConfidenceLevel.HIGH
        investigation.confidence_score = 0.88
        
        # Step 6: Suggest Remediation (handled by Action Engine)
        
        # Complete investigation
        investigation.status = InvestigationStatus.COMPLETED
        investigation.completed_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Publish completed event
        event = InvestigationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.INVESTIGATION_COMPLETED,
            tenant_id=investigation.tenant_id,
            timestamp=datetime.utcnow(),
            investigation_id=investigation.id,
            status="completed",
            incident_id=investigation.incident_id,
            title=investigation.title,
            trigger_source="manual",
        )
        
        with EventProducer(settings.kafka) as producer:
            await producer.publish("investigations.completed", event)
        
        logger.info("investigation_completed", investigation_id=investigation.id)
        
    except Exception as e:
        logger.error("investigation_failed", investigation_id=investigation.id, error=str(e))
        investigation.status = InvestigationStatus.FAILED
        await db.commit()


@app.post("/api/v1/investigations", response_model=InvestigationResponse)
async def create_investigation(
    request: InvestigationCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create and start new investigation."""
    investigation = Investigation(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        title=request.title,
        description=request.description,
        incident_id=request.incident_id,
        status=InvestigationStatus.PENDING,
        extra_data={},
    )
    
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)
    
    # Start investigation pipeline in background
    asyncio.create_task(run_investigation_pipeline(investigation.id, db))
    
    logger.info("investigation_created", investigation_id=investigation.id)
    
    return InvestigationResponse(
        id=investigation.id,
        tenant_id=investigation.tenant_id,
        title=investigation.title,
        description=investigation.description,
        incident_id=investigation.incident_id,
        status=investigation.status,
        root_cause=investigation.root_cause,
        recommendations=investigation.recommendations,
        confidence_level=investigation.confidence_level,
        confidence_score=investigation.confidence_score,
        started_at=investigation.started_at,
        completed_at=investigation.completed_at,
    )


@app.get("/api/v1/investigations/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get investigation by ID."""
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found"
        )
    
    return InvestigationResponse(
        id=investigation.id,
        tenant_id=investigation.tenant_id,
        title=investigation.title,
        description=investigation.description,
        incident_id=investigation.incident_id,
        status=investigation.status,
        root_cause=investigation.root_cause,
        recommendations=investigation.recommendations,
        confidence_level=investigation.confidence_level,
        confidence_score=investigation.confidence_score,
        started_at=investigation.started_at,
        completed_at=investigation.completed_at,
    )


@app.get("/api/v1/investigations", response_model=list[InvestigationResponse])
async def list_investigations(
    tenant_id: Optional[str] = None,
    status: Optional[InvestigationStatus] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List investigations."""
    query = select(Investigation).order_by(desc(Investigation.started_at)).limit(limit)
    
    if tenant_id:
        query = query.where(Investigation.tenant_id == tenant_id)
    if status:
        query = query.where(Investigation.status == status)
    
    result = await db.execute(query)
    investigations = result.scalars().all()
    
    return [
        InvestigationResponse(
            id=inv.id,
            tenant_id=inv.tenant_id,
            title=inv.title,
            description=inv.description,
            incident_id=inv.incident_id,
            status=inv.status,
            root_cause=inv.root_cause,
            recommendations=inv.recommendations,
            confidence_level=inv.confidence_level,
            confidence_score=inv.confidence_score,
            started_at=inv.started_at,
            completed_at=inv.completed_at,
        )
        for inv in investigations
    ]


@app.get("/api/v1/investigations/{investigation_id}/stream")
async def stream_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Stream investigation progress via SSE."""
    async def event_generator():
        """Generate SSE events for investigation progress."""
        # Check investigation exists
        result = await db.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        investigation = result.scalar_one_or_none()
        
        if not investigation:
            yield f"event: error\ndata: Investigation not found\n\n"
            return
        
        # Stream updates
        last_status = None
        for _ in range(30):  # Poll for 30 seconds
            result = await db.execute(
                select(Investigation).where(Investigation.id == investigation_id)
            )
            investigation = result.scalar_one_or_none()
            
            if investigation and investigation.status != last_status:
                last_status = investigation.status
                yield f"event: status_update\ndata: {investigation.status.value}\n\n"
                
                if investigation.status == InvestigationStatus.COMPLETED:
                    yield f"event: completed\ndata: Investigation completed\n\n"
                    break
                elif investigation.status == InvestigationStatus.FAILED:
                    yield f"event: failed\ndata: Investigation failed\n\n"
                    break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/v1/investigations/{investigation_id}/hypotheses", response_model=list[HypothesisResponse])
async def get_hypotheses(
    investigation_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hypotheses for investigation."""
    result = await db.execute(
        select(Hypothesis)
        .where(Hypothesis.investigation_id == investigation_id)
        .order_by(desc(Hypothesis.created_at))
    )
    hypotheses = result.scalars().all()
    
    return [
        HypothesisResponse(
            id=h.id,
            investigation_id=h.investigation_id,
            hypothesis=h.hypothesis,
            reasoning=h.reasoning,
            is_validated=h.is_validated,
            confidence_score=h.confidence_score,
            created_at=h.created_at,
        )
        for h in hypotheses
    ]


@app.get("/api/v1/investigations/{investigation_id}/evidence", response_model=list[EvidenceResponse])
async def get_evidence(
    investigation_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get evidence for investigation."""
    result = await db.execute(
        select(EvidenceItem)
        .where(EvidenceItem.investigation_id == investigation_id)
        .order_by(desc(EvidenceItem.collected_at))
    )
    evidence_items = result.scalars().all()
    
    return [
        EvidenceResponse(
            id=e.id,
            investigation_id=e.investigation_id,
            source=e.source,
            evidence_type=e.evidence_type,
            content=e.content,
            relevance_score=e.relevance_score,
            collected_at=e.collected_at,
        )
        for e in evidence_items
    ]


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "investigation-engine"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
