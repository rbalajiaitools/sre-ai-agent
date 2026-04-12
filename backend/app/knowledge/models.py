"""Graph node and relationship models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.base import BaseSchema


class ServiceNode(BaseSchema):
    """Service node in the knowledge graph."""

    name: str = Field(..., description="Service name")
    type: str = Field(..., description="Service type (api, database, queue, etc.)")
    tenant_id: str = Field(..., description="Tenant UUID")
    provider: str = Field(..., description="Provider name (aws, azure, gcp)")
    region: Optional[str] = Field(default=None, description="Cloud region")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ResourceNode(BaseSchema):
    """Resource node in the knowledge graph."""

    resource_id: str = Field(..., description="Unique resource identifier")
    type: str = Field(..., description="Resource type (ec2, rds, lambda, etc.)")
    name: str = Field(..., description="Resource name")
    tenant_id: str = Field(..., description="Tenant UUID")
    provider: str = Field(..., description="Provider name")
    status: Optional[str] = Field(default=None, description="Resource status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class IncidentNode(BaseSchema):
    """Incident node in the knowledge graph."""

    incident_number: str = Field(..., description="Incident number")
    title: str = Field(..., description="Incident title")
    severity: str = Field(..., description="Severity level")
    tenant_id: str = Field(..., description="Tenant UUID")
    service_name: Optional[str] = Field(
        default=None, description="Affected service name"
    )
    resolved_at: Optional[datetime] = Field(
        default=None, description="When incident was resolved"
    )
    root_cause: Optional[str] = Field(default=None, description="Root cause summary")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When incident was created"
    )


class TeamNode(BaseSchema):
    """Team node in the knowledge graph."""

    name: str = Field(..., description="Team name")
    tenant_id: str = Field(..., description="Tenant UUID")
    slack_channel: Optional[str] = Field(
        default=None, description="Slack channel for team"
    )
    oncall_rotation: Optional[str] = Field(
        default=None, description="Oncall rotation identifier"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class DependencyRelationship(BaseSchema):
    """DEPENDS_ON relationship between services."""

    from_service: str = Field(..., description="Source service name")
    to_service: str = Field(..., description="Target service name")
    tenant_id: str = Field(..., description="Tenant UUID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship metadata"
    )


class TopologyResult(BaseSchema):
    """Result of service topology query."""

    service: ServiceNode = Field(..., description="The queried service")
    dependencies: List[ServiceNode] = Field(
        default_factory=list, description="Services this service depends on"
    )
    resources: List[ResourceNode] = Field(
        default_factory=list, description="Resources this service runs on"
    )
    dependent_resources: Dict[str, List[ResourceNode]] = Field(
        default_factory=dict,
        description="Resources for each dependency (service_name -> resources)",
    )


class SimilarIncident(BaseSchema):
    """Similar incident from memory search."""

    incident_number: str = Field(..., description="Incident number")
    summary: str = Field(..., description="Incident summary")
    root_cause: Optional[str] = Field(default=None, description="Root cause")
    fix_applied: Optional[str] = Field(default=None, description="Fix that was applied")
    service_name: str = Field(..., description="Affected service")
    resolved_at: Optional[datetime] = Field(
        default=None, description="When resolved"
    )
    similarity_score: float = Field(
        ..., description="Similarity score (0.0-1.0)", ge=0.0, le=1.0
    )


class IncidentSummary(BaseSchema):
    """Incident summary for memory storage."""

    incident_number: str = Field(..., description="Incident number")
    tenant_id: str = Field(..., description="Tenant UUID")
    summary: str = Field(..., description="Incident summary")
    root_cause: Optional[str] = Field(default=None, description="Root cause")
    fix_applied: Optional[str] = Field(default=None, description="Fix applied")
    service_name: str = Field(..., description="Affected service")
    resolved_at: datetime = Field(..., description="When resolved")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
