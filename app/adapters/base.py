"""Abstract base adapter defining the provider-agnostic interface.

This module defines the contract that all provider adapters must implement.
Agents interact exclusively with this interface, never with provider-specific code.

Implementing a New Provider:
    1. Create a new class inheriting from BaseAdapter
    2. Implement all abstract methods
    3. Set the SUPPORTED_CAPABILITIES class attribute
    4. Implement provider_name and provider_type properties
    5. Use the provider's SDK within each method
    6. Translate provider responses to our shared models
    7. Handle provider-specific errors and convert to our exceptions

Example:
    ```python
    from app.adapters.base import BaseAdapter
    from app.adapters.models import (
        AdapterCapability,
        MetricsRequest,
        MetricsResponse,
        ProviderType,
    )

    class PrometheusAdapter(BaseAdapter):
        SUPPORTED_CAPABILITIES = {
            AdapterCapability.METRICS,
            AdapterCapability.LOGS,
        }

        def __init__(self, url: str, api_key: str):
            self.url = url
            self.api_key = api_key
            self.client = PrometheusClient(url, api_key)

        @property
        def provider_name(self) -> str:
            return "prometheus"

        @property
        def provider_type(self) -> ProviderType:
            return ProviderType.OBSERVABILITY

        async def get_metrics(
            self, request: MetricsRequest
        ) -> MetricsResponse:
            # Use Prometheus SDK to fetch metrics
            # Translate to our MetricsResponse model
            ...
    ```
"""

from abc import ABC, abstractmethod
from typing import Set

from app.adapters.models import (
    AdapterCapability,
    AdapterHealthResponse,
    AuditRequest,
    AuditResponse,
    ChangesRequest,
    ChangesResponse,
    CostRequest,
    CostResponse,
    LogsRequest,
    LogsResponse,
    MetricsRequest,
    MetricsResponse,
    ProviderType,
    ResourcesRequest,
    ResourcesResponse,
    TopologyRequest,
    TopologyResponse,
)


class BaseAdapter(ABC):
    """Abstract base class for all provider adapters.

    All provider adapters must inherit from this class and implement all
    abstract methods. This ensures a consistent interface across all providers.

    Attributes:
        SUPPORTED_CAPABILITIES: Set of capabilities this adapter supports.
            Must be defined as a class attribute in each implementation.
    """

    SUPPORTED_CAPABILITIES: Set[AdapterCapability] = set()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name (e.g., "aws", "azure", "gcp", "prometheus")
        """
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get the provider type.

        Returns:
            Provider type enum value
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate provider credentials.

        Returns:
            True if credentials are valid, False otherwise

        Raises:
            ProviderAuthError: If authentication fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> AdapterHealthResponse:
        """Perform health check on the adapter.

        Returns:
            Health status response

        Raises:
            ProviderTimeoutError: If health check times out
        """
        pass

    @abstractmethod
    async def get_metrics(self, request: MetricsRequest) -> MetricsResponse:
        """Retrieve metrics data.

        Args:
            request: Metrics request parameters

        Returns:
            Metrics response with time series data

        Raises:
            AdapterCapabilityError: If adapter doesn't support metrics
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def query_logs(self, request: LogsRequest) -> LogsResponse:
        """Query log data.

        Args:
            request: Logs request parameters

        Returns:
            Logs response with log entries

        Raises:
            AdapterCapabilityError: If adapter doesn't support logs
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def get_resources(self, request: ResourcesRequest) -> ResourcesResponse:
        """Retrieve infrastructure resources.

        Args:
            request: Resources request parameters

        Returns:
            Resources response with resource list

        Raises:
            AdapterCapabilityError: If adapter doesn't support resources
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def get_topology(self, request: TopologyRequest) -> TopologyResponse:
        """Retrieve service topology.

        Args:
            request: Topology request parameters

        Returns:
            Topology response with nodes and edges

        Raises:
            AdapterCapabilityError: If adapter doesn't support topology
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def get_audit_events(self, request: AuditRequest) -> AuditResponse:
        """Retrieve audit events.

        Args:
            request: Audit request parameters

        Returns:
            Audit response with event list

        Raises:
            AdapterCapabilityError: If adapter doesn't support audit
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def get_cost(self, request: CostRequest) -> CostResponse:
        """Retrieve cost data.

        Args:
            request: Cost request parameters

        Returns:
            Cost response with cost breakdown

        Raises:
            AdapterCapabilityError: If adapter doesn't support cost
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def get_recent_changes(self, request: ChangesRequest) -> ChangesResponse:
        """Retrieve recent changes.

        Args:
            request: Changes request parameters

        Returns:
            Changes response with change events

        Raises:
            AdapterCapabilityError: If adapter doesn't support changes
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        pass

    def supports_capability(self, capability: AdapterCapability) -> bool:
        """Check if adapter supports a specific capability.

        Args:
            capability: Capability to check

        Returns:
            True if capability is supported, False otherwise
        """
        return capability in self.SUPPORTED_CAPABILITIES

    def get_supported_capabilities(self) -> Set[AdapterCapability]:
        """Get all supported capabilities.

        Returns:
            Set of supported capabilities
        """
        return self.SUPPORTED_CAPABILITIES.copy()
