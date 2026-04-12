"""RCA node - aggregates evidence and produces root cause analysis."""

from datetime import datetime
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.logging import get_logger
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.models import IncidentNode
from app.orchestration.state import (
    InvestigationState,
    InvestigationStatus,
    RCAResult,
    TimelineEvent,
)

logger = get_logger(__name__)


# RCA system prompt
RCA_SYSTEM_PROMPT = """You are an expert SRE performing root cause analysis. Your job is to synthesize findings from multiple specialist agents and identify the most likely root cause of an incident.

Guidelines:
1. Review all evidence from agents (metrics, logs, infrastructure, code, security)
2. Identify the PRIMARY root cause - the underlying issue that triggered the incident
3. Distinguish between root cause and contributing factors
4. Build a timeline of events leading to the incident
5. Assess confidence based on strength of evidence
6. Be specific - avoid vague statements like "system overload"

Confidence scoring:
- 0.9-1.0: Strong evidence, clear root cause, reproducible
- 0.7-0.8: Good evidence, likely root cause, some uncertainty
- 0.5-0.6: Moderate evidence, possible root cause, needs validation
- 0.3-0.4: Weak evidence, speculative root cause
- 0.0-0.2: Insufficient evidence

Your response must be a JSON object with:
{
    "root_cause": "Clear one-paragraph explanation of the root cause",
    "confidence": 0.85,
    "supporting_evidence": [
        "Evidence point 1",
        "Evidence point 2"
    ],
    "affected_resources": [
        "resource-1",
        "resource-2"
    ],
    "contributing_factors": [
        "Factor 1 that made it worse",
        "Factor 2 that made it worse"
    ],
    "incident_timeline": [
        {
            "timestamp": "2024-01-15T14:25:00Z",
            "event_type": "deployment",
            "description": "New version deployed",
            "source": "code_agent"
        }
    ]
}
"""


