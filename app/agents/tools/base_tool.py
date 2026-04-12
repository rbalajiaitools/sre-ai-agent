"""Base agent tool wrapping adapter calls.

CRITICAL: No provider-specific imports allowed. All provider interaction
happens through BaseAdapter via the registry.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain.tools import BaseTool
from pydantic import BaseModel

from app.adapters.base import BaseAdapter
from app.adapters.models import AdapterCapability
from app.adapters.registry import ProviderRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgentTool(BaseTool):
    """Base class for all agent tools.

    Wraps adapter calls and handles:
    - Provider resolution via registry
    - Concurrent queries across providers
    - Partial failure handling
    - Result merging and tagging
    """

    tenant_id: UUID
    registry: ProviderRegistry

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def _get_adapters(self, capability: AdapterCapability) -> List[BaseAdapter]:
        """Get all adapters supporting a capability.

        Args:
            capability: Required capability

        Returns:
            List of adapters
        """
        try:
            adapters = asyncio.run(
                self.registry.get_adapters(self.tenant_id, capability)
            )

            logger.info(
                "adapters_retrieved",
                tenant_id=str(self.tenant_id),
                capability=capability.value,
                count=len(adapters),
            )

            return adapters

        except Exception as e:
            logger.error(
                "adapter_retrieval_failed",
                tenant_id=str(self.tenant_id),
                capability=capability.value,
                error=str(e),
            )
            return []

    async def _run_across_providers(
        self,
        capability: AdapterCapability,
        request_builder: callable,
    ) -> Dict[str, Any]:
        """Run request across all providers supporting capability.

        Handles partial failures - if one provider fails, log and continue.

        Args:
            capability: Required capability
            request_builder: Function that builds the request object

        Returns:
            Dict with merged results and metadata
        """
        adapters = self._get_adapters(capability)

        if not adapters:
            logger.warning(
                "no_adapters_found",
                tenant_id=str(self.tenant_id),
                capability=capability.value,
            )
            return {
                "success": False,
                "error": f"No adapters found for capability: {capability.value}",
                "results": [],
                "providers_queried": [],
            }

        # Build request
        try:
            request = request_builder()
        except Exception as e:
            logger.error("request_build_failed", error=str(e))
            return {
                "success": False,
                "error": f"Failed to build request: {str(e)}",
                "results": [],
                "providers_queried": [],
            }

        # Query all adapters concurrently
        tasks = []
        for adapter in adapters:
            task = self._query_adapter(adapter, capability, request)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = []
        providers_queried = []
        errors = []

        for adapter, result in zip(adapters, results):
            provider_name = adapter.provider_name

            if isinstance(result, Exception):
                logger.error(
                    "adapter_query_failed",
                    provider=provider_name,
                    error=str(result),
                )
                errors.append(f"{provider_name}: {str(result)}")
            else:
                successful_results.append({
                    "provider": provider_name,
                    "data": result,
                })
                providers_queried.append(provider_name)

        return {
            "success": len(successful_results) > 0,
            "results": successful_results,
            "providers_queried": providers_queried,
            "errors": errors if errors else None,
        }

    async def _query_adapter(
        self,
        adapter: BaseAdapter,
        capability: AdapterCapability,
        request: Any,
    ) -> Any:
        """Query a single adapter.

        Args:
            adapter: Adapter to query
            capability: Capability being used
            request: Request object

        Returns:
            Response from adapter
        """
        logger.debug(
            "querying_adapter",
            provider=adapter.provider_name,
            capability=capability.value,
        )

        # Route to appropriate adapter method based on capability
        if capability == AdapterCapability.METRICS:
            return await adapter.get_metrics(request)
        elif capability == AdapterCapability.LOGS:
            return await adapter.query_logs(request)
        elif capability == AdapterCapability.RESOURCES:
            return await adapter.get_resources(request)
        elif capability == AdapterCapability.CHANGES:
            return await adapter.get_recent_changes(request)
        elif capability == AdapterCapability.AUDIT:
            return await adapter.get_audit_events(request)
        elif capability == AdapterCapability.COST:
            return await adapter.get_cost(request)
        else:
            raise ValueError(f"Unsupported capability: {capability}")

    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format result as JSON string for agent consumption.

        Args:
            result: Result dictionary

        Returns:
            JSON string
        """
        # Convert Pydantic models to dicts
        formatted = {
            "success": result.get("success", False),
            "providers_queried": result.get("providers_queried", []),
            "results": [],
        }

        for provider_result in result.get("results", []):
            provider = provider_result["provider"]
            data = provider_result["data"]

            # Convert Pydantic model to dict
            if hasattr(data, "model_dump"):
                data_dict = data.model_dump()
            else:
                data_dict = data

            formatted["results"].append({
                "provider": provider,
                "data": data_dict,
            })

        if result.get("errors"):
            formatted["errors"] = result["errors"]

        return json.dumps(formatted, default=str, indent=2)
