"""Security specialist agent."""

from typing import Any, Dict
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.tools import GetAuditEventsTool, GetResourcesTool


class SecurityAgent:
    """Specialist agent for security analysis.

    Focuses on security-related causes and compliance issues.
    """

    def __init__(
        self,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
    ) -> None:
        """Initialize security agent.

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
            GetAuditEventsTool(tenant_id=tenant_id, registry=registry),
            GetResourcesTool(tenant_id=tenant_id, registry=registry),
        ]

        # Create CrewAI agent
        self.agent = Agent(
            role="Security and Compliance Analyst",
            goal="""Identify security-related causes for the incident.
            
            Investigate:
            1. IAM permission changes
            2. Unusual API call patterns
            3. Credential issues
            4. Policy violations
            5. Security group changes
            6. Failed authentication attempts
            
            Your analysis should determine:
            - Is this a security incident?
            - What security-related changes occurred?
            - Are there permission or access issues?
            - Is there unusual or suspicious activity?
            """,
            backstory="""You are a security expert with 10 years of experience in 
            cloud security, IAM, and incident response. You have a keen eye for 
            spotting security issues and understanding their impact.
            
            You know that:
            - Permission errors often stem from IAM changes
            - Unusual API patterns can indicate attacks or misconfigurations
            - Credential rotation can break applications
            - Security group changes affect network access
            - Failed auth attempts might indicate credential issues
            - Policy changes can inadvertently block legitimate access
            
            You understand the difference between security incidents (attacks, breaches) 
            and security-related operational issues (permission errors, credential problems).
            
            You always check:
            - Recent IAM role/policy changes
            - Security group modifications
            - Unusual API call patterns
            - Failed authentication attempts
            - Resource access patterns
            
            You provide clear assessments of whether this is a security incident or 
            a security-related operational issue, and what the root cause appears to be.
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
        """Analyze security aspects for the service.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        return {
            "agent_type": "security",
            "service_name": service_name,
            "incident_time": incident_time,
        }
