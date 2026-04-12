"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health, demo

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(demo.router)
# Note: Real orchestration API requires redis, neo4j, and other dependencies
# api_router.include_router(orchestration_router, tags=["investigations"])
