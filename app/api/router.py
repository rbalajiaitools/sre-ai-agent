"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health
# from app.orchestration import api as orchestration_api

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
# api_router.include_router(orchestration_api.router, prefix="", tags=["investigations"])
