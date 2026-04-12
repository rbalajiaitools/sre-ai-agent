"""Metrics tools for agents."""

from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field

from app.adapters.models import AdapterCapability, MetricsRequest
from app.agents.tools.base_tool import BaseAgentTool


class GetMetricsInput(BaseModel):
    """Input for GetMetricsTool."""

    service_name: str = Field(..., description="Name of the service to query")
    metric_names: List[str] = Field(
        default_factory=lambda: [
            "cpu_usage",
            "memory_usage",
            "error_rate",
            "request_rate",
            "latency_p50",
            "latency_p95",
            "latency_p99",
        ],
        description="List of metric names to retrieve",
    )
    lookback_minutes: int = Field(
        default=60, description="How many minutes to look back"
    )


class GetMetricsTool(BaseAgentTool):
    """Tool for retrieving metrics from all connected providers.

    This tool queries all adapters that support metrics and merges results.
    Use this to check CPU, memory, error rates, latency, throughput.
    """

    name: str = "get_metrics"
    description: str = """Retrieve metrics for a service. Use this to check CPU usage, 
    memory usage, error rates, latency percentiles (p50, p95, p99), and request throughput. 
    
    Input: service name, optional list of metric names, and lookback time in minutes.
    
    Returns time series data from all connected monitoring providers (Datadog, Prometheus, 
    CloudWatch, etc.). Each result is tagged with the source provider.
    
    Example metrics to query:
    - cpu_usage, memory_usage (resource utilization)
    - error_rate, request_rate (traffic patterns)
    - latency_p50, latency_p95, latency_p99 (performance)
    - connection_pool_usage (database connections)
    """
    args_schema: type[BaseModel] = GetMetricsInput

    def _run(
        self,
        service_name: str,
        metric_names: List[str] = None,
        lookback_minutes: int = 60,
    ) -> str:
        """Execute the tool.

        Args:
            service_name: Service to query
            metric_names: Metrics to retrieve
            lookback_minutes: Lookback period

        Returns:
            JSON string with results
        """
        if metric_names is None:
            metric_names = GetMetricsInput().metric_names

        def build_request():
            return MetricsRequest(
                service_name=service_name,
                metric_names=metric_names,
                start_time=datetime.utcnow() - timedelta(minutes=lookback_minutes),
                end_time=datetime.utcnow(),
                granularity_seconds=60,
                filters={},
            )

        import asyncio

        result = asyncio.run(
            self._run_across_providers(
                capability=AdapterCapability.METRICS,
                request_builder=build_request,
            )
        )

        return self._format_result(result)

    async def _arun(
        self,
        service_name: str,
        metric_names: List[str] = None,
        lookback_minutes: int = 60,
    ) -> str:
        """Async version of _run."""
        if metric_names is None:
            metric_names = GetMetricsInput().metric_names

        def build_request():
            return MetricsRequest(
                service_name=service_name,
                metric_names=metric_names,
                start_time=datetime.utcnow() - timedelta(minutes=lookback_minutes),
                end_time=datetime.utcnow(),
                granularity_seconds=60,
                filters={},
            )

        result = await self._run_across_providers(
            capability=AdapterCapability.METRICS,
            request_builder=build_request,
        )

        return self._format_result(result)
