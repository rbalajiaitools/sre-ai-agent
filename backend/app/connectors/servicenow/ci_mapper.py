"""CI to resource mapper using knowledge graph."""

from typing import List
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.adapters.registry import ProviderRegistry
from app.connectors.servicenow.models import MappedResource
from app.core.logging import get_logger

logger = get_logger(__name__)


class CIMapper:
    """Maps ServiceNow CMDB CI names to platform resources.

    Uses the knowledge graph (Neo4j) to find matching resources across
    all registered adapters. Supports fuzzy matching for CI names that
    don't exactly match resource names.
    """

    def __init__(
        self,
        neo4j_driver: AsyncDriver,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Initialize CI mapper.

        Args:
            neo4j_driver: Neo4j async driver
            provider_registry: Provider registry
        """
        self.neo4j_driver = neo4j_driver
        self.provider_registry = provider_registry

        logger.info("ci_mapper_initialized")

    async def map_ci_to_resources(
        self,
        tenant_id: UUID,
        ci_name: str,
    ) -> List[MappedResource]:
        """Map CI name to platform resources.

        Searches across all registered adapters for matching resources.
        Uses fuzzy matching if exact match not found.

        Args:
            tenant_id: Tenant UUID
            ci_name: CMDB CI name from ServiceNow

        Returns:
            List of mapped resources with confidence scores
        """
        logger.info(
            "mapping_ci_to_resources",
            tenant_id=str(tenant_id),
            ci_name=ci_name,
        )

        if not ci_name:
            return []

        mapped_resources = []

        # Try exact match first
        exact_matches = await self._find_exact_matches(tenant_id, ci_name)
        mapped_resources.extend(exact_matches)

        # If no exact matches, try fuzzy matching
        if not exact_matches:
            fuzzy_matches = await self._find_fuzzy_matches(tenant_id, ci_name)
            mapped_resources.extend(fuzzy_matches)

        logger.info(
            "ci_mapping_complete",
            tenant_id=str(tenant_id),
            ci_name=ci_name,
            matches=len(mapped_resources),
        )

        return mapped_resources

    async def _find_exact_matches(
        self,
        tenant_id: UUID,
        ci_name: str,
    ) -> List[MappedResource]:
        """Find exact matches in knowledge graph.

        Args:
            tenant_id: Tenant UUID
            ci_name: CI name

        Returns:
            List of exact matches
        """
        matches = []

        try:
            async with self.neo4j_driver.session() as session:
                # Query Neo4j for resources with matching name
                query = """
                MATCH (r:Resource {tenant_id: $tenant_id})
                WHERE r.name = $ci_name OR r.resource_id = $ci_name
                RETURN r.adapter_name as adapter_name,
                       r.provider_name as provider_name,
                       r.resource_id as resource_id,
                       r.resource_name as resource_name
                """

                result = await session.run(
                    query,
                    tenant_id=str(tenant_id),
                    ci_name=ci_name,
                )

                async for record in result:
                    matches.append(
                        MappedResource(
                            adapter_name=record["adapter_name"],
                            provider_name=record["provider_name"],
                            resource_id=record["resource_id"],
                            resource_name=record["resource_name"],
                            confidence_score=1.0,  # Exact match
                        )
                    )

        except Exception as e:
            logger.error(
                "exact_match_query_failed",
                tenant_id=str(tenant_id),
                ci_name=ci_name,
                error=str(e),
            )

        return matches

    async def _find_fuzzy_matches(
        self,
        tenant_id: UUID,
        ci_name: str,
    ) -> List[MappedResource]:
        """Find fuzzy matches using similarity algorithms.

        Args:
            tenant_id: Tenant UUID
            ci_name: CI name

        Returns:
            List of fuzzy matches with confidence scores
        """
        matches = []

        try:
            async with self.neo4j_driver.session() as session:
                # Use Levenshtein distance or similar for fuzzy matching
                # This is a simplified version - in production, use proper
                # fuzzy matching algorithms
                query = """
                MATCH (r:Resource {tenant_id: $tenant_id})
                WHERE r.name CONTAINS $ci_name_lower
                   OR $ci_name_lower CONTAINS toLower(r.name)
                RETURN r.adapter_name as adapter_name,
                       r.provider_name as provider_name,
                       r.resource_id as resource_id,
                       r.resource_name as resource_name,
                       r.name as actual_name
                LIMIT 10
                """

                result = await session.run(
                    query,
                    tenant_id=str(tenant_id),
                    ci_name_lower=ci_name.lower(),
                )

                async for record in result:
                    # Calculate confidence score based on similarity
                    confidence = self._calculate_similarity(
                        ci_name,
                        record["actual_name"],
                    )

                    if confidence > 0.5:  # Only include if > 50% similar
                        matches.append(
                            MappedResource(
                                adapter_name=record["adapter_name"],
                                provider_name=record["provider_name"],
                                resource_id=record["resource_id"],
                                resource_name=record["resource_name"],
                                confidence_score=confidence,
                            )
                        )

        except Exception as e:
            logger.error(
                "fuzzy_match_query_failed",
                tenant_id=str(tenant_id),
                ci_name=ci_name,
                error=str(e),
            )

        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)

        return matches

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.

        Uses a simple algorithm. In production, use proper similarity
        algorithms like Levenshtein distance, Jaro-Winkler, etc.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        # Exact match
        if str1_lower == str2_lower:
            return 1.0

        # One contains the other
        if str1_lower in str2_lower or str2_lower in str1_lower:
            # Calculate ratio of lengths
            shorter = min(len(str1_lower), len(str2_lower))
            longer = max(len(str1_lower), len(str2_lower))
            return shorter / longer

        # Calculate word overlap
        words1 = set(str1_lower.split())
        words2 = set(str2_lower.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    async def store_resource_mapping(
        self,
        tenant_id: UUID,
        ci_name: str,
        adapter_name: str,
        provider_name: str,
        resource_id: str,
        resource_name: str,
    ) -> bool:
        """Store resource mapping in knowledge graph.

        Args:
            tenant_id: Tenant UUID
            ci_name: CI name from ServiceNow
            adapter_name: Adapter name
            provider_name: Provider name
            resource_id: Resource ID
            resource_name: Resource name

        Returns:
            True if successful
        """
        try:
            async with self.neo4j_driver.session() as session:
                query = """
                MERGE (r:Resource {
                    tenant_id: $tenant_id,
                    resource_id: $resource_id
                })
                SET r.adapter_name = $adapter_name,
                    r.provider_name = $provider_name,
                    r.resource_name = $resource_name,
                    r.name = $resource_name,
                    r.ci_name = $ci_name,
                    r.updated_at = datetime()
                """

                await session.run(
                    query,
                    tenant_id=str(tenant_id),
                    ci_name=ci_name,
                    adapter_name=adapter_name,
                    provider_name=provider_name,
                    resource_id=resource_id,
                    resource_name=resource_name,
                )

                logger.info(
                    "resource_mapping_stored",
                    tenant_id=str(tenant_id),
                    ci_name=ci_name,
                    resource_id=resource_id,
                )

                return True

        except Exception as e:
            logger.error(
                "resource_mapping_storage_failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return False

    async def get_ci_for_resource(
        self,
        tenant_id: UUID,
        resource_id: str,
    ) -> str | None:
        """Get CI name for a resource.

        Args:
            tenant_id: Tenant UUID
            resource_id: Resource ID

        Returns:
            CI name if found, None otherwise
        """
        try:
            async with self.neo4j_driver.session() as session:
                query = """
                MATCH (r:Resource {
                    tenant_id: $tenant_id,
                    resource_id: $resource_id
                })
                RETURN r.ci_name as ci_name
                """

                result = await session.run(
                    query,
                    tenant_id=str(tenant_id),
                    resource_id=resource_id,
                )

                record = await result.single()
                if record:
                    return record["ci_name"]

        except Exception as e:
            logger.error(
                "ci_lookup_failed",
                tenant_id=str(tenant_id),
                resource_id=resource_id,
                error=str(e),
            )

        return None
