"""Changes tools for agents."""

from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from app.adapters.models import AdapterCapability, ChangesRequest
from app.agents.tools.base_tool import BaseAgentTool


class GetRecentChangesInput(BaseModel):
    """Input for GetRecentChangesTool."""

    service_name: str = Field(..., description="Name of the service to query")
    lookback_hours: int = Field(
        default=24, description="How many hours to look back for changes"
    )


class GetRecentChangesTool(BaseAgentTool):
    """Tool for getting recent changes, deployments, and configuration updates.

    This tool queries all adapters that support changes and merges results.
    ALWAYS use this early in an investigation - many incidents are caused by recent changes.
    """

    name: str = "get_recent_changes"
    description: str = """Get recent deployments, configuration changes, scaling events, 
    and infrastructure changes. ALWAYS use this tool early in an investigation because 
    many incidents are caused by recent changes.
    
    Input: service name, lookback time in hours (default 24).
    
    Returns change events from all connected sources including:
    - Deployments (new code releases)
    - Configuration changes (environment variables, feature flags)
    - Scaling events (autoscaling, manual scaling)
    - Infrastructure changes (resource modifications)
    - Code merges (from GitHub, GitLab, etc.)
    - Restarts and reboots
    
    Each change includes:
    - What changed
    - When it changed
    - Who made the change
    - Affected resources
    
    Look for changes that occurred shortly before the incident started - this is often 
    the root cause. Pay special attention to:
    - Deployments within 1 hour of incident
    - Configuration changes
    - Scaling events that might have caused capacity issues
    
    This is one of the most important tools for incident investigation.
    """
    args_schema: type[BaseModel] = GetRecentChangesInput

    def _run(
        self,
        service_name: str,
        lookback_hours: int = 24,
    ) -> str:
        """Execute the tool.

        Args:
            service_name: Service to query
            lookback_hours: Lookback period in hours

        Returns:
            JSON string with results
        """

        def build_request():
            return ChangesRequest(
                service_name=service_name,
                start_time=datetime.utcnow() - timedelta(hours=lookback_hours),
                end_time=datetime.utcnow(),
                change_types=[],  # All types
            )

        import asyncio

        result = asyncio.run(
            self._run_across_providers(
                capability=AdapterCapability.CHANGES,
                request_builder=build_request,
            )
        )

        return self._format_result(result)

    async def _arun(
        self,
        service_name: str,
        lookback_hours: int = 24,
    ) -> str:
        """Async version of _run."""

        def build_request():
            return ChangesRequest(
                service_name=service_name,
                start_time=datetime.utcnow() - timedelta(hours=lookback_hours),
                end_time=datetime.utcnow(),
                change_types=[],  # All types
            )

        result = await self._run_across_providers(
            capability=AdapterCapability.CHANGES,
            request_builder=build_request,
        )

        return self._format_result(result)
