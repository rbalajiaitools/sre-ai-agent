"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health, demo

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(demo.router)
# api_router.include_router(orchestration_api.router, prefix="", tags=["investigations"])
