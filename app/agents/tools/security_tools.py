"""Security tools for agents."""

from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from app.adapters.models import AdapterCapability, AuditRequest
from app.agents.tools.base_tool import BaseAgentTool


class GetAuditEventsInput(BaseModel):
    """Input for GetAuditEventsTool."""

    service_name: str = Field(..., description="Name of the service to query")
    lookback_hours: int = Field(
        default=24, description="How many hours to look back for audit events"
    )


class GetAuditEventsTool(BaseAgentTool):
    """Tool for getting audit trail events.

    This tool queries all adapters that support audit and merges results.
    Use for security-related incidents.
    """

    name: str = "get_audit_events"
    description: str = """Get audit trail events including IAM changes, permission changes, 
    unusual API calls, and security-related activities.
    
    Input: service name, lookback time in hours.
    
    Returns audit events from all connected sources (CloudTrail, Azure Activity Log, etc.) including:
    - IAM role/policy changes
    - Permission modifications
    - Resource access attempts
    - API calls (especially unusual or failed ones)
    - Security group changes
    - Credential usage
    
    Use this for security-related incidents or when investigating:
    - Access denied errors
    - Permission issues
    - Unusual activity patterns
    - Potential security breaches
    
    Each event includes who did what, when, and whether it succeeded or failed.
    """
    args_schema: type[BaseModel] = GetAuditEventsInput

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
            return AuditRequest(
                start_time=datetime.utcnow() - timedelta(hours=lookback_hours),
                end_time=datetime.utcnow(),
                limit=100,
            )

        import asyncio

        result = asyncio.run(
            self._run_across_providers(
                capability=AdapterCapability.AUDIT,
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
            return AuditRequest(
                start_time=datetime.utcnow() - timedelta(hours=lookback_hours),
                end_time=datetime.utcnow(),
                limit=100,
            )

        result = await self._run_across_providers(
            capability=AdapterCapability.AUDIT,
            request_builder=build_request,
        )

        return self._format_result(result)
