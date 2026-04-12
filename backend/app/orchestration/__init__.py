"""LangGraph orchestration engine for SRE AI Agent platform.

This module provides the orchestration layer that coordinates:
- Incident investigation planning
- Multi-agent execution
- Root cause analysis
- Resolution generation
- ServiceNow integration

Architecture:
    - StateGraph: LangGraph workflow definition
    - Nodes: Planner, Dispatcher, RCA, Resolver
    - Router: Conditional edge routing
    - API: FastAPI endpoints for triggering investigations
"""

from app.orchestration.api import router as orchestration_router
from app.orchestration.graph import InvestigationGraph
from app.orchestration.state import (
    InvestigationState,
    InvestigationStatus,
    RCAResult,
    ResolutionOutput,
)

__all__ = [
    # Core
    "InvestigationGraph",
    # State
    "InvestigationState",
    "InvestigationStatus",
    "RCAResult",
    "ResolutionOutput",
    # API
    "orchestration_router",
]
