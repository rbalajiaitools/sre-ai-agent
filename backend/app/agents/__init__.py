"""Agent framework for SRE AI Agent platform.

This module contains specialist agents for parallel execution.
"""

# Only export the parallel executor, not the old CrewAI agents
from app.agents.parallel_executor import ParallelAgentExecutor

__all__ = [
    "ParallelAgentExecutor",
]

