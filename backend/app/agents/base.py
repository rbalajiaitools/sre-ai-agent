"""Base agent and shared agent utilities.

This module provides the base class and utilities for all specialist agents.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.models import AgentType


class BaseAgent:
    """Base class for all specialist agents.

    Provides common functionality for agent initialization and execution.
    All specialist agents should inherit from this class.

    CRITICAL: No agent may import provider-specific modules (boto3, azure-sdk, etc.).
    All provider interaction happens through BaseAdapter via the registry.
    """

    def __init__(
        self,
        agent_type: AgentType,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Any],
        verbose: bool = True,
        allow_delegation: bool = False,
    ) -> None:
        """Initialize base agent.

        Args:
            agent_type: Type of agent
            tenant_id: Tenant UUID
            registry: Provider registry
            llm: Language model
            role: Agent role
            goal: Agent goal
            backstory: Agent backstory
            tools: List of tools
            verbose: Whether to enable verbose output
            allow_delegation: Whether agent can delegate to others
        """
        self.agent_type = agent_type
        self.tenant_id = tenant_id
        self.registry = registry
        self.llm = llm
        self.tools = tools

        # Create CrewAI agent
        self.agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            verbose=verbose,
            allow_delegation=allow_delegation,
        )

    def analyze(
        self,
        service_name: str,
        incident_time: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze the service for the incident.

        This method should be overridden by specialist agents.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze()")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information.

        Returns:
            Dict with agent metadata
        """
        return {
            "agent_type": self.agent_type.value,
            "role": self.agent.role,
            "goal": self.agent.goal,
            "tools": [tool.name for tool in self.tools],
            "allow_delegation": self.agent.allow_delegation,
        }


class AgentExecutionContext:
    """Context for agent execution.

    Provides shared context and utilities for agents during execution.
    """

    def __init__(
        self,
        tenant_id: UUID,
        service_name: str,
        incident_time: str,
        incident_description: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize execution context.

        Args:
            tenant_id: Tenant UUID
            service_name: Service being investigated
            incident_time: When incident occurred
            incident_description: Description of incident
            additional_context: Additional context
        """
        self.tenant_id = tenant_id
        self.service_name = service_name
        self.incident_time = incident_time
        self.incident_description = incident_description
        self.additional_context = additional_context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.

        Returns:
            Dict representation
        """
        return {
            "tenant_id": str(self.tenant_id),
            "service_name": self.service_name,
            "incident_time": self.incident_time,
            "incident_description": self.incident_description,
            "additional_context": self.additional_context,
        }

    def get_context_string(self) -> str:
        """Get context as formatted string for agent prompts.

        Returns:
            Formatted context string
        """
        return f"""
Service: {self.service_name}
Incident Time: {self.incident_time}
Description: {self.incident_description}

Additional Context:
{self._format_additional_context()}
        """.strip()

    def _format_additional_context(self) -> str:
        """Format additional context for display.

        Returns:
            Formatted string
        """
        if not self.additional_context:
            return "None"

        lines = []
        for key, value in self.additional_context.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)


def create_task_description(
    agent_type: AgentType,
    context: AgentExecutionContext,
) -> str:
    """Create task description for an agent.

    Args:
        agent_type: Type of agent
        context: Execution context

    Returns:
        Task description string
    """
    base_context = f"""
Investigate the following incident:

{context.get_context_string()}

Your task is to analyze this incident from your area of expertise.
    """.strip()

    # Add agent-specific instructions
    if agent_type == AgentType.METRICS:
        return f"""{base_context}

Focus on:
1. Retrieve metrics for the service around the incident time
2. Identify any anomalies (spikes, drops, unusual patterns)
3. Compare to baseline/normal values
4. Assess correlation with incident timing
5. Provide confidence score for your findings

Use the get_metrics tool to retrieve time series data.
Look at error rates, latency, CPU, memory, and throughput.
        """.strip()

    elif agent_type == AgentType.LOGS:
        return f"""{base_context}

Focus on:
1. Search logs for errors and exceptions around incident time
2. Identify error patterns and stack traces
3. Find the first occurrence of errors
4. Look for root cause signals in error messages
5. Assess frequency and severity of errors

Use the query_logs tool to search for errors, exceptions, and patterns.
Start with broad searches (ERROR, Exception) then narrow down.
        """.strip()

    elif agent_type == AgentType.INFRA:
        return f"""{base_context}

Focus on:
1. Check resource status (are things running?)
2. Check health status (healthy, degraded, unhealthy)
3. Identify capacity issues
4. Review recent infrastructure changes
5. Assess dependency health

Use get_resources to check infrastructure state.
Use get_recent_changes to see what changed recently.
        """.strip()

    elif agent_type == AgentType.CODE:
        return f"""{base_context}

Focus on:
1. Identify recent deployments
2. Check timing correlation with incident
3. Analyze what changed in each deployment
4. Assess likelihood each change caused the incident
5. Provide confidence in your assessment

Use get_recent_changes to see deployments and code changes.
Pay special attention to changes within 1 hour of incident.
        """.strip()

    elif agent_type == AgentType.SECURITY:
        return f"""{base_context}

Focus on:
1. Check for IAM/permission changes
2. Look for unusual API activity
3. Identify failed authentication attempts
4. Review security group changes
5. Determine if this is a security incident

Use get_audit_events to see security-related activities.
Use get_resources to check resource access patterns.
        """.strip()

    return base_context


def format_agent_output(
    agent_type: AgentType,
    raw_output: str,
) -> Dict[str, Any]:
    """Format agent output into structured result.

    Args:
        agent_type: Type of agent
        raw_output: Raw output from agent

    Returns:
        Structured result dictionary
    """
    # This is a simple implementation
    # In production, you might parse the output more carefully
    return {
        "agent_type": agent_type.value,
        "raw_output": raw_output,
        "summary": raw_output[:500] if len(raw_output) > 500 else raw_output,
    }


def merge_agent_results(
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Merge results from multiple agents.

    Args:
        results: List of agent results

    Returns:
        Merged results
    """
    merged = {
        "agents_run": [r.get("agent_type") for r in results],
        "total_agents": len(results),
        "successful_agents": sum(1 for r in results if r.get("success", False)),
        "all_evidence": [],
        "all_providers_queried": set(),
    }

    for result in results:
        # Collect evidence
        if "evidence" in result:
            merged["all_evidence"].extend(result["evidence"])

        # Collect providers
        if "providers_queried" in result:
            merged["all_providers_queried"].update(result["providers_queried"])

    merged["all_providers_queried"] = list(merged["all_providers_queried"])

    return merged
