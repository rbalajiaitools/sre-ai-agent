"""ServiceNow-specific Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from app.models.base import BaseSchema


class IncidentPriority(str, Enum):
    """ServiceNow incident priority levels."""

    P1 = "1"  # Critical
    P2 = "2"  # High
    P3 = "3"  # Moderate
    P4 = "4"  # Low
    P5 = "5"  # Planning


class IncidentState(str, Enum):
    """ServiceNow incident states."""

    NEW = "1"
    IN_PROGRESS = "2"
    ON_HOLD = "3"
    RESOLVED = "6"
    CLOSED = "7"
    CANCELED = "8"


class ServiceNowIncident(BaseSchema):
    """Canonical incident model used throughout the platform.

    This model represents a ServiceNow incident in our system.
    All incident data is normalized to this format.
    """

    sys_id: str = Field(..., description="ServiceNow sys_id")
    number: str = Field(..., description="Incident number (e.g., INC0012345)")
    short_description: str = Field(..., description="Short description")
    description: str = Field(..., description="Full description")
    priority: IncidentPriority = Field(..., description="Priority level")
    state: IncidentState = Field(..., description="Current state")
    category: str = Field(default="", description="Incident category")
    subcategory: str = Field(default="", description="Incident subcategory")
    cmdb_ci: str = Field(default="", description="Configuration item name")
    cmdb_ci_sys_id: str = Field(default="", description="CI sys_id")
    assignment_group: str = Field(default="", description="Assignment group")
    assigned_to: Optional[str] = Field(default=None, description="Assigned user")
    opened_at: datetime = Field(..., description="Opened timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    resolved_at: Optional[datetime] = Field(default=None, description="Resolved timestamp")
    work_notes: List[str] = Field(default_factory=list, description="Work notes")
    related_incidents: List[str] = Field(
        default_factory=list, description="Related incident numbers"
    )
    tenant_id: str = Field(..., description="Tenant ID (added by our system)")


class IncidentFilter(BaseSchema):
    """Filter criteria for querying incidents."""

    states: List[IncidentState] = Field(
        default_factory=lambda: [IncidentState.NEW, IncidentState.IN_PROGRESS],
        description="Filter by states",
    )
    priorities: List[IncidentPriority] = Field(
        default_factory=list, description="Filter by priorities"
    )
    updated_after: Optional[datetime] = Field(
        default=None, description="Filter by update time"
    )
    assignment_groups: List[str] = Field(
        default_factory=list, description="Filter by assignment groups"
    )
    incident_numbers: List[str] = Field(
        default_factory=list, description="Filter by specific incident numbers"
    )
    custom_query: Optional[str] = Field(
        default=None, description="Custom ServiceNow query string"
    )
    limit: int = Field(default=50, description="Maximum results to return")


class RawIncident(BaseSchema):
    """Raw incident data from ServiceNow API.

    This represents the raw response from ServiceNow before normalization.
    """

    sys_id: str
    number: str
    short_description: str
    description: str
    priority: str
    state: str
    category: str = ""
    subcategory: str = ""
    cmdb_ci: dict | str = Field(default_factory=dict)
    assignment_group: dict | str = Field(default_factory=dict)
    assigned_to: dict | str = Field(default_factory=dict)
    opened_at: str
    sys_updated_on: str
    resolved_at: Optional[str] = None
    work_notes: str = ""
    parent_incident: dict = Field(default_factory=dict)
    child_incidents: str = ""


class IncidentHistory(BaseSchema):
    """Incident history entry."""

    sys_id: str
    field: str
    old_value: str
    new_value: str
    update_time: datetime
    updated_by: str


class MappedResource(BaseSchema):
    """Resource mapped from ServiceNow CI."""

    adapter_name: str = Field(..., description="Name of the adapter")
    provider_name: str = Field(..., description="Provider name (aws, azure, etc.)")
    resource_id: str = Field(..., description="Resource identifier")
    resource_name: str = Field(..., description="Resource name")
    confidence_score: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
