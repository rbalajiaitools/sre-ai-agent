"""Main API router configuration."""

from fastapi import APIRouter

from app.api import health, demo, real, topology, dashboard, simulation, knowledge
from app.api import integrations, incidents

api_router = APIRouter()

# Include sub-routers
# IMPORTANT: Order matters! More specific routes should come before general ones
api_router.include_router(health.router)
api_router.include_router(integrations.router)  # Integration management (ServiceNow, AWS)
api_router.include_router(incidents.router)  # Incident management
api_router.include_router(real.router)  # Investigations and chat (TODO: split further)
api_router.include_router(topology.router)  # Real topology discovery
api_router.include_router(dashboard.router)  # Dashboard with real data
api_router.include_router(knowledge.router)  # Knowledge base
api_router.include_router(simulation.router)  # Simulation for testing
api_router.include_router(demo.router)  # Demo endpoints (fallback)
# Note: Orchestration API has pydantic v1/v2 dependency conflicts with langchain/langgraph
# The full multi-agent orchestration system exists but requires dependency resolution
# For now, we use a simplified AI investigation in the real.py endpoints

