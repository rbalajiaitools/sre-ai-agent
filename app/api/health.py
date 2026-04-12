"""Health check endpoint."""

from typing import Dict

from fastapi import APIRouter, status

from app.core.logging import get_logger
from app.models.base import BaseSchema

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseSchema):
    """Health check response model."""

    status: str
    version: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the service is running and healthy",
)
async def health_check() -> HealthResponse:
    """Perform health check.

    Returns:
        HealthResponse with service status
    """
    logger.info("health_check_requested")

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment="development",
    )
