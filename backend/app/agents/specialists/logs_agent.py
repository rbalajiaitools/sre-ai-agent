"""Logs specialist agent."""

from typing import Any, Dict
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.tools import QueryLogsTool


class LogsAgent:
    """Specialist agent for log analysis.

    Focuses on finding error patterns and root cause signals in logs.
    """

    def __init__(
        self,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
    ) -> None:
        """Initialize logs agent.

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
            QueryLogsTool(tenant_id=tenant_id, registry=registry),
        ]

        # Create CrewAI agent
        self.agent = Agent(
            role="Log Investigation Specialist",
            goal="""Find error patterns, stack traces, and root cause signals in logs.
            
            Look for:
            1. Exceptions and stack traces
            2. Connection errors and timeouts
            3. Out of memory (OOM) signals
            4. Database errors
            5. Repeated error patterns
            6. The first occurrence of errors
            
            Your analysis should identify:
            - What errors occurred
            - When they first appeared
            - How frequently they occur
            - Any patterns or correlations
            - Root cause signals in error messages
            """,
            backstory="""You are a master at reading logs and finding needles in haystacks. 
            With 12 years of experience in production systems, you can quickly identify 
            the critical errors that matter and filter out noise.
            
            You know that:
            - The first error is often the root cause
            - Stack traces reveal the code path that failed
            - Connection timeouts suggest network or capacity issues
            - OOM errors indicate memory leaks or insufficient resources
            - Repeated patterns suggest systematic issues
            - Error messages often contain the root cause
            
            You always look for the timeline of errors - when did they start, how did 
            they progress. You understand that cascading failures can create many errors, 
            but the root cause is usually in the first few errors.
            
            You're skilled at pattern recognition and can identify similar errors even 
            when the exact messages differ slightly.
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
        """Analyze logs for the service.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        return {
            "agent_type": "logs",
            "service_name": service_name,
            "incident_time": incident_time,
        }
