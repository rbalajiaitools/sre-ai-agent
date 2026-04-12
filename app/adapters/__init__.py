"""Provider-agnostic adapter framework.

This module implements the adapter pattern to decouple agents from provider-specific APIs.
Agents interact with generic tool contracts, and adapters translate those contracts into
provider-specific API calls.

Architecture:
    - BaseAdapter: Abstract interface all providers must implement
    - ProviderRegistry: Maps tenants to their configured adapters
    - Shared Models: Provider-agnostic request/response models
    - Capability System: Adapters declare which capabilities they support

Adding a New Provider:
    1. Create a new adapter class inheriting from BaseAdapter
    2. Implement all abstract methods using provider's SDK
    3. Declare supported capabilities in the class
    4. Register the adapter instance for each tenant
    5. No agent code changes required
"""

from app.adapters.base import BaseAdapter
from app.adapters.exceptions import (
    AdapterCapabilityError,
    AdapterNotRegisteredError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.adapters.models import (
    AdapterCapability,
    AdapterHealthResponse,
    AuditRequest,
    AuditResponse,
    ChangeEvent,
    ChangesRequest,
    ChangesResponse,
    ChangeType,
    CostRequest,
    CostResponse,
    DataPoint,
    LogEntry,
    LogLevel,
    LogsRequest,
    LogsResponse,
    MetricSeries,
    MetricsRequest,
    MetricsResponse,
    ProviderType,
    Resource,
    ResourceHealth,
    ResourcesRequest,
    ResourcesResponse,
    ResourceStatus,
    ResourceType,
    TopologyRequest,
    TopologyResponse,
)
from app.adapters.registry import ProviderRegistry

__all__ = [
    # Base
    "BaseAdapter",
    # Registry
    "ProviderRegistry",
    # Enums
    "AdapterCapability",
    "ProviderType",
    "ResourceType",
    "ResourceStatus",
    "LogLevel",
    "ChangeType",
    # Request Models
    "MetricsRequest",
    "LogsRequest",
    "ResourcesRequest",
    "TopologyRequest",
    "AuditRequest",
    "CostRequest",
    "ChangesRequest",
    # Response Models
    "MetricsResponse",
    "LogsResponse",
    "ResourcesResponse",
    "TopologyResponse",
    "AuditResponse",
    "CostResponse",
    "ChangesResponse",
    "AdapterHealthResponse",
    # Data Models
    "MetricSeries",
    "DataPoint",
    "LogEntry",
    "Resource",
    "ResourceHealth",
    "ChangeEvent",
    # Exceptions
    "AdapterNotRegisteredError",
    "AdapterCapabilityError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
]
