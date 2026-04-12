"""Neo4j service map and relationship management."""

from typing import List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError

from app.core.logging import get_logger
from app.knowledge.models import (
    IncidentNode,
    ResourceNode,
    ServiceNode,
    TeamNode,
    TopologyResult,
)

logger = get_logger(__name__)


# Cypher query constants
CYPHER_CREATE_SERVICE = """
MERGE (s:Service {name: $name, tenant_id: $tenant_id})
SET s.type = $type,
    s.provider = $provider,
    s.region = $region,
    s.metadata = $metadata,
    s.updated_at = datetime()
RETURN s
"""

CYPHER_CREATE_RESOURCE = """
MERGE (r:Resource {resource_id: $resource_id, tenant_id: $tenant_id})
SET r.type = $type,
    r.name = $name,
    r.provider = $provider,
    r.status = $status,
    r.metadata = $metadata,
    r.updated_at = datetime()
RETURN r
"""

CYPHER_CREATE_INCIDENT = """
CREATE (i:Incident {
    incident_number: $incident_number,
    tenant_id: $tenant_id,
    title: $title,
    severity: $severity,
    service_name: $service_name,
    root_cause: $root_cause,
    created_at: datetime($created_at),
    resolved_at: datetime($resolved_at)
})
RETURN i
"""

CYPHER_CREATE_TEAM = """
MERGE (t:Team {name: $name, tenant_id: $tenant_id})
SET t.slack_channel = $slack_channel,
    t.oncall_rotation = $oncall_rotation,
    t.metadata = $metadata,
    t.updated_at = datetime()
RETURN t
"""

CYPHER_ADD_DEPENDENCY = """
MATCH (from:Service {name: $from_service, tenant_id: $tenant_id})
MATCH (to:Service {name: $to_service, tenant_id: $tenant_id})
MERGE (from)-[r:DEPENDS_ON]->(to)
SET r.updated_at = datetime()
RETURN r
"""

CYPHER_ADD_RUNS_ON = """
MATCH (s:Service {name: $service_name, tenant_id: $tenant_id})
MATCH (r:Resource {resource_id: $resource_id, tenant_id: $tenant_id})
MERGE (s)-[rel:RUNS_ON]->(r)
SET rel.updated_at = datetime()
RETURN rel
"""

CYPHER_ADD_CAUSED_BY = """
MATCH (i:Incident {incident_number: $incident_number, tenant_id: $tenant_id})
MATCH (target {name: $target_name, tenant_id: $tenant_id})
WHERE target:Service OR target:Resource
MERGE (i)-[r:CAUSED_BY]->(target)
SET r.updated_at = datetime()
RETURN r
"""

CYPHER_ADD_OWNS = """
MATCH (t:Team {name: $team_name, tenant_id: $tenant_id})
MATCH (s:Service {name: $service_name, tenant_id: $tenant_id})
MERGE (t)-[r:OWNS]->(s)
SET r.updated_at = datetime()
RETURN r
"""

CYPHER_GET_SERVICE_TOPOLOGY = """
MATCH (s:Service {name: $service_name, tenant_id: $tenant_id})
OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep:Service)
OPTIONAL MATCH (s)-[:RUNS_ON]->(res:Resource)
OPTIONAL MATCH (dep)-[:RUNS_ON]->(dep_res:Resource)
RETURN s,
       collect(DISTINCT dep) as dependencies,
       collect(DISTINCT res) as resources,
       collect(DISTINCT {service: dep.name, resource: dep_res}) as dependent_resources
"""

CYPHER_GET_RELATED_INCIDENTS = """
MATCH (i:Incident {tenant_id: $tenant_id})
WHERE i.service_name = $service_name
  AND i.resolved_at IS NOT NULL
RETURN i
ORDER BY i.created_at DESC
LIMIT $limit
"""

CYPHER_FIND_RESOURCE_BY_CI = """
MATCH (r:Resource {tenant_id: $tenant_id})
WHERE r.name =~ $pattern
   OR r.resource_id =~ $pattern
   OR r.metadata.ci_name =~ $pattern
RETURN r
LIMIT 10
"""

