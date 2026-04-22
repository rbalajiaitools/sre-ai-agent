"""Notification Service - Multi-channel notifications."""

import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import init_db, get_db_session
from shared.models import Notification, NotificationChannel, NotificationStatus
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("notification_service_startup", port=8007)
    init_db(settings.database)
    yield
    logger.info("notification_service_shutdown")


app = FastAPI(
    title="Notification Service",
    description="Multi-channel notification dispatch",
    version="0.1.0",
    lifespan=lifespan,
)


class NotificationCreate(BaseModel):
    tenant_id: str
    channel: NotificationChannel
    recipient: str
    subject: Optional[str] = None
    message: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None


@app.post("/api/v1/notifications")
async def send_notification(
    request: NotificationCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Send notification."""
    notification = Notification(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        channel=request.channel,
        recipient=request.recipient,
        subject=request.subject,
        message=request.message,
        context_type=request.context_type,
        context_id=request.context_id,
        status=NotificationStatus.SENT,
        sent_at=datetime.now(timezone.utc),
        extra_data={},
    )
    
    db.add(notification)
    await db.commit()
    
    logger.info("notification_sent", notification_id=notification.id, channel=notification.channel)
    
    return {"id": notification.id, "status": "sent"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "notification-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
