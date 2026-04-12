"""Dispatcher node - runs agents in parallel."""

import asyncio
from datetime import datetime
from typing import List
from uuid import UUID

from crewai import Crew, Task
from langchain_core.language_models import BaseChatModel

from app.adapters.registry import ProviderRegistry
from app.agents.models import AgentResult, AgentType
from app.agents.specialists import (
    CodeAgent,
    InfraAgent,
    LogsAgent,
    MetricsAgent,
    SecurityAgent,
)
from app.core.logging import get_logger
from app.orchestration.state import InvestigationState, InvestigationStatus

logger = get_logger(__name__)


class DispatcherNode:
    """Dispatches and runs selected agents in parallel.

    Creates CrewAI crew with selected agents and executes them
    concurrently with timeout handling.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        registry: ProviderRegistry,
        agent_timeout: int = 120,
    ) -> None:
        """Initialize dispatcher node.

        Args:
            llm: Language model for agents
            registry: Provider registry for tools
            agent_timeout: Timeout per agent in seconds
        """
        self.llm = llm
        self.registry = registry
        self.agent_timeout = agent_timeout

        logger.info(
            "dispatcher_node_initialized",
            agent_timeout=agent_timeout,
        )

    async def __call__(self, state: InvestigationState) -> InvestigationState:
        """Execute dispatcher node.

        Args:
            state: Current investigation state

        Returns:
            Updated state with agent_results
        """
        try:
            logger.info(
                "dispatcher_started",
                investigation_id=state.get("investigation_id"),
                selected_agents=[a.value for a in state.get("selected_agents", [])],
            )

            # Update status
            state["status"] = InvestigationStatus.INVESTIGATING

            # Get selected agents
            selected_agents = state.get("selected_agents", [])
            if not selected_agents:
                logger.warning(
                    "no_agents_selected",
                    investigation_id=state.get("investigation_id"),
                )
                state["agent_results"] = []
                return state

            # Create agent instances
            tenant_id = UUID(state["tenant_id"])
            agent_instances = self._create_agent_instances(
                tenant_id,
                selected_agents,
            )

            # Check if we have any agent instances
            if not agent_instances:
                logger.error(
                    "no_agent_instances_created",
                    investigation_id=state.get("investigation_id"),
                )
                state["agent_results"] = [
                    AgentResult(
                        agent_type=agent_type,
                        success=False,
                        analysis={},
                        evidence=[],
                        duration_seconds=0.0,
                        providers_queried=[],
                        error="Failed to create agent instance",
                    )
                    for agent_type in selected_agents
                ]
                return state

            # Create tasks for each agent
            tasks = self._create_agent_tasks(state, agent_instances)

            # Create crew
            crew = Crew(
                agents=[agent.agent for agent in agent_instances.values()],
                tasks=tasks,
                verbose=True,
            )

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(crew.kickoff),
                    timeout=self.agent_timeout * len(selected_agents),
                )

                # Parse results
                agent_results = self._parse_crew_results(
                    result,
                    agent_instances,
                    selected_agents,
                )

            except asyncio.TimeoutError:
                logger.error(
                    "crew_execution_timeout",
                    investigation_id=state.get("investigation_id"),
                    timeout=self.agent_timeout * len(selected_agents),
                )

                # Create timeout results
                agent_results = [
                    AgentResult(
                        agent_type=agent_type,
                        success=False,
                        analysis={},
                        evidence=[],
                        duration_seconds=self.agent_timeout,
                        providers_queried=[],
                        error="Agent execution timed out",
                    )
                    for agent_type in selected_agents
                ]

            state["agent_results"] = agent_results

            # Log summary
            successful = sum(1 for r in agent_results if r.success)
            logger.info(
                "dispatcher_completed",
                investigation_id=state.get("investigation_id"),
                total_agents=len(agent_results),
                successful=successful,
                failed=len(agent_results) - successful,
            )

            return state

        except Exception as e:
            logger.error(
                "dispatcher_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            state["error"] = f"Agent dispatch failed: {str(e)}"
            state["status"] = InvestigationStatus.FAILED
            return state

    def _create_agent_instances(
        self,
        tenant_id: UUID,
        selected_agents: List[AgentType],
    ) -> dict:
        """Create agent instances.

        Args:
            tenant_id: Tenant UUID
            selected_agents: List of agent types to create

        Returns:
            Dict mapping agent type to agent instance
        """
        instances = {}

        for agent_type in selected_agents:
            try:
                if agent_type == AgentType.METRICS:
                    instances[agent_type] = MetricsAgent(
                        tenant_id, self.registry, self.llm
                    )
                elif agent_type == AgentType.LOGS:
                    instances[agent_type] = LogsAgent(
                        tenant_id, self.registry, self.llm
                    )
                elif agent_type == AgentType.INFRA:
                    instances[agent_type] = InfraAgent(
                        tenant_id, self.registry, self.llm
                    )
                elif agent_type == AgentType.CODE:
                    instances[agent_type] = CodeAgent(
                        tenant_id, self.registry, self.llm
                    )
                elif agent_type == AgentType.SECURITY:
                    instances[agent_type] = SecurityAgent(
                        tenant_id, self.registry, self.llm
                    )

                logger.debug(
                    "agent_instance_created",
                    agent_type=agent_type.value,
                )

            except Exception as e:
                logger.error(
                    "agent_creation_failed",
                    agent_type=agent_type.value,
                    error=str(e),
                )

        return instances

    def _create_agent_tasks(
        self,
        state: InvestigationState,
        agent_instances: dict,
    ) -> List[Task]:
        """Create tasks for each agent.

        Args:
            state: Investigation state
            agent_instances: Agent instances

        Returns:
            List of CrewAI tasks
        """
        incident = state["incident"]
        service_name = state.get("service_name", "unknown")

        tasks = []

        for agent_type, agent_instance in agent_instances.items():
            # Create task description based on agent type
            description = self._create_task_description(
                agent_type,
                incident,
                service_name,
            )

            task = Task(
                description=description,
                agent=agent_instance.agent,
                expected_output=f"{agent_type.value.title()}Analysis JSON with findings",
            )

            tasks.append(task)

        return tasks

    def _create_task_description(
        self,
        agent_type: AgentType,
        incident: any,
        service_name: str,
    ) -> str:
        """Create task description for agent.

        Args:
            agent_type: Type of agent
            incident: ServiceNow incident
            service_name: Service name

        Returns:
            Task description
        """
        base = f"""
