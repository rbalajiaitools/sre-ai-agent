"""Resources tools for agents."""

from typing import List

from pydantic import BaseModel, Field

from app.adapters.models import AdapterCapability, ResourcesRequest, ResourceType
from app.agents.tools.base_tool import BaseAgentTool


class GetResourcesInput(BaseModel):
    """Input for GetResourcesTool."""

    service_name: str = Field(..., description="Name of the service to query")
    include_health: bool = Field(
        default=True, description="Include health status of resources"
    )


class GetResourcesTool(BaseAgentTool):
    """Tool for getting infrastructure resources and health status.

    This tool queries all adapters that support resources and merges results.
    Use this to check if containers are running, database health, autoscaling status.
    """

    name: str = "get_resources"
    description: str = """Get infrastructure resources and their health status. Use this 
    to check if containers are running, database instances are healthy, autoscaling groups 
    are at capacity, or if there are any infrastructure issues.
    
    Input: service name, whether to include health status.
    
    Returns resources from all connected cloud providers (AWS, Azure, GCP, etc.) including:
    - Compute instances (EC2, VMs)
    - Containers (ECS, Kubernetes pods)
    - Databases (RDS, Cloud SQL)
    - Serverless functions (Lambda, Cloud Functions)
    - Load balancers
    - Storage
    
    Each resource includes:
    - Current status (running, stopped, failed)
    - Health status (healthy, degraded, unhealthy)
    - Resource metadata (instance type, region, tags)
    
    Use this early in investigation to understand infrastructure state.
    """
    args_schema: type[BaseModel] = GetResourcesInput

    def _run(
        self,
        service_name: str,
        include_health: bool = True,
    ) -> str:
        """Execute the tool.

        Args:
            service_name: Service to query
            include_health: Include health status

        Returns:
            JSON string with results
        """

        def build_request():
            return ResourcesRequest(
                resource_types=[
                    ResourceType.COMPUTE,
                    ResourceType.CONTAINER,
                    ResourceType.DATABASE,
                    ResourceType.SERVERLESS,
                    ResourceType.LOAD_BALANCER,
                ],
                filters={"service": service_name},
                include_health=include_health,
            )

        import asyncio

        result = asyncio.run(
            self._run_across_providers(
                capability=AdapterCapability.RESOURCES,
                request_builder=build_request,
            )
        )

        return self._format_result(result)

    async def _arun(
        self,
        service_name: str,
        include_health: bool = True,
    ) -> str:
        """Async version of _run."""

        def build_request():
            return ResourcesRequest(
                resource_types=[
                    ResourceType.COMPUTE,
                    ResourceType.CONTAINER,
                    ResourceType.DATABASE,
                    ResourceType.SERVERLESS,
                    ResourceType.LOAD_BALANCER,
                ],
                filters={"service": service_name},
                include_health=include_health,
            )

        result = await self._run_across_providers(
            capability=AdapterCapability.RESOURCES,
            request_builder=build_request,
        )

        return self._format_result(result)
