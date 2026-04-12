"""Metrics specialist agent."""

from typing import Any, Dict, List
from uuid import UUID

from crewai import Agent
from langchain.llms.base import BaseLLM

from app.adapters.registry import ProviderRegistry
from app.agents.tools import GetMetricsTool, GetResourcesTool


class MetricsAgent:
    """Specialist agent for metrics analysis.

    Focuses on identifying anomalies in metrics that correlate with incidents.
    """

    def __init__(
        self,
        tenant_id: UUID,
        registry: ProviderRegistry,
        llm: BaseLLM,
    ) -> None:
        """Initialize metrics agent.

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
            GetMetricsTool(tenant_id=tenant_id, registry=registry),
            GetResourcesTool(tenant_id=tenant_id, registry=registry),
        ]

        # Create CrewAI agent
        self.agent = Agent(
            role="Senior Metrics Analyst",
            goal="""Identify anomalies in metrics that correlate with the incident timeframe. 
            Focus on: error rates, latency percentiles (p50, p95, p99), CPU/memory utilization, 
            request throughput, and connection pool usage.
            
            Your analysis should:
            1. Identify which metrics show anomalous behavior
            2. Determine when the anomaly started
            3. Compare to baseline/normal values
            4. Assess correlation with incident timing
            5. Provide confidence score for findings
            """,
            backstory="""You are an expert in observability and performance analysis with 
            15 years of experience. You have deep knowledge of system metrics, performance 
            patterns, and how to identify anomalies that indicate root causes.
            
            You understand that:
            - Sudden spikes in error rates often indicate code or config issues
            - Gradual increases in latency suggest capacity problems
            - Memory leaks show as steadily increasing memory usage
            - CPU spikes can indicate inefficient code or traffic surges
            - Connection pool exhaustion shows as maxed out connections
            
            You always look at multiple metrics together to understand the full picture.
            You know that correlation doesn't always mean causation, so you provide 
            confidence scores based on the strength of the evidence.
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
        """Analyze metrics for the service.

        Args:
            service_name: Service to analyze
            incident_time: When incident occurred
            context: Additional context

        Returns:
            Analysis results
        """
        # This would be called by the orchestrator with a CrewAI Task
        # For now, return structure
        return {
            "agent_type": "metrics",
            "service_name": service_name,
            "incident_time": incident_time,
        }
