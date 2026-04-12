"""FastAPI endpoints for investigation orchestration."""

import asyncio
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.connectors.servicenow.ci_mapper import CIMapper
from app.connectors.servicenow.connector import ServiceNowConnector
from app.core.dependencies import (
    get_incident_memory,
    get_knowledge_graph,
    get_llm,
    get_provider_registry,
    get_servicenow_connector,
)
from app.core.logging import get_logger
from app.orchestration.graph import InvestigationGraph
from app.orchestration.state import (
    ApproveResolutionRequest,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationState,
    InvestigationStatus,
    InvestigationStatusResponse,
    MappedResource,
    RCAResult,
)

logger = get_logger(__name__)

router = APIRouter(tags=["investigations"])


# Global investigation graph instance
# In production, this would be managed by dependency injection
_investigation_graph: Optional[InvestigationGraph] = None


def get_investigation_graph(
    llm=Depends(get_llm),
    registry=Depends(get_provider_registry),
    knowledge_graph=Depends(get_knowledge_graph),
    incident_memory=Depends(get_incident_memory),
    servicenow_connector=Depends(get_servicenow_connector),
) -> InvestigationGraph:
    """Get investigation graph instance.

    Args:
        llm: Language model
        registry: Provider registry
        knowledge_graph: Knowledge graph
        incident_memory: Incident memory
        servicenow_connector: ServiceNow connector

    Returns:
        Investigation graph instance
    """
    global _investigation_graph

    if _investigation_graph is None:
        _investigation_graph = InvestigationGraph(
            llm=llm,
            registry=registry,
            knowledge_graph=knowledge_graph,
            incident_memory=incident_memory,
            servicenow_connector=servicenow_connector,
        )

    return _investigation_graph


@router.post("/investigations", response_model=InvestigationResponse)
async def start_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks,
    graph: InvestigationGraph = Depends(get_investigation_graph),
    servicenow: ServiceNowConnector = Depends(get_servicenow_connector),
    knowledge_graph=Depends(get_knowledge_graph),
) -> InvestigationResponse:
    """Start an incident investigation.

    Args:
        request: Investigation request
        background_tasks: Background tasks
        graph: Investigation graph
        servicenow: ServiceNow connector
        knowledge_graph: Knowledge graph

    Returns:
        Investigation response with ID and status
    """
    try:
        logger.info(
            "investigation_request_received",
            tenant_id=request.tenant_id,
            incident_number=request.incident_number,
        )

        # Fetch incident from ServiceNow
        tenant_id = UUID(request.tenant_id)
        incidents = await servicenow.get_incidents(tenant_id)

        incident = next(
            (i for i in incidents if i.number == request.incident_number),
            None,
        )

        if not incident:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {request.incident_number} not found",
            )

        # Extract service name from incident
        # In production, this would use more sophisticated logic
        service_name = incident.cmdb_ci or "unknown"

        # Map CI to resources
        ci_mapper = CIMapper(knowledge_graph)
        mapped_resources = []

        if incident.cmdb_ci:
            resources = await knowledge_graph.find_resource_by_ci(
                request.tenant_id,
                incident.cmdb_ci,
            )

            for resource in resources:
                mapped_resources.append(
                    MappedResource(
                        ci_name=incident.cmdb_ci,
                        resource_id=resource.resource_id,
                        resource_name=resource.name,
                        resource_type=resource.type,
                        provider=resource.provider,
                        confidence=0.8,  # Placeholder
                    )
                )

        # Start investigation in background
        async def run_investigation():
            try:
                await graph.investigate(
                    tenant_id=request.tenant_id,
                    incident=incident,
                    service_name=service_name,
                    mapped_resources=mapped_resources,
                )
            except Exception as e:
                logger.error(
                    "background_investigation_failed",
                    tenant_id=request.tenant_id,
                    incident_number=request.incident_number,
                    error=str(e),
                )

        # Add to background tasks
        background_tasks.add_task(run_investigation)

        # Generate investigation ID (will be created by graph)
        # For now, return a placeholder
        investigation_id = f"inv-{request.incident_number}"

        logger.info(
            "investigation_started",
            investigation_id=investigation_id,
            tenant_id=request.tenant_id,
            incident_number=request.incident_number,
        )

        return InvestigationResponse(
            investigation_id=investigation_id,
            status=InvestigationStatus.STARTED,
            message="Investigation started successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "start_investigation_failed",
            tenant_id=request.tenant_id,
            incident_number=request.incident_number,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start investigation: {str(e)}",
        )


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationStatusResponse,
)
async def get_investigation_status(
    investigation_id: str,
    graph: InvestigationGraph = Depends(get_investigation_graph),
) -> InvestigationStatusResponse:
    """Get investigation status.

    Args:
        investigation_id: Investigation ID
        graph: Investigation graph

    Returns:
        Investigation status
    """
    try:
        logger.info(
            "investigation_status_requested",
            investigation_id=investigation_id,
        )

        # Get state from graph
        state = await graph.get_state(investigation_id)

        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Investigation {investigation_id} not found",
            )

        # Build response
        response = InvestigationStatusResponse(
            investigation_id=investigation_id,
            tenant_id=state.get("tenant_id", ""),
            incident_number=state.get("incident", {}).number
            if state.get("incident")
            else "",
            status=state.get("status", InvestigationStatus.STARTED),
            started_at=state.get("started_at"),
            completed_at=state.get("completed_at"),
            selected_agents=state.get("selected_agents", []),
            agent_results_count=len(state.get("agent_results", [])),
            has_rca=state.get("rca") is not None,
            has_resolution=state.get("resolution") is not None,
            error=state.get("error"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_investigation_status_failed",
            investigation_id=investigation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get investigation status: {str(e)}",
        )


@router.get("/investigations/{investigation_id}/rca", response_model=RCAResult)
async def get_investigation_rca(
    investigation_id: str,
    graph: InvestigationGraph = Depends(get_investigation_graph),
) -> RCAResult:
    """Get investigation RCA result.

    Args:
        investigation_id: Investigation ID
        graph: Investigation graph

    Returns:
        RCA result
    """
    try:
        logger.info(
            "investigation_rca_requested",
            investigation_id=investigation_id,
        )

        # Get state from graph
        state = await graph.get_state(investigation_id)

        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Investigation {investigation_id} not found",
            )

        # Check if RCA is complete
        rca = state.get("rca")
        if not rca:
            raise HTTPException(
                status_code=404,
                detail="RCA not yet complete for this investigation",
            )

        return rca

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_investigation_rca_failed",
            investigation_id=investigation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get investigation RCA: {str(e)}",
        )


