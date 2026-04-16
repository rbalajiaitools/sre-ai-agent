"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health, demo, real, topology, dashboard, simulation, knowledge

api_router = APIRouter()

# Include sub-routers
# IMPORTANT: Order matters! More specific routes should come before general ones
api_router.include_router(health.router)
api_router.include_router(real.router)  # Real ServiceNow and AWS integration
api_router.include_router(topology.router)  # Real topology discovery (must come before demo)
api_router.include_router(dashboard.router)  # Dashboard with real data
api_router.include_router(knowledge.router)  # Knowledge base
api_router.include_router(simulation.router)  # Simulation for testing
api_router.include_router(demo.router)  # Demo endpoints for other features (fallback)
# Note: Orchestration API has pydantic v1/v2 dependency conflicts with langchain/langgraph
# The full multi-agent orchestration system exists but requires dependency resolution
# For now, we use a simplified AI investigation in the real.py endpoints