CYPHER_CREATE_INDEXES = """
CREATE INDEX service_name_tenant IF NOT EXISTS FOR (s:Service) ON (s.name, s.tenant_id);
CREATE INDEX resource_id_tenant IF NOT EXISTS FOR (r:Resource) ON (r.resource_id, r.tenant_id);
CREATE INDEX incident_number_tenant IF NOT EXISTS FOR (i:Incident) ON (i.incident_number, i.tenant_id);
CREATE INDEX team_name_tenant IF NOT EXISTS FOR (t:Team) ON (t.name, t.tenant_id);
CREATE TEXT INDEX resource_name IF NOT EXISTS FOR (r:Resource) ON (r.name);
"""


class KnowledgeGraph:
    """Neo4j-based knowledge graph for service topology and relationships.

    Manages services, resources, incidents, teams, and their relationships.
    Provides topology queries and incident correlation.
    """

    def __init__(self, uri: str, username: str, password: str) -> None:
        """Initialize knowledge graph.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self._driver: Optional[AsyncDriver] = None

    async def connect(self) -> None:
        """Connect to Neo4j database."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info("neo4j_connected", uri=self.uri)

            # Create indexes
            await self._create_indexes()

        except Neo4jError as e:
            logger.error("neo4j_connection_failed", uri=self.uri, error=str(e))
            raise

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            logger.info("neo4j_closed")

    async def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        try:
            async with self._driver.session() as session:
                # Split and execute each CREATE INDEX statement
                for statement in CYPHER_CREATE_INDEXES.strip().split(";"):
                    statement = statement.strip()
                    if statement:
                        await session.run(statement)

            logger.info("neo4j_indexes_created")

        except Neo4jError as e:
            logger.warning("neo4j_index_creation_failed", error=str(e))
            # Don't fail if indexes already exist

    async def upsert_service(self, tenant_id: str, service: ServiceNode) -> None:
        """Create or update a service node.

        Args:
            tenant_id: Tenant UUID
            service: Service node data
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_CREATE_SERVICE,
                    name=service.name,
                    tenant_id=tenant_id,
                    type=service.type,
                    provider=service.provider,
                    region=service.region,
                    metadata=service.metadata,
                )

            logger.info(
                "service_upserted",
                tenant_id=tenant_id,
                service_name=service.name,
            )

        except Neo4jError as e:
            logger.error(
                "service_upsert_failed",
                tenant_id=tenant_id,
                service_name=service.name,
                error=str(e),
            )
            raise

    async def upsert_resource(self, tenant_id: str, resource: ResourceNode) -> None:
        """Create or update a resource node.

        Args:
            tenant_id: Tenant UUID
            resource: Resource node data
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_CREATE_RESOURCE,
                    resource_id=resource.resource_id,
                    tenant_id=tenant_id,
                    type=resource.type,
                    name=resource.name,
                    provider=resource.provider,
                    status=resource.status,
                    metadata=resource.metadata,
                )

            logger.info(
                "resource_upserted",
                tenant_id=tenant_id,
                resource_id=resource.resource_id,
            )

        except Neo4jError as e:
            logger.error(
                "resource_upsert_failed",
                tenant_id=tenant_id,
                resource_id=resource.resource_id,
                error=str(e),
            )
            raise

    async def upsert_incident(self, tenant_id: str, incident: IncidentNode) -> None:
        """Create an incident node.

        Args:
            tenant_id: Tenant UUID
            incident: Incident node data
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_CREATE_INCIDENT,
                    incident_number=incident.incident_number,
                    tenant_id=tenant_id,
                    title=incident.title,
                    severity=incident.severity,
                    service_name=incident.service_name,
                    root_cause=incident.root_cause,
                    created_at=incident.created_at.isoformat() if incident.created_at else None,
                    resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
                )

            logger.info(
                "incident_created",
                tenant_id=tenant_id,
                incident_number=incident.incident_number,
            )

        except Neo4jError as e:
            logger.error(
                "incident_creation_failed",
                tenant_id=tenant_id,
                incident_number=incident.incident_number,
                error=str(e),
            )
            raise

    async def upsert_team(self, tenant_id: str, team: TeamNode) -> None:
        """Create or update a team node.

        Args:
            tenant_id: Tenant UUID
            team: Team node data
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_CREATE_TEAM,
                    name=team.name,
                    tenant_id=tenant_id,
                    slack_channel=team.slack_channel,
                    oncall_rotation=team.oncall_rotation,
                    metadata=team.metadata,
                )

            logger.info(
                "team_upserted",
                tenant_id=tenant_id,
                team_name=team.name,
            )

        except Neo4jError as e:
            logger.error(
                "team_upsert_failed",
                tenant_id=tenant_id,
                team_name=team.name,
                error=str(e),
            )
            raise

    async def add_dependency(
        self,
        tenant_id: str,
        from_service: str,
        to_service: str,
    ) -> None:
        """Add DEPENDS_ON relationship between services.

        Args:
            tenant_id: Tenant UUID
            from_service: Source service name
            to_service: Target service name
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    CYPHER_ADD_DEPENDENCY,
                    tenant_id=tenant_id,
                    from_service=from_service,
                    to_service=to_service,
                )

                # Check if relationship was created
                record = await result.single()
                if record:
                    logger.info(
                        "dependency_added",
                        tenant_id=tenant_id,
                        from_service=from_service,
                        to_service=to_service,
                    )
                else:
                    logger.warning(
                        "dependency_not_added",
                        tenant_id=tenant_id,
                        from_service=from_service,
                        to_service=to_service,
                        reason="Services not found",
                    )

        except Neo4jError as e:
            logger.error(
                "dependency_add_failed",
                tenant_id=tenant_id,
                from_service=from_service,
                to_service=to_service,
                error=str(e),
            )
            raise

    async def add_runs_on(
        self,
        tenant_id: str,
        service_name: str,
        resource_id: str,
    ) -> None:
        """Add RUNS_ON relationship between service and resource.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name
            resource_id: Resource ID
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_ADD_RUNS_ON,
                    tenant_id=tenant_id,
                    service_name=service_name,
                    resource_id=resource_id,
                )

            logger.info(
                "runs_on_added",
                tenant_id=tenant_id,
                service_name=service_name,
                resource_id=resource_id,
            )

        except Neo4jError as e:
            logger.error(
                "runs_on_add_failed",
                tenant_id=tenant_id,
                service_name=service_name,
                resource_id=resource_id,
                error=str(e),
            )
            raise

    async def add_owns(
        self,
        tenant_id: str,
        team_name: str,
        service_name: str,
    ) -> None:
        """Add OWNS relationship between team and service.

        Args:
            tenant_id: Tenant UUID
            team_name: Team name
            service_name: Service name
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    CYPHER_ADD_OWNS,
                    tenant_id=tenant_id,
                    team_name=team_name,
                    service_name=service_name,
                )

            logger.info(
                "owns_added",
                tenant_id=tenant_id,
                team_name=team_name,
                service_name=service_name,
            )

        except Neo4jError as e:
            logger.error(
                "owns_add_failed",
                tenant_id=tenant_id,
                team_name=team_name,
                service_name=service_name,
                error=str(e),
            )
            raise

    async def get_service_topology(
        self,
        tenant_id: str,
        service_name: str,
    ) -> Optional[TopologyResult]:
        """Get service topology including dependencies and resources.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name

        Returns:
            Topology result or None if service not found
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    CYPHER_GET_SERVICE_TOPOLOGY,
                    tenant_id=tenant_id,
                    service_name=service_name,
                )

                record = await result.single()
                if not record or not record["s"]:
                    logger.warning(
                        "service_not_found",
                        tenant_id=tenant_id,
                        service_name=service_name,
                    )
                    return None

                # Parse service
                service_data = dict(record["s"])
                service = ServiceNode(
                    name=service_data["name"],
                    type=service_data.get("type", "unknown"),
                    tenant_id=service_data["tenant_id"],
                    provider=service_data.get("provider", "unknown"),
                    region=service_data.get("region"),
                    metadata=service_data.get("metadata", {}),
                )

                # Parse dependencies
                dependencies = []
                for dep in record["dependencies"]:
                    if dep:
                        dep_data = dict(dep)
                        dependencies.append(
                            ServiceNode(
                                name=dep_data["name"],
                                type=dep_data.get("type", "unknown"),
                                tenant_id=dep_data["tenant_id"],
                                provider=dep_data.get("provider", "unknown"),
                                region=dep_data.get("region"),
                                metadata=dep_data.get("metadata", {}),
                            )
                        )

                # Parse resources
                resources = []
                for res in record["resources"]:
                    if res:
                        res_data = dict(res)
                        resources.append(
                            ResourceNode(
                                resource_id=res_data["resource_id"],
                                type=res_data.get("type", "unknown"),
                                name=res_data["name"],
                                tenant_id=res_data["tenant_id"],
                                provider=res_data.get("provider", "unknown"),
                                status=res_data.get("status"),
                                metadata=res_data.get("metadata", {}),
                            )
                        )

                # Parse dependent resources
                dependent_resources = {}
                for item in record["dependent_resources"]:
                    if item and item["service"] and item["resource"]:
                        service_name = item["service"]
                        res_data = dict(item["resource"])

                        if service_name not in dependent_resources:
                            dependent_resources[service_name] = []

                        dependent_resources[service_name].append(
                            ResourceNode(
                                resource_id=res_data["resource_id"],
                                type=res_data.get("type", "unknown"),
                                name=res_data["name"],
                                tenant_id=res_data["tenant_id"],
                                provider=res_data.get("provider", "unknown"),
                                status=res_data.get("status"),
                                metadata=res_data.get("metadata", {}),
                            )
                        )

                return TopologyResult(
                    service=service,
                    dependencies=dependencies,
                    resources=resources,
                    dependent_resources=dependent_resources,
                )

        except Neo4jError as e:
            logger.error(
                "topology_query_failed",
                tenant_id=tenant_id,
                service_name=service_name,
                error=str(e),
            )
            raise

    async def get_related_incidents(
        self,
        tenant_id: str,
        service_name: str,
        limit: int = 5,
    ) -> List[IncidentNode]:
        """Get past incidents for a service.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name
            limit: Maximum number of incidents to return

        Returns:
            List of incident nodes, ordered by recency
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    CYPHER_GET_RELATED_INCIDENTS,
                    tenant_id=tenant_id,
                    service_name=service_name,
                    limit=limit,
                )

                incidents = []
                async for record in result:
                    incident_data = dict(record["i"])
                    incidents.append(
                        IncidentNode(
                            incident_number=incident_data["incident_number"],
                            title=incident_data["title"],
                            severity=incident_data["severity"],
                            tenant_id=incident_data["tenant_id"],
                            service_name=incident_data.get("service_name"),
                            root_cause=incident_data.get("root_cause"),
                            created_at=incident_data.get("created_at"),
                            resolved_at=incident_data.get("resolved_at"),
                        )
                    )

                logger.info(
                    "related_incidents_found",
                    tenant_id=tenant_id,
                    service_name=service_name,
                    count=len(incidents),
                )

                return incidents

        except Neo4jError as e:
            logger.error(
                "related_incidents_query_failed",
                tenant_id=tenant_id,
                service_name=service_name,
                error=str(e),
            )
            raise

    async def find_resource_by_ci(
        self,
        tenant_id: str,
        ci_name: str,
    ) -> List[ResourceNode]:
        """Find resources by CI name using fuzzy matching.

        Args:
            tenant_id: Tenant UUID
            ci_name: Configuration Item name from ServiceNow

        Returns:
            List of matching resource nodes
        """
        try:
            # Create regex pattern for fuzzy matching
            # Convert spaces to .* for flexible matching
            pattern = f"(?i).*{ci_name.replace(' ', '.*')}.*"

            async with self._driver.session() as session:
                result = await session.run(
                    CYPHER_FIND_RESOURCE_BY_CI,
                    tenant_id=tenant_id,
                    pattern=pattern,
                )

                resources = []
                async for record in result:
                    res_data = dict(record["r"])
                    resources.append(
                        ResourceNode(
                            resource_id=res_data["resource_id"],
                            type=res_data.get("type", "unknown"),
                            name=res_data["name"],
                            tenant_id=res_data["tenant_id"],
                            provider=res_data.get("provider", "unknown"),
                            status=res_data.get("status"),
                            metadata=res_data.get("metadata", {}),
                        )
                    )

                logger.info(
                    "resources_found_by_ci",
                    tenant_id=tenant_id,
                    ci_name=ci_name,
                    count=len(resources),
                )

                return resources

        except Neo4jError as e:
            logger.error(
                "resource_ci_search_failed",
                tenant_id=tenant_id,
                ci_name=ci_name,
                error=str(e),
            )
            raise