class RCANode:
    """Performs root cause analysis by synthesizing agent findings.

    Aggregates evidence from all agents, cross-references with
    historical data, and produces a structured RCA result.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        knowledge_graph: KnowledgeGraph,
    ) -> None:
        """Initialize RCA node.

        Args:
            llm: Language model for analysis
            knowledge_graph: Knowledge graph for storing results
        """
        self.llm = llm
        self.knowledge_graph = knowledge_graph

        logger.info("rca_node_initialized")

    async def __call__(self, state: InvestigationState) -> InvestigationState:
        """Execute RCA node.

        Args:
            state: Current investigation state

        Returns:
            Updated state with rca
        """
        try:
            logger.info(
                "rca_started",
                investigation_id=state.get("investigation_id"),
                agent_results_count=len(state.get("agent_results", [])),
            )

            # Check if we have agent results
            agent_results = state.get("agent_results", [])
            if not agent_results:
                logger.warning(
                    "no_agent_results",
                    investigation_id=state.get("investigation_id"),
                )
                state["error"] = "No agent results available for RCA"
                state["status"] = InvestigationStatus.FAILED
                return state

            # Build RCA prompt
            prompt = self._build_rca_prompt(state)

            # Call LLM with structured output
            messages = [
                SystemMessage(content=RCA_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)

            # Parse response
            import json

            try:
                result_dict = json.loads(response.content)

                # Parse timeline events
                timeline_events = []
                for event_data in result_dict.get("incident_timeline", []):
                    timeline_events.append(
                        TimelineEvent(
                            timestamp=datetime.fromisoformat(
                                event_data["timestamp"].replace("Z", "+00:00")
                            ),
                            event_type=event_data["event_type"],
                            description=event_data["description"],
                            source=event_data["source"],
                        )
                    )

                # Create RCAResult
                rca = RCAResult(
                    root_cause=result_dict["root_cause"],
                    confidence=result_dict["confidence"],
                    supporting_evidence=result_dict.get("supporting_evidence", []),
                    affected_resources=result_dict.get("affected_resources", []),
                    contributing_factors=result_dict.get("contributing_factors", []),
                    incident_timeline=timeline_events,
                )

                state["rca"] = rca
                state["status"] = InvestigationStatus.RCA_COMPLETE

                logger.info(
                    "rca_completed",
                    investigation_id=state.get("investigation_id"),
                    confidence=rca.confidence,
                    root_cause_length=len(rca.root_cause),
                )

                # Store in knowledge graph
                await self._store_incident_in_graph(state, rca)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(
                    "rca_parse_failed",
                    investigation_id=state.get("investigation_id"),
                    error=str(e),
                    response=response.content[:500],
                )

                # Create fallback RCA
                rca = RCAResult(
                    root_cause="Unable to determine root cause from available evidence. "
                    "Manual investigation required.",
                    confidence=0.1,
                    supporting_evidence=[
                        f"Agent results: {len(agent_results)} agents completed"
                    ],
                    affected_resources=[],
                    contributing_factors=[],
                    incident_timeline=[],
                )

                state["rca"] = rca
                state["status"] = InvestigationStatus.RCA_COMPLETE

            return state

        except Exception as e:
            logger.error(
                "rca_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            state["error"] = f"RCA failed: {str(e)}"
            state["status"] = InvestigationStatus.FAILED
            return state

    def _build_rca_prompt(self, state: InvestigationState) -> str:
        """Build RCA prompt for LLM.

        Args:
            state: Investigation state

        Returns:
            Formatted prompt
        """
        incident = state["incident"]
        agent_results = state.get("agent_results", [])
        similar_incidents = state.get("similar_incidents", [])
        topology = state.get("topology", {})

        prompt_parts = [
            "# Incident Information",
            f"Number: {incident.number}",
            f"Title: {incident.short_description}",
            f"Description: {incident.description}",
            f"Opened: {incident.opened_at}",
            f"Priority: {incident.priority}",
        ]

        # Add topology context
        if topology:
            prompt_parts.append("\n# Service Topology")
            prompt_parts.append(f"Service: {topology.get('service', 'unknown')}")
            if topology.get("dependencies"):
                prompt_parts.append(
                    f"Dependencies: {', '.join(topology['dependencies'])}"
                )

        # Add agent findings
        prompt_parts.append("\n# Agent Findings")

        for result in agent_results:
            prompt_parts.append(f"\n## {result.agent_type.value.upper()} Agent")

            if result.success:
                prompt_parts.append(f"Status: ✓ Completed successfully")
                prompt_parts.append(
                    f"Duration: {result.duration_seconds:.1f}s"
                )
                prompt_parts.append(
                    f"Providers: {', '.join(result.providers_queried)}"
                )

                if result.evidence:
                    prompt_parts.append("\nEvidence:")
                    for evidence in result.evidence[:5]:  # Limit to 5
                        prompt_parts.append(f"- {evidence}")

                if result.analysis:
                    prompt_parts.append("\nAnalysis:")
                    # Format analysis dict
                    for key, value in list(result.analysis.items())[:3]:
                        prompt_parts.append(f"- {key}: {value}")

            else:
                prompt_parts.append(f"Status: ✗ Failed")
                prompt_parts.append(f"Error: {result.error}")

        # Add similar incidents
        if similar_incidents:
            prompt_parts.append("\n# Similar Past Incidents")
            for sim in similar_incidents:
                prompt_parts.append(
                    f"\n{sim['incident_number']} "
                    f"(similarity: {sim['similarity']:.0%})"
                )
                if sim.get("root_cause"):
                    prompt_parts.append(f"Root Cause: {sim['root_cause']}")

        prompt_parts.append(
            "\n# Task\n"
            "Analyze all evidence and determine the root cause. "
            "Return your response as JSON following the specified format."
        )

        return "\n".join(prompt_parts)

    async def _store_incident_in_graph(
        self,
        state: InvestigationState,
        rca: RCAResult,
    ) -> None:
        """Store incident in knowledge graph.

        Args:
            state: Investigation state
            rca: RCA result
        """
        try:
            incident = state["incident"]

            incident_node = IncidentNode(
                incident_number=incident.number,
                title=incident.short_description,
                severity=incident.priority,
                tenant_id=state["tenant_id"],
                service_name=state.get("service_name"),
                root_cause=rca.root_cause,
                created_at=incident.opened_at,
                resolved_at=None,  # Not resolved yet
            )

            await self.knowledge_graph.upsert_incident(
                state["tenant_id"],
                incident_node,
            )

            logger.info(
                "incident_stored_in_graph",
                investigation_id=state.get("investigation_id"),
                incident_number=incident.number,
            )

        except Exception as e:
            logger.warning(
                "incident_graph_storage_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            # Don't fail RCA if graph storage fails
