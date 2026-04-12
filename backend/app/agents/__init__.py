"""Agent framework for SRE AI Agent platform.

This module contains specialist agents built with CrewAI and LangChain.
Agents use tools that wrap adapter calls - no provider-specific code allowed.

Architecture:
    - BaseAgent: Base class for all specialist agents
    - BaseAgentTool: Wraps adapter calls via registry
    - Specialist Agents: Domain-specific investigation agents
    - Tools: Metrics, Logs, Resources, Changes, Security

CRITICAL RULE: No agent may import provider-specific modules (boto3, azure-sdk, etc.).
All provider interaction happens through BaseAdapter via the registry.
"""

from app.agents.base import (
    AgentExecutionContext,
    BaseAgent,
    create_task_description,
    format_agent_output,
    merge_agent_results,
)
from app.agents.models import (
    AgentInvestigationRequest,
    AgentResult,
    AgentType,
    InvestigationResult,
)
from app.agents.tools import (
    GetAuditEventsTool,
    GetMetricsTool,
    GetRecentChangesTool,
    GetResourcesTool,
    QueryLogsTool,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentExecutionContext",
    "create_task_description",
    "format_agent_output",
    "merge_agent_results",
    # Models
    "AgentType",
    "AgentInvestigationRequest",
    "AgentResult",
    "InvestigationResult",
    # Tools
    "GetMetricsTool",
    "QueryLogsTool",
    "GetResourcesTool",
    "GetRecentChangesTool",
    "GetAuditEventsTool",
]
