"""Base connector interface for incident management systems.

All incident management connectors (ServiceNow, PagerDuty, Jira, etc.)
must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID


class BaseConnector(ABC):
    """Abstract base class for incident management connectors.

    Connectors integrate with external incident management systems to:
    - Fetch open incidents
    - Update incidents with investigation findings
    - Close incidents after resolution
    - Map incident CIs to monitored resources
    """

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """Get connector name.

        Returns:
            Connector name (e.g., "servicenow", "pagerduty")
        """
        pass

    @abstractmethod
    async def get_open_incidents(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get open incidents for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of open incidents
        """
        pass

    @abstractmethod
    async def get_incident(
        self, tenant_id: UUID, incident_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific incident.

        Args:
            tenant_id: Tenant UUID
            incident_number: Incident number (e.g., "INC0012345")

        Returns:
            Incident if found, None otherwise
        """
        pass

    @abstractmethod
    async def write_investigation_notes(
        self,
        tenant_id: UUID,
        incident_number: str,
        rca_summary: str,
        evidence: List[str],
        recommended_fix: str,
    ) -> bool:
        """Write investigation findings to incident.

        Args:
            tenant_id: Tenant UUID
            incident_number: Incident number
            rca_summary: Root cause analysis summary
            evidence: List of evidence items
            recommended_fix: Recommended fix

        Returns:
            True if successful
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def validate_credentials(self, tenant_id: UUID) -> bool:
        """Validate connector credentials for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if credentials are valid
        """
        pass
