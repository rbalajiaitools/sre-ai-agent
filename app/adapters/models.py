"""Provider-agnostic data models for adapter framework.

All models in this module are completely provider-agnostic. They define the
contract between agents and adapters, ensuring no provider-specific types
leak into agent code.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.base import BaseSchema


class ProviderType(str, Enum):
    """Type of provider."""

    CLOUD = "cloud"
    ON_PREM = "on_prem"
    OBSERVABILITY = "observability"
    ITSM = "itsm"


class AdapterCapability(str, Enum):
    """Capabilities that adapters can support."""

    METRICS = "metrics"
    LOGS = "logs"
    RESOURCES = "resources"
    AUDIT = "audit"
    COST = "cost"
    CHANGES = "changes"
    TOPOLOGY = "topology"


class LogLevel(str, Enum):
    """Log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    """Types of infrastructure resources."""

    COMPUTE = "compute"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    DATABASE = "database"
    QUEUE = "queue"
    LOAD_BALANCER = "load_balancer"
    NETWORK = "network"
    STORAGE = "storage"
    KUBERNETES_WORKLOAD = "kubernetes_workload"


class ResourceStatus(str, Enum):
    """Status of a resource."""

    RUNNING = "running"
    STOPPED = "stopped"
    PENDING = "pending"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ChangeType(str, Enum):
    """Types of changes that can occur."""

    DEPLOYMENT = "deployment"
    CONFIG_CHANGE = "config_change"
    SCALING_EVENT = "scaling_event"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    CODE_MERGE = "code_merge"
    RESTART = "restart"


# ============================================================================
# Metrics Models
# ============================================================================


class DataPoint(BaseSchema):
    """Single data point in a time series."""

    timestamp: datetime = Field(..., description="Timestamp of the data point")
    value: float = Field(..., description="Metric value")
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Additional tags for this data point"
    )


class MetricSeries(BaseSchema):
    """Time series data for a single metric."""

    metric_name: str = Field(..., description="Name of the metric")
    unit: str = Field(..., description="Unit of measurement (e.g., 'percent', 'bytes', 'count')")
    data_points: List[DataPoint] = Field(..., description="Time series data points")


class MetricsRequest(BaseSchema):
    """Request for metrics data."""

    service_name: str = Field(..., description="Name of the service to query")
    metric_names: List[str] = Field(..., description="List of metric names to retrieve")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    granularity_seconds: int = Field(
        default=60, description="Data point granularity in seconds"
    )
    filters: Dict[str, str] = Field(
        default_factory=dict, description="Additional filters (e.g., region, environment)"
    )


class MetricsResponse(BaseSchema):
    """Response containing metrics data."""

    metrics: List[MetricSeries] = Field(..., description="List of metric time series")
    source_provider: str = Field(..., description="Provider that supplied the data")
    query_duration_ms: int = Field(..., description="Query execution time in milliseconds")


# ============================================================================
# Logs Models
# ============================================================================


class LogEntry(BaseSchema):
    """Single log entry."""

    timestamp: datetime = Field(..., description="Log timestamp")
    level: LogLevel = Field(..., description="Log severity level")
    message: str = Field(..., description="Log message")
    service: str = Field(..., description="Service that generated the log")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Additional log attributes"
    )
    trace_id: Optional[str] = Field(default=None, description="Distributed trace ID")


class LogsRequest(BaseSchema):
    """Request for log data."""

    service_name: str = Field(..., description="Name of the service to query")
    query: str = Field(..., description="Log query string (provider-agnostic syntax)")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    limit: int = Field(default=1000, description="Maximum number of logs to return")
    log_level: Optional[LogLevel] = Field(
        default=None, description="Filter by log level"
    )


class LogsResponse(BaseSchema):
    """Response containing log data."""

    logs: List[LogEntry] = Field(..., description="List of log entries")
    total_count: int = Field(..., description="Total number of matching logs")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Resources Models
# ============================================================================


class ResourceHealth(BaseSchema):
    """Health status of a resource."""

    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    last_check: datetime = Field(..., description="Last health check timestamp")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional health details"
    )


class Resource(BaseSchema):
    """Infrastructure resource."""

    resource_id: str = Field(..., description="Unique resource identifier")
    resource_type: ResourceType = Field(..., description="Type of resource")
    name: str = Field(..., description="Resource name")
    status: ResourceStatus = Field(..., description="Current resource status")
    region: str = Field(..., description="Region or location")
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional resource metadata"
    )
    health: Optional[ResourceHealth] = Field(
        default=None, description="Health status if available"
    )


