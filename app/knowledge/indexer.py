"""Discovery indexer for automatic graph population."""

import re
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.adapters.models import DiscoveryResult, DiscoveredResource, DiscoveredService
from app.core.logging import get_logger
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.models import ResourceNode, ServiceNode

logger = get_logger(__name__)


class DiscoveryIndexer:
    """Indexes provider discovery results into the knowledge graph.

    Automatically creates/updates ServiceNodes and ResourceNodes.
    Infers dependencies from resource metadata.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph) -> None:
        """Initialize discovery indexer.

        Args:
            knowledge_graph: Knowledge graph instance
        """
        self.graph = knowledge_graph

        logger.info("discovery_indexer_initialized")

    async def index_discovery_result(
        self,
        tenant_id: UUID,
        discovery_result: DiscoveryResult,
    ) -> None:
        """Index discovery result into knowledge graph.

        Args:
            tenant_id: Tenant UUID
            discovery_result: Discovery result from adapter
        """
        try:
            tenant_id_str = str(tenant_id)

            logger.info(
                "indexing_discovery_result",
                tenant_id=tenant_id_str,
                provider=discovery_result.provider,
                services_count=len(discovery_result.services),
                resources_count=len(discovery_result.resources),
            )

            # Index services
            for service in discovery_result.services:
                await self._index_service(tenant_id_str, service, discovery_result.provider)

            # Index resources
            for resource in discovery_result.resources:
                await self._index_resource(tenant_id_str, resource, discovery_result.provider)

            # Create RUNS_ON relationships
            await self._create_runs_on_relationships(
                tenant_id_str,
                discovery_result.services,
                discovery_result.resources,
            )

            # Infer dependencies
            await self._infer_dependencies(
                tenant_id_str,
                discovery_result.services,
                discovery_result.resources,
            )

            logger.info(
                "discovery_result_indexed",
                tenant_id=tenant_id_str,
                provider=discovery_result.provider,
            )

        except Exception as e:
            logger.error(
                "discovery_indexing_failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            raise

    async def _index_service(
        self,
        tenant_id: str,
        service: DiscoveredService,
        provider: str,
    ) -> None:
        """Index a discovered service.

        Args:
            tenant_id: Tenant UUID
            service: Discovered service
            provider: Provider name
        """
        try:
            service_node = ServiceNode(
                name=service.name,
                type=service.type,
                tenant_id=tenant_id,
                provider=provider,
                region=service.region,
                metadata=service.metadata,
            )

            await self.graph.upsert_service(tenant_id, service_node)

            logger.debug(
                "service_indexed",
                tenant_id=tenant_id,
                service_name=service.name,
            )

        except Exception as e:
            logger.error(
                "service_indexing_failed",
                tenant_id=tenant_id,
                service_name=service.name,
                error=str(e),
            )
            # Don't fail entire indexing for one service
            pass

    async def _index_resource(
        self,
        tenant_id: str,
        resource: DiscoveredResource,
        provider: str,
    ) -> None:
        """Index a discovered resource.

        Args:
            tenant_id: Tenant UUID
            resource: Discovered resource
            provider: Provider name
        """
        try:
            resource_node = ResourceNode(
                resource_id=resource.resource_id,
                type=resource.type,
                name=resource.name,
                tenant_id=tenant_id,
                provider=provider,
                status=resource.status,
                metadata=resource.metadata,
            )

            await self.graph.upsert_resource(tenant_id, resource_node)

            logger.debug(
                "resource_indexed",
                tenant_id=tenant_id,
                resource_id=resource.resource_id,
            )

        except Exception as e:
            logger.error(
                "resource_indexing_failed",
                tenant_id=tenant_id,
                resource_id=resource.resource_id,
                error=str(e),
            )
            # Don't fail entire indexing for one resource
            pass

    async def _create_runs_on_relationships(
        self,
        tenant_id: str,
        services: List[DiscoveredService],
        resources: List[DiscoveredResource],
    ) -> None:
        """Create RUNS_ON relationships between services and resources.

        Args:
            tenant_id: Tenant UUID
            services: Discovered services
            resources: Discovered resources
        """
        # Build resource lookup by tags
        resource_by_service: Dict[str, List[str]] = {}

        for resource in resources:
            # Check for service tag
            service_name = resource.metadata.get("service")
            if not service_name:
                # Try common tag names
                for tag_key in ["Service", "service", "app", "application"]:
                    service_name = resource.metadata.get(tag_key)
                    if service_name:
                        break

            if service_name:
                if service_name not in resource_by_service:
                    resource_by_service[service_name] = []
                resource_by_service[service_name].append(resource.resource_id)

        # Create relationships
        for service in services:
            if service.name in resource_by_service:
                for resource_id in resource_by_service[service.name]:
                    try:
                        await self.graph.add_runs_on(
                            tenant_id,
                            service.name,
                            resource_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "runs_on_creation_failed",
                            service=service.name,
                            resource=resource_id,
                            error=str(e),
                        )

    async def _infer_dependencies(
        self,
        tenant_id: str,
        services: List[DiscoveredService],
        resources: List[DiscoveredResource],
    ) -> None:
        """Infer service dependencies from resource metadata.

        Looks for patterns like:
        - Environment variables with database endpoints
        - RDS endpoints in ECS task definitions
        - Service mesh configurations
        - API Gateway integrations

        Args:
            tenant_id: Tenant UUID
            services: Discovered services
            resources: Discovered resources
        """
        # Build service name set for validation
        service_names = {s.name for s in services}

        # Build resource lookup
        resources_by_id = {r.resource_id: r for r in resources}

        # Track inferred dependencies to avoid duplicates
        inferred_deps: Set[tuple] = set()

        for service in services:
            # Check service metadata for dependency hints
            dependencies = self._extract_dependencies_from_metadata(
                service.metadata,
                service_names,
            )

            for dep_service in dependencies:
                dep_key = (service.name, dep_service)
                if dep_key not in inferred_deps:
                    try:
                        await self.graph.add_dependency(
                            tenant_id,
                            service.name,
                            dep_service,
                        )
                        inferred_deps.add(dep_key)

                        logger.info(
                            "dependency_inferred",
                            from_service=service.name,
                            to_service=dep_service,
                            source="metadata",
                        )

                    except Exception as e:
                        logger.warning(
                            "dependency_inference_failed",
                            from_service=service.name,
                            to_service=dep_service,
                            error=str(e),
                        )

        # Check resources for dependency hints
        for resource in resources:
            dependencies = self._extract_dependencies_from_metadata(
                resource.metadata,
                service_names,
            )

            # Find which service owns this resource
            service_name = resource.metadata.get("service")
            if service_name and service_name in service_names:
                for dep_service in dependencies:
                    dep_key = (service_name, dep_service)
                    if dep_key not in inferred_deps:
                        try:
                            await self.graph.add_dependency(
                                tenant_id,
                                service_name,
                                dep_service,
                            )
                            inferred_deps.add(dep_key)

                            logger.info(
                                "dependency_inferred",
                                from_service=service_name,
                                to_service=dep_service,
                                source="resource_metadata",
                            )

                        except Exception as e:
                            logger.warning(
                                "dependency_inference_failed",
                                from_service=service_name,
                                to_service=dep_service,
                                error=str(e),
                            )

    def _extract_dependencies_from_metadata(
        self,
        metadata: Dict[str, any],
        valid_service_names: Set[str],
    ) -> List[str]:
        """Extract service dependencies from metadata.

        Args:
            metadata: Resource or service metadata
            valid_service_names: Set of valid service names

        Returns:
            List of inferred dependency service names
        """
        dependencies = []

        # Patterns to look for
        patterns = [
            # Database endpoints
            r"([a-z0-9-]+)\.([a-z0-9-]+)\.rds\.amazonaws\.com",
            r"([a-z0-9-]+)\.database\.windows\.net",
            r"([a-z0-9-]+)\.postgres\.database\.azure\.com",
            # Service endpoints
            r"([a-z0-9-]+)-service",
            r"([a-z0-9-]+)-api",
            # Queue names
            r"([a-z0-9-]+)-queue",
            r"([a-z0-9-]+)-topic",
        ]

        # Check all metadata values
        for key, value in metadata.items():
            if not isinstance(value, str):
                continue

            # Check for direct service name references
            if value in valid_service_names:
                dependencies.append(value)
                continue

            # Check patterns
            for pattern in patterns:
                matches = re.findall(pattern, value, re.IGNORECASE)
                for match in matches:
                    # Extract service name from match
                    if isinstance(match, tuple):
                        service_name = match[0]
                    else:
                        service_name = match

                    # Validate against known services
                    if service_name in valid_service_names:
                        dependencies.append(service_name)

        return list(set(dependencies))  # Remove duplicates

    async def index_service_dependencies(
        self,
        tenant_id: UUID,
        service_name: str,
        dependencies: List[str],
    ) -> None:
        """Manually index service dependencies.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name
            dependencies: List of service names this service depends on
        """
        tenant_id_str = str(tenant_id)

        for dep_service in dependencies:
            try:
                await self.graph.add_dependency(
                    tenant_id_str,
                    service_name,
                    dep_service,
                )

                logger.info(
                    "manual_dependency_added",
                    tenant_id=tenant_id_str,
                    from_service=service_name,
                    to_service=dep_service,
                )

            except Exception as e:
                logger.error(
                    "manual_dependency_failed",
                    tenant_id=tenant_id_str,
                    from_service=service_name,
                    to_service=dep_service,
                    error=str(e),
                )

    async def run_scheduled_indexing(
        self,
        tenant_id: UUID,
        discovery_results: List[DiscoveryResult],
    ) -> None:
        """Run scheduled indexing for multiple discovery results.

        This should be called daily to keep the graph updated.

        Args:
            tenant_id: Tenant UUID
            discovery_results: List of discovery results from all providers
        """
        logger.info(
            "scheduled_indexing_started",
            tenant_id=str(tenant_id),
            providers_count=len(discovery_results),
        )

        for result in discovery_results:
            try:
                await self.index_discovery_result(tenant_id, result)
            except Exception as e:
                logger.error(
                    "scheduled_indexing_provider_failed",
                    tenant_id=str(tenant_id),
                    provider=result.provider,
                    error=str(e),
                )
                # Continue with other providers

        logger.info(
            "scheduled_indexing_completed",
            tenant_id=str(tenant_id),
        )