Investigate the following incident:

Service: {service_name}
Incident: {incident.number}
Title: {incident.short_description}
Description: {incident.description}
Opened: {incident.opened_at}
Priority: {incident.priority}

Your task: Analyze this incident from your area of expertise.
        """.strip()

        if agent_type == AgentType.METRICS:
            return f"""{base}

Focus on:
1. Retrieve metrics around the incident time
2. Identify anomalies (spikes, drops, unusual patterns)
3. Compare to baseline values
4. Assess correlation with incident timing
5. Provide confidence score

Use get_metrics tool to retrieve time series data.
            """.strip()

        elif agent_type == AgentType.LOGS:
            return f"""{base}

Focus on:
1. Search logs for errors around incident time
2. Identify error patterns and stack traces
3. Find first occurrence of errors
4. Look for root cause signals
5. Assess frequency and severity

Use query_logs tool to search for errors and patterns.
            """.strip()

        elif agent_type == AgentType.INFRA:
            return f"""{base}

Focus on:
1. Check resource status (running, healthy?)
2. Check health status (degraded, unhealthy?)
3. Identify capacity issues
4. Review recent infrastructure changes
5. Assess dependency health

Use get_resources and get_recent_changes tools.
            """.strip()

        elif agent_type == AgentType.CODE:
            return f"""{base}

Focus on:
1. Identify recent deployments
2. Check timing correlation with incident
3. Analyze what changed
4. Assess likelihood each change caused incident
5. Provide confidence assessment

Use get_recent_changes tool to see deployments.
            """.strip()

        elif agent_type == AgentType.SECURITY:
            return f"""{base}

Focus on:
1. Check for IAM/permission changes
2. Look for unusual API activity
3. Identify failed authentication attempts
4. Review security group changes
5. Determine if this is a security incident

Use get_audit_events and get_resources tools.
            """.strip()

        return base

    def _parse_crew_results(
        self,
        crew_result: any,
        agent_instances: dict,
        selected_agents: List[AgentType],
    ) -> List[AgentResult]:
        """Parse CrewAI results into AgentResult objects.

        Args:
            crew_result: Result from crew.kickoff()
            agent_instances: Agent instances
            selected_agents: Selected agent types

        Returns:
            List of AgentResult objects
        """
        agent_results = []

        # CrewAI returns a string result
        # In production, you'd parse structured output from each agent
        # For now, create basic results

        for agent_type in selected_agents:
            try:
                # Extract agent-specific output
                # This is simplified - in production, use structured output
                result = AgentResult(
                    agent_type=agent_type,
                    success=True,
                    analysis={"raw_output": str(crew_result)},
                    evidence=[
                        f"{agent_type.value} agent completed investigation"
                    ],
                    duration_seconds=60.0,  # Placeholder
                    providers_queried=[],  # Will be populated by actual tool execution
                    error=None,
                )

                agent_results.append(result)

            except Exception as e:
                logger.error(
                    "agent_result_parse_failed",
                    agent_type=agent_type.value,
                    error=str(e),
                )

                # Create error result
                result = AgentResult(
                    agent_type=agent_type,
                    success=False,
                    analysis={},
                    evidence=[],
                    duration_seconds=0.0,
                    providers_queried=[],
                    error=str(e),
                )

                agent_results.append(result)

        return agent_results