class ResourcesRequest(BaseSchema):
    """Request for resource data."""

    resource_types: List[ResourceType] = Field(
        ..., description="Types of resources to retrieve"
    )
    filters: Dict[str, str] = Field(
        default_factory=dict, description="Filters (e.g., region, tags)"
    )
    include_health: bool = Field(
        default=False, description="Whether to include health status"
    )


class ResourcesResponse(BaseSchema):
    """Response containing resource data."""

    resources: List[Resource] = Field(..., description="List of resources")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Topology Models
# ============================================================================


class TopologyNode(BaseSchema):
    """Node in the topology graph."""

    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Type of node (service, database, etc.)")
    name: str = Field(..., description="Node name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Node metadata")


class TopologyEdge(BaseSchema):
    """Edge connecting two nodes in the topology."""

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="Type of relationship (calls, depends_on, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")


class TopologyRequest(BaseSchema):
    """Request for topology data."""

    service_name: Optional[str] = Field(
        default=None, description="Service to center topology around"
    )
    depth: int = Field(default=2, description="Depth of topology traversal")
    filters: Dict[str, str] = Field(default_factory=dict, description="Topology filters")


class TopologyResponse(BaseSchema):
    """Response containing topology data."""

    nodes: List[TopologyNode] = Field(..., description="Topology nodes")
    edges: List[TopologyEdge] = Field(..., description="Topology edges")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Audit Models
# ============================================================================


class AuditEvent(BaseSchema):
    """Audit event record."""

    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    actor: str = Field(..., description="User or service that performed the action")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    result: str = Field(..., description="Result (success, failure)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")


class AuditRequest(BaseSchema):
    """Request for audit events."""

    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    actor: Optional[str] = Field(default=None, description="Filter by actor")
    action: Optional[str] = Field(default=None, description="Filter by action")
    resource: Optional[str] = Field(default=None, description="Filter by resource")
    limit: int = Field(default=1000, description="Maximum number of events")


class AuditResponse(BaseSchema):
    """Response containing audit events."""

    events: List[AuditEvent] = Field(..., description="List of audit events")
    total_count: int = Field(..., description="Total number of matching events")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Cost Models
# ============================================================================


class CostBreakdown(BaseSchema):
    """Cost breakdown by dimension."""

    dimension: str = Field(..., description="Dimension name (service, region, etc.)")
    value: str = Field(..., description="Dimension value")
    cost: float = Field(..., description="Cost amount")
    currency: str = Field(..., description="Currency code (USD, EUR, etc.)")


class CostRequest(BaseSchema):
    """Request for cost data."""

    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    granularity: str = Field(
        default="daily", description="Granularity (daily, monthly)"
    )
    group_by: List[str] = Field(
        default_factory=list, description="Dimensions to group by"
    )
    filters: Dict[str, str] = Field(default_factory=dict, description="Cost filters")


class CostResponse(BaseSchema):
    """Response containing cost data."""

    total_cost: float = Field(..., description="Total cost for the period")
    currency: str = Field(..., description="Currency code")
    breakdown: List[CostBreakdown] = Field(..., description="Cost breakdown")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Changes Models
# ============================================================================


class ChangeEvent(BaseSchema):
    """Change event record."""

    timestamp: datetime = Field(..., description="When the change occurred")
    change_type: ChangeType = Field(..., description="Type of change")
    description: str = Field(..., description="Human-readable description")
    actor: str = Field(..., description="Who or what made the change")
    affected_resources: List[str] = Field(
        ..., description="Resources affected by the change"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional change metadata"
    )


class ChangesRequest(BaseSchema):
    """Request for change events."""

    service_name: str = Field(..., description="Service to query changes for")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    change_types: List[ChangeType] = Field(
        default_factory=list, description="Filter by change types"
    )


class ChangesResponse(BaseSchema):
    """Response containing change events."""

    changes: List[ChangeEvent] = Field(..., description="List of change events")
    source_provider: str = Field(..., description="Provider that supplied the data")


# ============================================================================
# Health Models
# ============================================================================


class AdapterHealthResponse(BaseSchema):
    """Health status of an adapter."""

    healthy: bool = Field(..., description="Whether the adapter is healthy")
    provider_name: str = Field(..., description="Name of the provider")
    provider_type: ProviderType = Field(..., description="Type of provider")
    latency_ms: Optional[int] = Field(
        default=None, description="Response latency in milliseconds"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if unhealthy"
    )
    last_check: datetime = Field(
        default_factory=datetime.utcnow, description="Last health check timestamp"
    )