@router.post("/investigations/{investigation_id}/approve-resolution")
async def approve_resolution(
    investigation_id: str,
    request: ApproveResolutionRequest,
    graph: InvestigationGraph = Depends(get_investigation_graph),
    servicenow: ServiceNowConnector = Depends(get_servicenow_connector),
) -> dict:
    """Approve resolution and close incident.

    Args:
        investigation_id: Investigation ID
        request: Approval request
        graph: Investigation graph
        servicenow: ServiceNow connector

    Returns:
        Confirmation message
    """
    try:
        logger.info(
            "resolution_approval_requested",
            investigation_id=investigation_id,
            approved_by=request.approved_by,
        )

        # Get state from graph
        state = await graph.get_state(investigation_id)

        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Investigation {investigation_id} not found",
            )

        # Validate investigation is complete
        if state.get("status") != InvestigationStatus.RESOLVED:
            raise HTTPException(
                status_code=400,
                detail=f"Investigation not resolved. Current status: {state.get('status')}",
            )

        resolution = state.get("resolution")
        if not resolution:
            raise HTTPException(
                status_code=404,
                detail="Resolution not found for this investigation",
            )

        # Get incident
        incident = state.get("incident")
        if not incident:
            raise HTTPException(
                status_code=404,
                detail="Incident not found in investigation state",
            )

        # Add approval note to ServiceNow
        approval_note = (
            f"Resolution approved by {request.approved_by}\n\n"
            f"Recommended Fix:\n{resolution.recommended_fix}\n\n"
            f"Fix Steps:\n"
        )

        for i, step in enumerate(resolution.fix_steps, 1):
            approval_note += f"{i}. {step}\n"

        if resolution.commands:
            approval_note += "\nCommands:\n"
            for cmd in resolution.commands:
                approval_note += f"  {cmd}\n"

        if request.comments:
            approval_note += f"\nApproval Comments:\n{request.comments}\n"

        # Add work note
        await servicenow.client.add_work_note(incident.sys_id, approval_note)

        # Close incident
        # In production, you might want to update incident state
        # await servicenow.client.update_incident(incident.sys_id, {"state": "resolved"})

        logger.info(
            "resolution_approved",
            investigation_id=investigation_id,
            incident_number=incident.number,
            approved_by=request.approved_by,
        )

        return {
            "message": "Resolution approved and incident updated",
            "investigation_id": investigation_id,
            "incident_number": incident.number,
            "approved_by": request.approved_by,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "approve_resolution_failed",
            investigation_id=investigation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve resolution: {str(e)}",
        )


@router.get("/incidents")
async def get_incidents(
    tenant_id: str = Query(..., description="Tenant UUID"),
    refresh: bool = Query(False, description="Refresh from ServiceNow"),
    servicenow: ServiceNowConnector = Depends(get_servicenow_connector),
) -> List[dict]:
    """Get cached ServiceNow incidents for tenant.

    Args:
        tenant_id: Tenant UUID
        refresh: Whether to refresh from ServiceNow
        servicenow: ServiceNow connector

    Returns:
        List of incidents
    """
    try:
        logger.info(
            "incidents_requested",
            tenant_id=tenant_id,
            refresh=refresh,
        )

        tenant_uuid = UUID(tenant_id)

        # Refresh if requested
        if refresh:
            # Trigger manual poller refresh
            # In production, this would call the poller
            logger.info("manual_refresh_requested", tenant_id=tenant_id)

        # Get incidents
        incidents = await servicenow.get_incidents(tenant_uuid)

        # Convert to dict
        incidents_dict = [
            {
                "number": i.number,
                "short_description": i.short_description,
                "description": i.description,
                "priority": i.priority,
                "state": i.state,
                "opened_at": i.opened_at.isoformat() if i.opened_at else None,
                "cmdb_ci": i.cmdb_ci,
                "sys_id": i.sys_id,
            }
            for i in incidents
        ]

        logger.info(
            "incidents_returned",
            tenant_id=tenant_id,
            count=len(incidents_dict),
        )

        return incidents_dict

    except Exception as e:
        logger.error(
            "get_incidents_failed",
            tenant_id=tenant_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get incidents: {str(e)}",
        )
