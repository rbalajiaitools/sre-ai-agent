"""Logs tools for agents."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from app.adapters.models import AdapterCapability, LogLevel, LogsRequest
from app.agents.tools.base_tool import BaseAgentTool


class QueryLogsInput(BaseModel):
    """Input for QueryLogsTool."""

    service_name: str = Field(..., description="Name of the service to query")
    query: str = Field(..., description="Search query or pattern to find in logs")
    lookback_minutes: int = Field(
        default=60, description="How many minutes to look back"
    )
    log_level: Optional[str] = Field(
        default=None, description="Filter by log level (ERROR, WARNING, INFO, DEBUG)"
    )


class QueryLogsTool(BaseAgentTool):
    """Tool for searching logs across all connected providers.

    This tool queries all adapters that support logs and merges results.
    Use this to find errors, exceptions, or specific patterns.
    """

    name: str = "query_logs"
    description: str = """Search logs for a service. Use this to find errors, exceptions, 
    stack traces, or specific patterns in application logs.
    
    Input: service name, search query, lookback time in minutes, optional log level filter.
    
    Returns log entries from all connected log providers (Datadog, CloudWatch Logs, 
    Splunk, etc.). Each result is tagged with the source provider.
    
    Useful queries:
    - "ERROR" or "Exception" (find errors)
    - "OutOfMemoryError" (specific error types)
    - "connection timeout" (connection issues)
    - "database" (database-related logs)
    - "status code 500" (HTTP errors)
    
    Always check logs when investigating incidents - they often contain the root cause.
    """
    args_schema: type[BaseModel] = QueryLogsInput

    def _run(
        self,
        service_name: str,
        query: str,
        lookback_minutes: int = 60,
        log_level: Optional[str] = None,
    ) -> str:
        """Execute the tool.

        Args:
            service_name: Service to query
            query: Search query
            lookback_minutes: Lookback period
            log_level: Optional log level filter

        Returns:
            JSON string with results
        """
        level = None
        if log_level:
            try:
                level = LogLevel(log_level.lower())
            except ValueError:
                pass

        def build_request():
            return LogsRequest(
                service_name=service_name,
                query=query,
                start_time=datetime.utcnow() - timedelta(minutes=lookback_minutes),
                end_time=datetime.utcnow(),
                limit=100,
                log_level=level,
            )

        import asyncio

        result = asyncio.run(
            self._run_across_providers(
                capability=AdapterCapability.LOGS,
                request_builder=build_request,
            )
        )

        return self._format_result(result)

    async def _arun(
        self,
        service_name: str,
        query: str,
        lookback_minutes: int = 60,
        log_level: Optional[str] = None,
    ) -> str:
        """Async version of _run."""
        level = None
        if log_level:
            try:
                level = LogLevel(log_level.lower())
            except ValueError:
                pass

        def build_request():
            return LogsRequest(
                service_name=service_name,
                query=query,
                start_time=datetime.utcnow() - timedelta(minutes=lookback_minutes),
                end_time=datetime.utcnow(),
                limit=100,
                log_level=level,
            )

        result = await self._run_across_providers(
            capability=AdapterCapability.LOGS,
            request_builder=build_request,
        )

        return self._format_result(result)
