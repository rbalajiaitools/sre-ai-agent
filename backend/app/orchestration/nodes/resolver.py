"""Resolver node - generates fix recommendations and resolution."""

from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.connectors.servicenow.connector import ServiceNowConnector
from app.core.logging import get_logger
from app.knowledge.memory import IncidentMemory
from app.knowledge.models import IncidentSummary
from app.orchestration.state import (
    InvestigationState,
    InvestigationStatus,
    ResolutionOutput,
)

logger = get_logger(__name__)


# Resolver system prompt
RESOLVER_SYSTEM_PROMPT = """You are an expert SRE generating resolution recommendations for incidents. Your job is to propose specific, actionable fixes based on the root cause analysis.

Guidelines:
1. Propose specific fix steps based on the root cause
2. Generate exact commands where applicable (kubectl, aws cli, terraform)
3. Use actual resource names from the incident context
4. Order steps logically (diagnose → fix → verify)
5. Set requires_human_approval=True for destructive actions:
   - Deleting resources
   - Scaling down
   - Modifying production databases
   - Changing security policies
6. Estimate impact (downtime, performance, cost)
7. Format ServiceNow work note professionally

Command examples:
- kubectl: kubectl scale deployment payment-api --replicas=5
- AWS CLI: aws rds modify-db-instance --db-instance-identifier prod-db --max-connections 200
- Terraform: terraform apply -target=aws_db_instance.main

Your response must be a JSON object with:
{
    "recommended_fix": "Brief description of the recommended fix",
    "fix_steps": [
        "Step 1: Verify current state",
        "Step 2: Apply fix",
        "Step 3: Verify fix"
    ],
    "commands": [
        "kubectl get pods -n production",
        "kubectl scale deployment payment-api --replicas=5"
    ],
    "estimated_impact": "5 minutes downtime during restart",
    "requires_human_approval": true,
    "snow_work_note": "Formatted work note for ServiceNow"
}
"""


