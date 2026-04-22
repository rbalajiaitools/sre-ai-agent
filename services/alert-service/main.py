"""Alert Service - Alert ingestion and incident correlation."""

import uuid
import hashlib
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import init_db, get_db_session
from shared.models import Alert, Incident, AlertSeverity, AlertStatus, IncidentState
from shared.events import EventProducer, AlertEvent, InvestigationEvent, EventType
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("alert_service_startup", port=8001)
    init_db(settings.database)
    yield
    logger.info("alert_service_shutdown")


app = FastAPI(
    title="Alert Service",
    description="Alert ingestion and incident correlation",
    version="0.1.0",
    lifespan=lifespan,
)


# Schemas
class AlertCreate(BaseModel):
    tenant_id: str
    source: str
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    labels: dict = {}
    annotations: dict = {}
    external_id: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    tenant_id: str
    source: str
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    fingerprint: str
    incident_id: Optional[str]
    fired_at: datetime
    created_at: datetime


class IncidentCreate(BaseModel):
    tenant_id: str
    title: str
    description: Optional[str] = None
    priority: int = 3
    category: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    tenant_id: str
    number: str
    title: str
    description: Optional[str]
    priority: int
    state: IncidentState
    affected_services: list
    opened_at: datetime


def generate_fingerprint(alert_data: dict) -> str:
    """Generate fingerprint for alert deduplication."""
    # Create fingerprint from source, title, and key labels
    fingerprint_data = f"{alert_data['source']}:{alert_data['title']}"
    
    # Add important labels
    if "service" in alert_data.get("labels", {}):
        fingerprint_data += f":{alert_data['labels']['service']}"
    if "instance" in alert_data.get("labels", {}):
        fingerprint_data += f":{alert_data['labels']['instance']}"
    
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


async def trigger_investigation(alert: Alert, db: AsyncSession):
    """Trigger auto-investigation for high-severity alerts."""
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
        # Publish investigation request event
        event = InvestigationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.INVESTIGATION_REQUESTED,
            tenant_id=alert.tenant_id,
            timestamp=datetime.utcnow(),
            investigation_id=str(uuid.uuid4()),
            status="pending",
            incident_id=alert.incident_id,
            title=f"Auto-investigation: {alert.title}",
            trigger_source="alert",
        )
        
        with EventProducer(settings.kafka) as producer:
            await producer.publish("investigations.requested", event)
        
        logger.info(
            "investigation_triggered",
            alert_id=alert.id,
            severity=alert.severity,
            investigation_id=event.investigation_id
        )


