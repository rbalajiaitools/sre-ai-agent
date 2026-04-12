"""ServiceNow connector main interface."""

import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from redis.asyncio import Redis

from app.connectors.base import BaseConnector
from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import ServiceNowConfig
from app.connectors.servicenow.models import (
    IncidentFilter,
    IncidentPriority,
    IncidentState,
    RawIncident,
    ServiceNowIncident,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ApprovalToken:
    """Token required for closing incidents.

    This ensures human approval before closing incidents.
    """

    def __init__(self, token: str, issued_by: str, issued_at: datetime) -> None:
        """Initialize approval token.

        Args:
            token: Unique token string
            issued_by: User who issued the token
            issued_at: When token was issued
        """
        self.token = token
        self.issued_by = issued_by
        self.issued_at = issued_at


class ServiceNowConnector(BaseConnector):
    """ServiceNow connector for incident management.

    This is the main interface used by the rest of the platform to interact
    with ServiceNow. It handles caching, normalization, and business logic.
    """

    CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
    ) -> None:
        """Initialize ServiceNow connector.

        Args:
            redis_client: Redis client for caching
        """
        self.redis_client = redis_client
        self._clients: dict[UUID, ServiceNowClient] = {}
        self._configs: dict[UUID, ServiceNowConfig] = {}

        logger.info("servicenow_connector_initialized")

    @property
    def connector_name(self) -> str:
        """Get connector name.

        Returns:
            Connector name "servicenow"
        """
        return "servicenow"

    def register_tenant(self, tenant_id: UUID, config: ServiceNowConfig) -> None:
        """Register a tenant with ServiceNow configuration.

        Args:
            tenant_id: Tenant UUID
            config: ServiceNow configuration
        """
        config.validate_config()

        self._configs[tenant_id] = config
        self._clients[tenant_id] = ServiceNowClient(config)

        logger.info(
            "tenant_registered",
            tenant_id=str(tenant_id),
            instance=config.instance,
        )

    def _get_client(self, tenant_id: UUID) -> ServiceNowClient:
        """Get ServiceNow client for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            ServiceNow client

        Raises:
            ValueError: If tenant not registered
        """
        if tenant_id not in self._clients:
            raise ValueError(f"Tenant {tenant_id} not registered with ServiceNow")

        return self._clients[tenant_id]

    def _get_config(self, tenant_id: UUID) -> ServiceNowConfig:
        """Get ServiceNow config for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            ServiceNow configuration

        Raises:
            ValueError: If tenant not registered
        """
        if tenant_id not in self._configs:
            raise ValueError(f"Tenant {tenant_id} not registered with ServiceNow")

        return self._configs[tenant_id]

    def _normalize_incident(
        self, raw: RawIncident, tenant_id: UUID
    ) -> ServiceNowIncident:
        """Normalize raw ServiceNow incident to canonical model.

        Args:
            raw: Raw incident from ServiceNow API
            tenant_id: Tenant UUID

        Returns:
            Normalized incident
        """
        # Parse timestamps
        opened_at = datetime.fromisoformat(raw.opened_at.replace(" ", "T"))
        updated_at = datetime.fromisoformat(raw.sys_updated_on.replace(" ", "T"))
        resolved_at = None
        if raw.resolved_at:
            resolved_at = datetime.fromisoformat(raw.resolved_at.replace(" ", "T"))

        # Extract CI information
        cmdb_ci = ""
        cmdb_ci_sys_id = ""
        if isinstance(raw.cmdb_ci, dict):
            cmdb_ci = raw.cmdb_ci.get("display_value", "")
            cmdb_ci_sys_id = raw.cmdb_ci.get("value", "")
        elif isinstance(raw.cmdb_ci, str):
            cmdb_ci = raw.cmdb_ci

        # Extract assignment group
        assignment_group = ""
        if isinstance(raw.assignment_group, dict):
            assignment_group = raw.assignment_group.get("display_value", "")
        elif isinstance(raw.assignment_group, str):
            assignment_group = raw.assignment_group

        # Extract assigned to
        assigned_to = None
        if isinstance(raw.assigned_to, dict):
            assigned_to = raw.assigned_to.get("display_value")
        elif isinstance(raw.assigned_to, str) and raw.assigned_to:
            assigned_to = raw.assigned_to

        # Parse work notes
        work_notes = []
        if raw.work_notes:
            # Work notes are typically newline-separated
            work_notes = [note.strip() for note in raw.work_notes.split("\n") if note.strip()]

        # Parse related incidents
        related_incidents = []
        if raw.child_incidents:
            related_incidents = [
                inc.strip() for inc in raw.child_incidents.split(",") if inc.strip()
            ]

        return ServiceNowIncident(
            sys_id=raw.sys_id,
            number=raw.number,
            short_description=raw.short_description,
            description=raw.description,
            priority=IncidentPriority(raw.priority),
            state=IncidentState(raw.state),
            category=raw.category,
            subcategory=raw.subcategory,
            cmdb_ci=cmdb_ci,
            cmdb_ci_sys_id=cmdb_ci_sys_id,
            assignment_group=assignment_group,
            assigned_to=assigned_to,
            opened_at=opened_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            work_notes=work_notes,
            related_incidents=related_incidents,
            tenant_id=str(tenant_id),
        )

    async def get_open_incidents(self, tenant_id: UUID) -> List[ServiceNowIncident]:
        """Get open incidents from cache.

        Incidents are refreshed by the poller. This method returns cached data.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of open incidents
        """
        logger.info("fetching_open_incidents", tenant_id=str(tenant_id))

        # Try to get from cache
        if self.redis_client:
            cache_key = f"incidents:{tenant_id}"
            cached = await self.redis_client.get(cache_key)

            if cached:
                logger.debug("incidents_from_cache", tenant_id=str(tenant_id))
                incidents_data = json.loads(cached)
                return [ServiceNowIncident(**inc) for inc in incidents_data]

        # If not in cache, fetch directly
        logger.debug("incidents_cache_miss", tenant_id=str(tenant_id))
        return await self._fetch_incidents(tenant_id)

    async def _fetch_incidents(self, tenant_id: UUID) -> List[ServiceNowIncident]:
        """Fetch incidents directly from ServiceNow.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of incidents
        """
        client = self._get_client(tenant_id)
        config = self._get_config(tenant_id)

        # Build filter
        incident_filter = IncidentFilter(
            states=[IncidentState.NEW, IncidentState.IN_PROGRESS],
            assignment_groups=config.assignment_groups,
        )

        # Fetch from ServiceNow
        raw_incidents = await client.get_incidents(incident_filter)

        # Normalize
        incidents = [
            self._normalize_incident(raw, tenant_id) for raw in raw_incidents
        ]

        # Cache if Redis available
        if self.redis_client:
            cache_key = f"incidents:{tenant_id}"
            incidents_data = [inc.model_dump() for inc in incidents]
            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(incidents_data, default=str),
            )

        return incidents

    async def get_incident(
        self, tenant_id: UUID, incident_number: str
    ) -> Optional[ServiceNowIncident]:
        """Get a specific incident.

        Args:
            tenant_id: Tenant UUID
            incident_number: Incident number (e.g., "INC0012345")

        Returns:
            Incident if found, None otherwise
        """
        logger.info(
            "fetching_incident",
            tenant_id=str(tenant_id),
            incident_number=incident_number,
        )

        client = self._get_client(tenant_id)

        raw_incident = await client.get_incident(incident_number)

        if raw_incident:
            return self._normalize_incident(raw_incident, tenant_id)

        return None

    async def write_investigation_notes(
        self,
        tenant_id: UUID,
        incident_number: str,
        rca_summary: str,
        evidence: List[str],
        recommended_fix: str,
    ) -> bool:
        """Write investigation findings to incident.

        Formats a clean, structured work note and posts to ServiceNow.

        Args:
            tenant_id: Tenant UUID
            incident_number: Incident number
            rca_summary: Root cause analysis summary
            evidence: List of evidence items
            recommended_fix: Recommended fix

        Returns:
            True if successful
        """
        logger.info(
            "writing_investigation_notes",
            tenant_id=str(tenant_id),
            incident_number=incident_number,
        )

        # Get incident to find sys_id
        incident = await self.get_incident(tenant_id, incident_number)
        if not incident:
            logger.error("incident_not_found", incident_number=incident_number)
            return False

        # Format work note
        work_note = self._format_investigation_note(
            rca_summary=rca_summary,
            evidence=evidence,
            recommended_fix=recommended_fix,
        )

        # Post to ServiceNow
        client = self._get_client(tenant_id)
        success = await client.add_work_note(incident.sys_id, work_note)

        if success:
            logger.info(
                "investigation_notes_written",
                incident_number=incident_number,
            )
        else:
            logger.error(
                "investigation_notes_failed",
                incident_number=incident_number,
            )

        return success

    def _format_investigation_note(
        self,
        rca_summary: str,
        evidence: List[str],
        recommended_fix: str,
    ) -> str:
        """Format investigation findings as structured work note.

        Args:
            rca_summary: Root cause analysis summary
            evidence: List of evidence items
            recommended_fix: Recommended fix

        Returns:
            Formatted work note
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        note_parts = [
            "=" * 80,
            "SRE AI Agent - Automated Investigation",
            f"Timestamp: {timestamp}",
            "=" * 80,
            "",
            "ROOT CAUSE ANALYSIS:",
            rca_summary,
            "",
            "EVIDENCE:",
        ]

        for i, item in enumerate(evidence, 1):
            note_parts.append(f"{i}. {item}")

        note_parts.extend([
            "",
            "RECOMMENDED FIX:",
            recommended_fix,
            "",
            "=" * 80,
            "This investigation was performed automatically by SRE AI Agent.",
            "Please review findings before taking action.",
            "=" * 80,
        ])

        return "\n".join(note_parts)

    async def close_incident(
        self,
        tenant_id: UUID,
        incident_number: str,
        resolution: str,
        approval_token: str,
    ) -> bool:
        """Close an incident.

        Requires human approval token for safety.

        Args:
            tenant_id: Tenant UUID
            incident_number: Incident number
            resolution: Resolution notes
            approval_token: Human approval token

        Returns:
            True if successful
        """
        logger.info(
            "closing_incident",
            tenant_id=str(tenant_id),
            incident_number=incident_number,
        )

        # Validate approval token
        # In production, verify token against database
        if not approval_token:
            logger.error("missing_approval_token", incident_number=incident_number)
            return False

        # Get incident
        incident = await self.get_incident(tenant_id, incident_number)
        if not incident:
            logger.error("incident_not_found", incident_number=incident_number)
            return False

        # Close incident
        client = self._get_client(tenant_id)
        success = await client.close_incident(
            incident_id=incident.sys_id,
            resolution_code="Solved (Permanently)",
            notes=resolution,
        )

        if success:
            logger.info("incident_closed", incident_number=incident_number)
        else:
            logger.error("incident_close_failed", incident_number=incident_number)

        return success

    async def validate_credentials(self, tenant_id: UUID) -> bool:
        """Validate ServiceNow credentials for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if credentials are valid
        """
        try:
            client = self._get_client(tenant_id)

            # Try to fetch one incident as validation
            incident_filter = IncidentFilter(limit=1)
            await client.get_incidents(incident_filter)

            logger.info("credentials_validated", tenant_id=str(tenant_id))
            return True

        except Exception as e:
            logger.error(
                "credentials_validation_failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return False

    async def invalidate_cache(self, tenant_id: UUID) -> None:
        """Invalidate incident cache for tenant.

        Args:
            tenant_id: Tenant UUID
        """
        if self.redis_client:
            cache_key = f"incidents:{tenant_id}"
            await self.redis_client.delete(cache_key)

            logger.info("cache_invalidated", tenant_id=str(tenant_id))
