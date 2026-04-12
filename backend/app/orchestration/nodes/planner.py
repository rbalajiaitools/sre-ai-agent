"""Planner node - decides which agents to run."""

from datetime import datetime
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.models import AgentType
from app.core.logging import get_logger
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.memory import IncidentMemory
from app.orchestration.state import InvestigationState, InvestigationStatus

logger = get_logger(__name__)


# Planner system prompt
PLANNER_SYSTEM_PROMPT = """You are an expert SRE incident planner. Your job is to analyze an incident and decide which specialist agents should investigate it.

Available agents:
- METRICS: Analyzes metrics (CPU, memory, error rates, latency) for anomalies
- LOGS: Searches logs for errors, exceptions, and patterns
- INFRA: Checks infrastructure health, capacity, and recent changes
- CODE: Investigates recent deployments and code changes
- SECURITY: Checks for security-related issues (IAM, permissions, access)

Guidelines:
1. ALWAYS include INFRA and METRICS - they provide baseline context
2. Include LOGS if description mentions: error, exception, timeout, crash, failure, down
3. Include CODE if description mentions: deployment, release, change, upgrade, rollout, version
4. Include SECURITY if description mentions: permission, auth, access, security, denied, unauthorized
5. Consider the time of day and recent deployment windows
6. Consider affected resource types
7. Consider similar past incidents

Your response must be a JSON object with:
{
    "selected_agents": ["METRICS", "LOGS", ...],
    "reasoning": "Brief explanation of why these agents were selected"
}
"""


class PlannerNode:
    """Plans investigation by selecting appropriate agents.

    Analyzes the incident and decides which specialist agents should
    investigate based on incident description, affected resources,
    and historical patterns.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        knowledge_graph: KnowledgeGraph,
        incident_memory: IncidentMemory,
    ) -> None:
        """Initialize planner node.

        Args:
            llm: Language model for planning
            knowledge_graph: Knowledge graph for topology
            incident_memory: Incident memory for similar incidents
        """
        self.llm = llm
        self.knowledge_graph = knowledge_graph
        self.incident_memory = incident_memory

        logger.info("planner_node_initialized")

    async def __call__(self, state: InvestigationState) -> InvestigationState:
        """Execute planning node.

        Args:
            state: Current investigation state

        Returns:
            Updated state with selected_agents
        """
        try:
            logger.info(
                "planner_started",
                investigation_id=state.get("investigation_id"),
                incident_number=state["incident"].number,
            )

            # Update status
            state["status"] = InvestigationStatus.PLANNING

            # Get similar past incidents
            similar_incidents = await self._get_similar_incidents(state)
            state["similar_incidents"] = similar_incidents

            # Get service topology
            topology = await self._get_service_topology(state)
            state["topology"] = topology

            # Build planning prompt
            prompt = self._build_planning_prompt(state, similar_incidents, topology)

            # Call LLM
            messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)

            # Parse response
            import json

            try:
                result = json.loads(response.content)
                selected_agents_str = result.get("selected_agents", [])
                reasoning = result.get("reasoning", "")

                # Convert to AgentType enum
                selected_agents = [
                    AgentType(agent.lower()) for agent in selected_agents_str
                ]

                # Ensure INFRA and METRICS are always included
                if AgentType.INFRA not in selected_agents:
                    selected_agents.append(AgentType.INFRA)
                if AgentType.METRICS not in selected_agents:
                    selected_agents.append(AgentType.METRICS)

                state["selected_agents"] = selected_agents

                logger.info(
                    "agents_selected",
                    investigation_id=state.get("investigation_id"),
                    agents=[a.value for a in selected_agents],
                    reasoning=reasoning,
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(
                    "planner_parse_failed",
                    investigation_id=state.get("investigation_id"),
                    error=str(e),
                    response=response.content,
                )

                # Fallback: use all agents
                state["selected_agents"] = [
                    AgentType.METRICS,
                    AgentType.LOGS,
                    AgentType.INFRA,
                    AgentType.CODE,
                ]

            return state

        except Exception as e:
            logger.error(
                "planner_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            state["error"] = f"Planning failed: {str(e)}"
            state["status"] = InvestigationStatus.FAILED
            return state

    async def _get_similar_incidents(
        self, state: InvestigationState
    ) -> List[dict]:
        """Get similar past incidents.

        Args:
            state: Investigation state

        Returns:
            List of similar incidents
        """
        try:
            incident = state["incident"]
            query = f"{incident.short_description} {incident.description}"

            similar = await self.incident_memory.find_similar_incidents(
                state["tenant_id"],
                query,
                k=3,
            )

            return [
                {
                    "incident_number": s.incident_number,
                    "summary": s.summary,
                    "root_cause": s.root_cause,
                    "similarity": s.similarity_score,
                }
                for s in similar
            ]

        except Exception as e:
            logger.warning(
                "similar_incidents_lookup_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            return []

    async def _get_service_topology(self, state: InvestigationState) -> dict:
        """Get service topology.

        Args:
            state: Investigation state

        Returns:
            Topology information
        """
        try:
            service_name = state.get("service_name")
            if not service_name:
                return {}

            topology = await self.knowledge_graph.get_service_topology(
                state["tenant_id"],
                service_name,
            )

            if not topology:
                return {}

            return {
                "service": topology.service.name,
                "dependencies": [d.name for d in topology.dependencies],
                "resources": [
                    {"name": r.name, "type": r.type, "status": r.status}
                    for r in topology.resources
                ],
            }

        except Exception as e:
            logger.warning(
                "topology_lookup_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            return {}

    def _build_planning_prompt(
        self,
        state: InvestigationState,
        similar_incidents: List[dict],
        topology: dict,
    ) -> str:
        """Build planning prompt for LLM.

        Args:
            state: Investigation state
            similar_incidents: Similar past incidents
            topology: Service topology

        Returns:
            Formatted prompt
        """
        incident = state["incident"]
        mapped_resources = state.get("mapped_resources", [])

        prompt_parts = [
            "# Incident to Investigate",
            f"Number: {incident.number}",
            f"Title: {incident.short_description}",
            f"Description: {incident.description}",
            f"Priority: {incident.priority}",
            f"Opened: {incident.opened_at}",
            f"Current Time: {datetime.utcnow().isoformat()}",
        ]

        # Add mapped resources
        if mapped_resources:
            prompt_parts.append("\n# Affected Resources")
            for resource in mapped_resources[:5]:  # Limit to 5
                prompt_parts.append(
                    f"- {resource.resource_name} ({resource.resource_type}) "
                    f"[{resource.provider}]"
                )

        # Add topology
        if topology:
            prompt_parts.append("\n# Service Topology")
            prompt_parts.append(f"Service: {topology.get('service', 'unknown')}")

            if topology.get("dependencies"):
                prompt_parts.append(
                    f"Dependencies: {', '.join(topology['dependencies'])}"
                )

            if topology.get("resources"):
                prompt_parts.append(
                    f"Resources: {len(topology['resources'])} resources"
                )

        # Add similar incidents
        if similar_incidents:
            prompt_parts.append("\n# Similar Past Incidents")
            for sim in similar_incidents:
                prompt_parts.append(
                    f"- {sim['incident_number']} "
                    f"(similarity: {sim['similarity']:.0%})"
                )
                if sim.get("root_cause"):
                    prompt_parts.append(f"  Root Cause: {sim['root_cause']}")

        prompt_parts.append(
            "\n# Task\nAnalyze this incident and select which agents should investigate. "
            "Return your response as JSON."
        )

        return "\n".join(prompt_parts)