@app.post("/api/v1/alerts", response_model=AlertResponse)
async def create_alert(
    request: AlertCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Ingest new alert."""
    # Generate fingerprint
    fingerprint = generate_fingerprint(request.model_dump())
    
    # Check for duplicate (within last hour)
    result = await db.execute(
        select(Alert)
        .where(Alert.fingerprint == fingerprint)
        .where(Alert.tenant_id == request.tenant_id)
        .where(Alert.status != AlertStatus.CLOSED)
        .order_by(desc(Alert.created_at))
        .limit(1)
    )
    existing_alert = result.scalar_one_or_none()
    
    if existing_alert:
        logger.info("alert_deduplicated", fingerprint=fingerprint, alert_id=existing_alert.id)
        return AlertResponse(
            id=existing_alert.id,
            tenant_id=existing_alert.tenant_id,
            source=existing_alert.source,
            title=existing_alert.title,
            description=existing_alert.description,
            severity=existing_alert.severity,
            status=existing_alert.status,
            fingerprint=existing_alert.fingerprint,
            incident_id=existing_alert.incident_id,
            fired_at=existing_alert.fired_at,
            created_at=existing_alert.created_at,
        )
    
    # Create new alert
    alert = Alert(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        source=request.source,
        external_id=request.external_id,
        title=request.title,
        description=request.description,
        severity=request.severity,
        status=AlertStatus.OPEN,
        fingerprint=fingerprint,
        labels=request.labels,
        annotations=request.annotations,
        raw_data=request.model_dump(),
        fired_at=datetime.now(timezone.utc),
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    # Publish alert event
    event = AlertEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.ALERT_INGESTED,
        tenant_id=alert.tenant_id,
        timestamp=datetime.utcnow(),
        alert_id=alert.id,
        severity=alert.severity.value,
        title=alert.title,
        source=alert.source,
        fingerprint=alert.fingerprint,
        labels=alert.labels,
    )
    
    with EventProducer(settings.kafka) as producer:
        await producer.publish("alerts.ingested", event)
    
    # Trigger auto-investigation for high-severity alerts
    background_tasks.add_task(trigger_investigation, alert, db)
    
    logger.info("alert_created", alert_id=alert.id, severity=alert.severity)
    
    return AlertResponse(
        id=alert.id,
        tenant_id=alert.tenant_id,
        source=alert.source,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        fingerprint=alert.fingerprint,
        incident_id=alert.incident_id,
        fired_at=alert.fired_at,
        created_at=alert.created_at,
    )


@app.get("/api/v1/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get alert by ID."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return AlertResponse(
        id=alert.id,
        tenant_id=alert.tenant_id,
        source=alert.source,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        fingerprint=alert.fingerprint,
        incident_id=alert.incident_id,
        fired_at=alert.fired_at,
        created_at=alert.created_at,
    )


@app.get("/api/v1/alerts", response_model=list[AlertResponse])
async def list_alerts(
    tenant_id: Optional[str] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List alerts."""
    query = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    
    if tenant_id:
        query = query.where(Alert.tenant_id == tenant_id)
    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        AlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            source=alert.source,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            status=alert.status,
            fingerprint=alert.fingerprint,
            incident_id=alert.incident_id,
            fired_at=alert.fired_at,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@app.post("/api/v1/incidents", response_model=IncidentResponse)
async def create_incident(
    request: IncidentCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new incident."""
    # Generate incident number
    result = await db.execute(
        select(Incident)
        .where(Incident.tenant_id == request.tenant_id)
        .order_by(desc(Incident.created_at))
        .limit(1)
    )
    last_incident = result.scalar_one_or_none()
    
    if last_incident:
        last_num = int(last_incident.number.split("-")[-1])
        incident_number = f"INC-{last_num + 1:06d}"
    else:
        incident_number = "INC-000001"
    
    incident = Incident(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        number=incident_number,
        title=request.title,
        description=request.description,
        priority=request.priority,
        state=IncidentState.NEW,
        category=request.category,
        affected_services=[],
        extra_data={},
    )
    
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    
    logger.info("incident_created", incident_id=incident.id, number=incident.number)
    
    return IncidentResponse(
        id=incident.id,
        tenant_id=incident.tenant_id,
        number=incident.number,
        title=incident.title,
        description=incident.description,
        priority=incident.priority,
        state=incident.state,
        affected_services=incident.affected_services,
        opened_at=incident.opened_at,
    )


@app.get("/api/v1/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get incident by ID."""
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return IncidentResponse(
        id=incident.id,
        tenant_id=incident.tenant_id,
        number=incident.number,
        title=incident.title,
        description=incident.description,
        priority=incident.priority,
        state=incident.state,
        affected_services=incident.affected_services,
        opened_at=incident.opened_at,
    )


@app.get("/api/v1/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    tenant_id: Optional[str] = None,
    state: Optional[IncidentState] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List incidents."""
    query = select(Incident).order_by(desc(Incident.opened_at)).limit(limit)
    
    if tenant_id:
        query = query.where(Incident.tenant_id == tenant_id)
    if state:
        query = query.where(Incident.state == state)
    
    result = await db.execute(query)
    incidents = result.scalars().all()
    
    return [
        IncidentResponse(
            id=incident.id,
            tenant_id=incident.tenant_id,
            number=incident.number,
            title=incident.title,
            description=incident.description,
            priority=incident.priority,
            state=incident.state,
            affected_services=incident.affected_services,
            opened_at=incident.opened_at,
        )
        for incident in incidents
    ]


@app.post("/api/v1/webhooks/pagerduty")
async def pagerduty_webhook(payload: dict):
    """PagerDuty webhook handler."""
    logger.info("pagerduty_webhook_received", payload=payload)
    # TODO: Parse PagerDuty payload and create alerts
    return {"status": "received"}


@app.post("/api/v1/webhooks/opsgenie")
async def opsgenie_webhook(payload: dict):
    """OpsGenie webhook handler."""
    logger.info("opsgenie_webhook_received", payload=payload)
    # TODO: Parse OpsGenie payload and create alerts
    return {"status": "received"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "alert-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
