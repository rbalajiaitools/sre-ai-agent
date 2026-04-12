"""Investigation state model for LangGraph."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import TypedDict

from app.agents.models import AgentResult, AgentType
from app.connectors.servicenow.models import ServiceNowIncident
from app.models.base import BaseSchema


class InvestigationStatus(str, Enum):
    """Investigation status."""

    STARTED = "started"
    PLANNING = "planning"
    INVESTIGATING = "investigating"
    RCA_COMPLETE = "rca_complete"
    RESOLVED = "resolved"
    FAILED = "failed"
    NEEDS_INPUT = "needs_input"


class MappedResource(BaseSchema):
    """Resource mapped from ServiceNow CI."""

    ci_name: str = Field(..., description="ServiceNow CI name")
    resource_id: str = Field(..., description="Cloud resource ID")
    resource_name: str = Field(..., description="Cloud resource name")
    resource_type: str = Field(..., description="Resource type")
    provider: str = Field(..., description="Cloud provider")
    confidence: float = Field(..., description="Mapping confidence (0-1)")


class TimelineEvent(BaseSchema):
    """Event in incident timeline."""

    timestamp: datetime = Field(..., description="When event occurred")
    event_type: str = Field(..., description="Type of event")
    description: str = Field(..., description="Event description")
    source: str = Field(..., description="Source of event (agent, metric, log)")


class RCAResult(BaseSchema):
    """Root cause analysis result."""

    root_cause: str = Field(..., description="Clear one-paragraph explanation")
    confidence: float = Field(
        ..., description="Confidence score (0-1)", ge=0.0, le=1.0
    )
    supporting_evidence: List[str] = Field(
        default_factory=list, description="Evidence supporting the root cause"
    )
    affected_resources: List[str] = Field(
        default_factory=list, description="Resources affected by the incident"
    )
    contributing_factors: List[str] = Field(
        default_factory=list, description="Contributing factors (not root cause)"
    )
    incident_timeline: List[TimelineEvent] = Field(
        default_factory=list, description="Timeline of events"
    )


class ResolutionOutput(BaseSchema):
    """Resolution output with fix recommendations."""

    recommended_fix: str = Field(..., description="Recommended fix description")
    fix_steps: List[str] = Field(
        default_factory=list, description="Ordered actionable steps"
    )
    commands: List[str] = Field(
        default_factory=list, description="Exact commands if applicable"
    )
    estimated_impact: str = Field(..., description="Estimated impact of fix")
    requires_human_approval: bool = Field(
        ..., description="Whether fix requires human approval"
    )
    snow_work_note: str = Field(
        ..., description="Pre-formatted ServiceNow work note"
    )


class InvestigationState(TypedDict, total=False):
    """State for LangGraph investigation workflow.

    This is the state that flows through the investigation graph.
    Each node reads from and writes to this state.
    """

    # Input
    investigation_id: str
    tenant_id: str
    incident: ServiceNowIncident
    service_name: str

    # Planning
    mapped_resources: List[MappedResource]
    selected_agents: List[AgentType]

    # Investigation
    agent_results: List[AgentResult]

    # Analysis
    rca: Optional[RCAResult]

    # Resolution
    resolution: Optional[ResolutionOutput]

    # Metadata
    status: InvestigationStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]

    # Additional context
    similar_incidents: List[Dict[str, Any]]
    topology: Optional[Dict[str, Any]]


class InvestigationRequest(BaseSchema):
    """Request to start an investigation."""

    tenant_id: str = Field(..., description="Tenant UUID")
    incident_number: str = Field(..., description="ServiceNow incident number")


class InvestigationResponse(BaseSchema):
    """Response from starting an investigation."""

    investigation_id: str = Field(..., description="Investigation UUID")
    status: InvestigationStatus = Field(..., description="Current status")
    message: str = Field(..., description="Status message")


class InvestigationStatusResponse(BaseSchema):
    """Response for investigation status query."""

    investigation_id: str = Field(..., description="Investigation UUID")
    tenant_id: str = Field(..., description="Tenant UUID")
    incident_number: str = Field(..., description="Incident number")
    status: InvestigationStatus = Field(..., description="Current status")
    started_at: datetime = Field(..., description="When investigation started")
    completed_at: Optional[datetime] = Field(
        default=None, description="When investigation completed"
    )
    selected_agents: List[AgentType] = Field(
        default_factory=list, description="Agents selected for investigation"
    )
    agent_results_count: int = Field(
        default=0, description="Number of agent results"
    )
    has_rca: bool = Field(default=False, description="Whether RCA is complete")
    has_resolution: bool = Field(
        default=False, description="Whether resolution is generated"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ApproveResolutionRequest(BaseSchema):
    """Request to approve resolution."""

    approved_by: str = Field(..., description="User who approved")
    comments: Optional[str] = Field(default=None, description="Approval comments")
