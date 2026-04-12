"""Provider registry for managing tenant-specific adapters.

The registry maintains mappings between tenants and their configured adapters.
It supports multi-instance deployments by persisting adapter configurations
to Redis and reconstructing adapter instances on demand.

Architecture:
    - Each tenant can have multiple adapters (e.g., AWS + Prometheus + PagerDuty)
    - Adapters are queried by capability (e.g., "give me all METRICS adapters")
    - Registry is singleton per tenant to avoid duplicate connections
    - Adapter configs (not instances) are serialized to Redis for persistence

Usage:
    ```python
    from app.adapters.registry import ProviderRegistry
    from app.adapters.models import AdapterCapability

    registry = ProviderRegistry(redis_client)

    # Register an adapter for a tenant
    await registry.register(tenant_id, aws_adapter)

    # Get all adapters that support metrics
    metrics_adapters = await registry.get_adapters(
        tenant_id,
        AdapterCapability.METRICS
    )

    # Get specific adapter by name
    aws = await registry.get_adapter(tenant_id, "aws")
    ```
"""

import json
from typing import Dict, List, Optional
from uuid import UUID

from redis.asyncio import Redis

from app.adapters.base import BaseAdapter
from app.adapters.exceptions import AdapterCapabilityError, AdapterNotRegisteredError
from app.adapters.models import AdapterCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdapterConfig:
    """Serializable adapter configuration.

    This class represents the configuration needed to reconstruct an adapter
    instance. It does not contain the adapter instance itself, making it
    suitable for Redis storage.
    """

    def __init__(
        self,
        provider_name: str,
        provider_type: str,
        config: Dict,
        supported_capabilities: List[str],
    ) -> None:
        """Initialize adapter configuration.

        Args:
            provider_name: Name of the provider
            provider_type: Type of provider
            config: Provider-specific configuration
            supported_capabilities: List of supported capabilities
        """
        self.provider_name = provider_name
        self.provider_type = provider_type
        self.config = config
        self.supported_capabilities = supported_capabilities

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "config": self.config,
            "supported_capabilities": self.supported_capabilities,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AdapterConfig":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AdapterConfig instance
        """
        return cls(
            provider_name=data["provider_name"],
            provider_type=data["provider_type"],
            config=data["config"],
            supported_capabilities=data["supported_capabilities"],
        )


class ProviderRegistry:
    """Registry for managing provider adapters per tenant.

    This class maintains the mapping between tenants and their configured
    adapters. It supports querying adapters by capability and persisting
    configurations to Redis for multi-instance deployments.
    """

    def __init__(self, redis_client: Optional[Redis] = None) -> None:
        """Initialize provider registry.

        Args:
            redis_client: Redis client for persistence (optional)
        """
        self.redis_client = redis_client
        # In-memory cache: {tenant_id: {provider_name: adapter_instance}}
        self._adapters: Dict[UUID, Dict[str, BaseAdapter]] = {}
        logger.info("provider_registry_initialized")

    def _get_redis_key(self, tenant_id: UUID) -> str:
        """Get Redis key for tenant adapters.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Redis key string
        """
        return f"adapters:tenant:{tenant_id}"

    async def register(
        self,
        tenant_id: UUID,
        adapter: BaseAdapter,
        persist: bool = True,
    ) -> None:
        """Register an adapter for a tenant.

        Args:
            tenant_id: Tenant UUID
            adapter: Adapter instance to register
            persist: Whether to persist to Redis

        Raises:
            ValueError: If adapter is invalid
        """
        if not isinstance(adapter, BaseAdapter):
            raise ValueError("Adapter must inherit from BaseAdapter")

        provider_name = adapter.provider_name

        # Add to in-memory cache
        if tenant_id not in self._adapters:
            self._adapters[tenant_id] = {}

        self._adapters[tenant_id][provider_name] = adapter

        logger.info(
            "adapter_registered",
            tenant_id=str(tenant_id),
            provider_name=provider_name,
            capabilities=list(adapter.get_supported_capabilities()),
        )

        # Persist to Redis if enabled
        if persist and self.redis_client:
            await self._persist_adapter_config(tenant_id, adapter)

    async def _persist_adapter_config(
        self, tenant_id: UUID, adapter: BaseAdapter
    ) -> None:
        """Persist adapter configuration to Redis.

        Note: This stores configuration, not the adapter instance itself.
        Adapter instances must be reconstructed from config on retrieval.

        Args:
            tenant_id: Tenant UUID
            adapter: Adapter instance
        """
        if not self.redis_client:
            return

        redis_key = self._get_redis_key(tenant_id)

        # Create serializable config
        # Note: In production, you'd extract actual config from adapter
        # This is a simplified version
        config = AdapterConfig(
            provider_name=adapter.provider_name,
            provider_type=adapter.provider_type.value,
            config={},  # Provider-specific config would go here
            supported_capabilities=[
                cap.value for cap in adapter.get_supported_capabilities()
            ],
        )

        # Store in Redis hash
        await self.redis_client.hset(
            redis_key,
            adapter.provider_name,
            json.dumps(config.to_dict()),
        )

        logger.debug(
            "adapter_config_persisted",
            tenant_id=str(tenant_id),
            provider_name=adapter.provider_name,
        )

    async def unregister(
        self, tenant_id: UUID, provider_name: str, persist: bool = True
    ) -> None:
        """Unregister an adapter for a tenant.

        Args:
            tenant_id: Tenant UUID
            provider_name: Name of the provider to unregister
            persist: Whether to persist to Redis
        """
        if tenant_id in self._adapters:
            self._adapters[tenant_id].pop(provider_name, None)

        if persist and self.redis_client:
            redis_key = self._get_redis_key(tenant_id)
            await self.redis_client.hdel(redis_key, provider_name)

        logger.info(
            "adapter_unregistered",
            tenant_id=str(tenant_id),
            provider_name=provider_name,
        )

    async def get_adapter(
        self, tenant_id: UUID, provider_name: str
    ) -> BaseAdapter:
        """Get a specific adapter by provider name.

        Args:
            tenant_id: Tenant UUID
            provider_name: Name of the provider

        Returns:
            Adapter instance

        Raises:
            AdapterNotRegisteredError: If adapter not found
        """
        if tenant_id not in self._adapters:
            raise AdapterNotRegisteredError(
                tenant_id=tenant_id,
                provider_name=provider_name,
                message=f"No adapters registered for tenant {tenant_id}",
            )

        adapter = self._adapters[tenant_id].get(provider_name)
        if not adapter:
            raise AdapterNotRegisteredError(
                tenant_id=tenant_id,
                provider_name=provider_name,
                message=f"Adapter '{provider_name}' not registered for tenant",
            )

        logger.debug(
            "adapter_retrieved",
            tenant_id=str(tenant_id),
            provider_name=provider_name,
        )

        return adapter

    async def get_adapters(
        self,
        tenant_id: UUID,
        capability: AdapterCapability,
    ) -> List[BaseAdapter]:
        """Get all adapters that support a specific capability.

        Args:
            tenant_id: Tenant UUID
            capability: Required capability

        Returns:
            List of adapters supporting the capability

        Raises:
            AdapterNotRegisteredError: If no adapters registered for tenant
        """
        if tenant_id not in self._adapters:
            raise AdapterNotRegisteredError(
                tenant_id=tenant_id,
                message=f"No adapters registered for tenant {tenant_id}",
            )

        adapters = [
            adapter
            for adapter in self._adapters[tenant_id].values()
            if adapter.supports_capability(capability)
        ]

        logger.debug(
            "adapters_retrieved_by_capability",
            tenant_id=str(tenant_id),
            capability=capability.value,
            count=len(adapters),
        )

        return adapters

    async def get_all_adapters(self, tenant_id: UUID) -> List[BaseAdapter]:
        """Get all adapters for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of all adapters

        Raises:
            AdapterNotRegisteredError: If no adapters registered
        """
        if tenant_id not in self._adapters:
            raise AdapterNotRegisteredError(
                tenant_id=tenant_id,
                message=f"No adapters registered for tenant {tenant_id}",
            )

        adapters = list(self._adapters[tenant_id].values())

        logger.debug(
            "all_adapters_retrieved",
            tenant_id=str(tenant_id),
            count=len(adapters),
        )

        return adapters

    async def list_providers(self, tenant_id: UUID) -> List[str]:
        """List all registered provider names for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of provider names
        """
        if tenant_id not in self._adapters:
            return []

        return list(self._adapters[tenant_id].keys())

    async def validate_capability(
        self,
        tenant_id: UUID,
        provider_name: str,
        capability: AdapterCapability,
    ) -> None:
        """Validate that an adapter supports a capability.

        Args:
            tenant_id: Tenant UUID
            provider_name: Name of the provider
            capability: Required capability

        Raises:
            AdapterNotRegisteredError: If adapter not found
            AdapterCapabilityError: If capability not supported
        """
        adapter = await self.get_adapter(tenant_id, provider_name)

        if not adapter.supports_capability(capability):
            raise AdapterCapabilityError(
                provider_name=provider_name,
                capability=capability.value,
                supported_capabilities=[
                    cap.value for cap in adapter.get_supported_capabilities()
                ],
            )

    async def health_check_all(self, tenant_id: UUID) -> Dict[str, bool]:
        """Perform health check on all adapters for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dictionary mapping provider names to health status
        """
        if tenant_id not in self._adapters:
            return {}

        results = {}
        for provider_name, adapter in self._adapters[tenant_id].items():
            try:
                health = await adapter.health_check()
                results[provider_name] = health.healthy
            except Exception as e:
                logger.error(
                    "adapter_health_check_failed",
                    tenant_id=str(tenant_id),
                    provider_name=provider_name,
                    error=str(e),
                )
                results[provider_name] = False

        return results
