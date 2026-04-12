"""AWS resource discovery service."""

import asyncio
from typing import List

import boto3
from botocore.exceptions import ClientError

from app.adapters.models import Resource, ResourcesRequest, ResourcesResponse, ResourceType
from app.adapters.providers.aws.mappers import (
    map_ec2_instance,
    map_ecs_service,
    map_eks_nodegroup,
    map_lambda_function,
    map_rds_instance,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AWSResourceService:
    """Service for discovering AWS resources."""

    def __init__(self, session: boto3.Session) -> None:
        """Initialize AWS resource service.

        Args:
            session: Authenticated boto3 session
        """
        self.session = session

    async def discover_all(self, request: ResourcesRequest) -> ResourcesResponse:
        """Discover all requested resource types.

        Args:
            request: Resources request

        Returns:
            ResourcesResponse with discovered resources
        """
        logger.info(
            "discovering_aws_resources",
            resource_types=request.resource_types,
        )

        # Create tasks for each resource type
        tasks = []
        for resource_type in request.resource_types:
            if resource_type == ResourceType.COMPUTE:
                tasks.append(self._discover_ec2_instances(request))
            elif resource_type == ResourceType.CONTAINER:
                tasks.append(self._discover_ecs_services(request))
            elif resource_type == ResourceType.KUBERNETES_WORKLOAD:
                tasks.append(self._discover_eks_nodegroups(request))
            elif resource_type == ResourceType.DATABASE:
                tasks.append(self._discover_rds_instances(request))
            elif resource_type == ResourceType.SERVERLESS:
                tasks.append(self._discover_lambda_functions(request))

        # Execute all discovery tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_resources = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("resource_discovery_error", error=str(result))
                continue
            all_resources.extend(result)

        logger.info(
            "aws_resources_discovered",
            total_count=len(all_resources),
        )

        return ResourcesResponse(
            resources=all_resources,
            source_provider="aws",
        )

    async def _discover_ec2_instances(self, request: ResourcesRequest) -> List[Resource]:
        """Discover EC2 instances.

        Args:
            request: Resources request

        Returns:
            List of EC2 instance resources
        """
        def _sync_discover():
            resources = []
            try:
                ec2 = self.session.client("ec2")

                # Build filters
                filters = []
                for key, value in request.filters.items():
                    if key.startswith("tag:"):
                        filters.append({
                            "Name": key,
                            "Values": [value],
                        })

                response = ec2.describe_instances(Filters=filters if filters else [])

                for reservation in response.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        resource = map_ec2_instance(instance)
                        resources.append(resource)

                logger.info("ec2_instances_discovered", count=len(resources))

            except ClientError as e:
                logger.error("ec2_discovery_error", error=str(e))

            return resources

        return await asyncio.to_thread(_sync_discover)

    async def _discover_ecs_services(self, request: ResourcesRequest) -> List[Resource]:
        """Discover ECS services.

        Args:
            request: Resources request

        Returns:
            List of ECS service resources
        """
        def _sync_discover():
            resources = []
            try:
                ecs = self.session.client("ecs")

                # List clusters
                clusters_response = ecs.list_clusters()
                cluster_arns = clusters_response.get("clusterArns", [])

                for cluster_arn in cluster_arns:
                    cluster_name = cluster_arn.split("/")[-1]

                    # List services in cluster
                    services_response = ecs.list_services(cluster=cluster_arn)
                    service_arns = services_response.get("serviceArns", [])

                    if not service_arns:
                        continue

                    # Describe services
                    services_detail = ecs.describe_services(
                        cluster=cluster_arn,
                        services=service_arns,
                        include=["TAGS"],
                    )

                    for service in services_detail.get("services", []):
                        resource = map_ecs_service(service, cluster_name)
                        resources.append(resource)

                logger.info("ecs_services_discovered", count=len(resources))

            except ClientError as e:
                logger.error("ecs_discovery_error", error=str(e))

            return resources

        return await asyncio.to_thread(_sync_discover)

    async def _discover_eks_nodegroups(self, request: ResourcesRequest) -> List[Resource]:
        """Discover EKS node groups.

        Args:
            request: Resources request

        Returns:
            List of EKS node group resources
        """
        def _sync_discover():
            resources = []
            try:
                eks = self.session.client("eks")

                # List clusters
                clusters_response = eks.list_clusters()
                cluster_names = clusters_response.get("clusters", [])

                for cluster_name in cluster_names:
                    # List node groups
                    nodegroups_response = eks.list_nodegroups(clusterName=cluster_name)
                    nodegroup_names = nodegroups_response.get("nodegroups", [])

                    for nodegroup_name in nodegroup_names:
                        # Describe node group
                        nodegroup_detail = eks.describe_nodegroup(
                            clusterName=cluster_name,
                            nodegroupName=nodegroup_name,
                        )

                        nodegroup = nodegroup_detail.get("nodegroup", {})
                        resource = map_eks_nodegroup(nodegroup, cluster_name)
                        resources.append(resource)

                logger.info("eks_nodegroups_discovered", count=len(resources))

            except ClientError as e:
                logger.error("eks_discovery_error", error=str(e))

            return resources

        return await asyncio.to_thread(_sync_discover)

    async def _discover_rds_instances(self, request: ResourcesRequest) -> List[Resource]:
        """Discover RDS instances.

        Args:
            request: Resources request

        Returns:
            List of RDS instance resources
        """
        def _sync_discover():
            resources = []
            try:
                rds = self.session.client("rds")

                response = rds.describe_db_instances()

                for db_instance in response.get("DBInstances", []):
                    resource = map_rds_instance(db_instance)
                    resources.append(resource)

                logger.info("rds_instances_discovered", count=len(resources))

            except ClientError as e:
                logger.error("rds_discovery_error", error=str(e))

            return resources

        return await asyncio.to_thread(_sync_discover)

    async def _discover_lambda_functions(self, request: ResourcesRequest) -> List[Resource]:
        """Discover Lambda functions.

        Args:
            request: Resources request

        Returns:
            List of Lambda function resources
        """
        def _sync_discover():
            resources = []
            try:
                lambda_client = self.session.client("lambda")

                # List functions
                response = lambda_client.list_functions()

                for function in response.get("Functions", []):
                    resource = map_lambda_function(function)
                    resources.append(resource)

                # Handle pagination
                while response.get("NextMarker"):
                    response = lambda_client.list_functions(
                        Marker=response["NextMarker"]
                    )

                    for function in response.get("Functions", []):
                        resource = map_lambda_function(function)
                        resources.append(resource)

                logger.info("lambda_functions_discovered", count=len(resources))

            except ClientError as e:
                logger.error("lambda_discovery_error", error=str(e))

            return resources

        return await asyncio.to_thread(_sync_discover)