class ResolverNode:
    """Generates resolution recommendations and updates ServiceNow.

    Creates actionable fix steps, commands, and impact assessment
    based on RCA results. Updates ServiceNow with work notes.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        servicenow_connector: ServiceNowConnector,
        incident_memory: IncidentMemory,
    ) -> None:
        """Initialize resolver node.

        Args:
            llm: Language model for resolution generation
            servicenow_connector: ServiceNow connector
            incident_memory: Incident memory for storing resolution
        """
        self.llm = llm
        self.servicenow_connector = servicenow_connector
        self.incident_memory = incident_memory

        logger.info("resolver_node_initialized")

    async def __call__(self, state: InvestigationState) -> InvestigationState:
        """Execute resolver node.

        Args:
            state: Current investigation state

        Returns:
            Updated state with resolution
        """
        try:
            logger.info(
                "resolver_started",
                investigation_id=state.get("investigation_id"),
            )

            # Check if we have RCA
            rca = state.get("rca")
            if not rca:
                logger.warning(
                    "no_rca_available",
                    investigation_id=state.get("investigation_id"),
                )
                state["error"] = "No RCA available for resolution"
                state["status"] = InvestigationStatus.FAILED
                return state

            # Build resolution prompt
            prompt = self._build_resolution_prompt(state)

            # Call LLM
            messages = [
                SystemMessage(content=RESOLVER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)

            # Parse response
            import json

            try:
                result_dict = json.loads(response.content)

                # Create ResolutionOutput
                resolution = ResolutionOutput(
                    recommended_fix=result_dict["recommended_fix"],
                    fix_steps=result_dict.get("fix_steps", []),
                    commands=result_dict.get("commands", []),
                    estimated_impact=result_dict["estimated_impact"],
                    requires_human_approval=result_dict.get(
                        "requires_human_approval", True
                    ),
                    snow_work_note=result_dict["snow_work_note"],
                )

                state["resolution"] = resolution
                state["status"] = InvestigationStatus.RESOLVED
                state["completed_at"] = datetime.utcnow()

                logger.info(
                    "resolution_generated",
                    investigation_id=state.get("investigation_id"),
                    requires_approval=resolution.requires_human_approval,
                    steps_count=len(resolution.fix_steps),
                )

                # Write work note to ServiceNow
                await self._update_servicenow(state, resolution)

                # Store in incident memory
                await self._store_in_memory(state, resolution)

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(
                    "resolution_parse_failed",
                    investigation_id=state.get("investigation_id"),
                    error=str(e),
                    response=response.content[:500],
                )

                # Create fallback resolution
                resolution = ResolutionOutput(
                    recommended_fix="Manual investigation and resolution required",
                    fix_steps=[
                        "Review RCA findings",
                        "Consult with team",
                        "Implement appropriate fix",
                    ],
                    commands=[],
                    estimated_impact="Unknown - requires manual assessment",
                    requires_human_approval=True,
                    snow_work_note=f"Automated investigation completed. "
                    f"Root cause: {rca.root_cause}\n\n"
                    f"Manual resolution required.",
                )

                state["resolution"] = resolution
                state["status"] = InvestigationStatus.RESOLVED
                state["completed_at"] = datetime.utcnow()

            return state

        except Exception as e:
            logger.error(
                "resolver_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            state["error"] = f"Resolution generation failed: {str(e)}"
            state["status"] = InvestigationStatus.FAILED
            return state

    def _build_resolution_prompt(self, state: InvestigationState) -> str:
        """Build resolution prompt for LLM.

        Args:
            state: Investigation state

        Returns:
            Formatted prompt
        """
        incident = state["incident"]
        rca = state["rca"]
        mapped_resources = state.get("mapped_resources", [])
        topology = state.get("topology", {})

        prompt_parts = [
            "# Incident Information",
            f"Number: {incident.number}",
            f"Title: {incident.short_description}",
            f"Service: {state.get('service_name', 'unknown')}",
        ]

        # Add RCA
        prompt_parts.append("\n# Root Cause Analysis")
        prompt_parts.append(f"Root Cause: {rca.root_cause}")
        prompt_parts.append(f"Confidence: {rca.confidence:.0%}")

        if rca.supporting_evidence:
            prompt_parts.append("\nSupporting Evidence:")
            for evidence in rca.supporting_evidence[:5]:
                prompt_parts.append(f"- {evidence}")

        if rca.affected_resources:
            prompt_parts.append("\nAffected Resources:")
            for resource in rca.affected_resources[:5]:
                prompt_parts.append(f"- {resource}")

        # Add mapped resources with details
        if mapped_resources:
            prompt_parts.append("\n# Resource Details")
            for resource in mapped_resources[:5]:
                prompt_parts.append(
                    f"- {resource.resource_name} ({resource.resource_type})"
                )
                prompt_parts.append(f"  ID: {resource.resource_id}")
                prompt_parts.append(f"  Provider: {resource.provider}")

        # Add topology
        if topology:
            prompt_parts.append("\n# Service Topology")
            if topology.get("dependencies"):
                prompt_parts.append(
                    f"Dependencies: {', '.join(topology['dependencies'])}"
                )

        # Add timeline
        if rca.incident_timeline:
            prompt_parts.append("\n# Incident Timeline")
            for event in rca.incident_timeline[:5]:
                prompt_parts.append(
                    f"- {event.timestamp.strftime('%H:%M:%S')}: "
                    f"{event.description}"
                )

        prompt_parts.append(
            "\n# Task\n"
            "Generate specific resolution recommendations with actionable steps. "
            "Return your response as JSON following the specified format."
        )

        return "\n".join(prompt_parts)

    async def _update_servicenow(
        self,
        state: InvestigationState,
        resolution: ResolutionOutput,
    ) -> None:
        """Update ServiceNow with work note.

        Args:
            state: Investigation state
            resolution: Resolution output
        """
        try:
            incident = state["incident"]

            # Add work note
            await self.servicenow_connector.add_work_note(
                incident.sys_id,
                resolution.snow_work_note,
            )

            logger.info(
                "servicenow_updated",
                investigation_id=state.get("investigation_id"),
                incident_number=incident.number,
            )

        except Exception as e:
            logger.error(
                "servicenow_update_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            # Don't fail resolution if ServiceNow update fails

    async def _store_in_memory(
        self,
        state: InvestigationState,
        resolution: ResolutionOutput,
    ) -> None:
        """Store incident and resolution in memory.

        Args:
            state: Investigation state
            resolution: Resolution output
        """
        try:
            incident = state["incident"]
            rca = state["rca"]

            # Create incident summary
            summary = IncidentSummary(
                incident_number=incident.number,
                tenant_id=state["tenant_id"],
                summary=f"{incident.short_description}. {rca.root_cause}",
                root_cause=rca.root_cause,
                fix_applied=resolution.recommended_fix,
                service_name=state.get("service_name", "unknown"),
                resolved_at=datetime.utcnow(),
                tags=[
                    incident.priority,
                    state.get("service_name", "unknown"),
                ],
            )

            # Store in memory
            await self.incident_memory.store_incident(
                state["tenant_id"],
                summary,
            )

            logger.info(
                "incident_stored_in_memory",
                investigation_id=state.get("investigation_id"),
                incident_number=incident.number,
            )

        except Exception as e:
            logger.warning(
                "incident_memory_storage_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )
            # Don't fail resolution if memory storage fails
