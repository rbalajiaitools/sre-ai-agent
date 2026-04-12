"""Code/deployment specialist agent."""

from typing import Any, Dict
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.tools import GetRecentChangesTool


class CodeAgent:
    """Specialist agent for deployment and code change analysis.

    Focuses on identifying if recent deployments or code changes caused the incident.
    """

    def __init__(
        self,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
    ) -> None:
        """Initialize code agent.

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
            GetRecentChangesTool(tenant_id=tenant_id, registry=registry),
        ]

        # Create CrewAI agent
        self.agent = Agent(
            role="Deployment and Change Analyst",
            goal="""Identify if a recent deployment or code change caused this incident.
            
            Investigate:
            1. What deployments happened recently?
            2. When were they deployed?
            3. Does the timing correlate with the incident?
            4. What changed in each deployment?
            5. Are there any obvious issues in the changes?
            
            Your analysis should determine:
            - Which deployment (if any) likely caused the incident
            - How strong is the correlation (timing-based)
            - What changed that could cause the symptoms
            - Confidence level in the assessment
            """,
            backstory="""You are a deployment expert who has seen countless incidents 
            caused by code changes. You have 8 years of experience in CI/CD, release 
            management, and incident response.
            
            You know that:
            - Most incidents are caused by recent changes
            - Deployments within 1 hour of incident are highly suspicious
            - Configuration changes can be as impactful as code changes
            - Feature flags can introduce issues when toggled
            - Database migrations can cause performance problems
            - Dependency updates sometimes break compatibility
            
            You understand the importance of timing correlation. If a deployment happened 
            5 minutes before the incident started, that's a strong signal. If it was 
            3 days ago, it's less likely to be the cause.
            
            You always look at what actually changed - new features, bug fixes, config 
            updates, dependency versions. You can often spot obvious issues like:
            - Removing error handling
            - Changing timeouts or limits
            - Modifying critical business logic
            - Updating database queries
            
            You provide clear assessments with confidence levels based on the evidence.
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
        """Analyze deployments and changes for the service.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        return {
            "agent_type": "code",
            "service_name": service_name,
            "incident_time": incident_time,
        }
