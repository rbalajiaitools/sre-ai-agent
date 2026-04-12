"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health, demo
from app.orchestration.api import router as orchestration_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(demo.router)  # Keep demo/settings endpoints for now
api_router.include_router(orchestration_router, tags=["investigations"])  # Enable real investigation endpoints
