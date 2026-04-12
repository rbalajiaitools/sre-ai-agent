"""Infrastructure specialist agent."""

from typing import Any, Dict
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.tools import GetRecentChangesTool, GetResourcesTool


class InfraAgent:
    """Specialist agent for infrastructure analysis.

    Focuses on infrastructure health, capacity, and recent changes.
    """

    def __init__(
        self,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
    ) -> None:
        """Initialize infrastructure agent.

        Args:
            tenant_id: Tenant UUID
            registry: Provider registry
            llm: Language model
        """
        self.tenant_id = tenant_id
        self.registry = registry
        self.llm = llm

        # Initialize tools
        self.tools = [
            GetResourcesTool(tenant_id=tenant_id, registry=registry),
            GetRecentChangesTool(tenant_id=tenant_id, registry=registry),
        ]

        # Create CrewAI agent
        self.agent = Agent(
            role="Infrastructure Reliability Engineer",
            goal="""Assess infrastructure health and identify issues that could cause 
            the reported symptoms.
            
            Check for:
            1. Resource status (are containers/instances running?)
            2. Health status (healthy, degraded, unhealthy)
            3. Capacity issues (at limits, need scaling)
            4. Recent infrastructure changes
            5. Dependency issues
            
            Your analysis should determine:
            - Are all required resources running?
            - Are any resources unhealthy or degraded?
            - Is the system at capacity?
            - Did recent infrastructure changes cause issues?
            - Are there dependency problems?
            """,
            backstory="""You are an infrastructure expert with deep knowledge of cloud 
            platforms, containers, databases, and distributed systems. You have 10 years 
            of experience running production systems at scale.
            
            You understand that:
            - Stopped or failed instances cause service unavailability
            - Degraded health often precedes complete failures
            - Capacity limits cause performance degradation
            - Autoscaling issues can leave systems under-provisioned
            - Database connection limits cause application errors
            - Network issues affect service communication
            - Recent infrastructure changes are common culprits
            
            You always check the basics first: are things running, are they healthy, 
            do they have enough capacity. You know that infrastructure issues often 
            manifest as application errors, so you look for the underlying cause.
            
            You pay special attention to recent changes - scaling events, instance 
            replacements, configuration updates - as these often introduce issues.
            """,
            tools=self.tools,
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    def analyze(
        self,
        service_name: str,
        incident_time: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze infrastructure for the service.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        return {
            "agent_type": "infra",
            "service_name": service_name,
            "incident_time": incident_time,
        }
