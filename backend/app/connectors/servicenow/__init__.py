"""ServiceNow connector for incident management.

This connector integrates with ServiceNow to:
- Poll for open incidents
- Update incidents with investigation findings
- Close incidents after resolution
- Map CMDB CIs to monitored resources

Components:
    - ServiceNowClient: REST API client
    - ServiceNowConnector: Main connector interface
    - IncidentPoller: Scheduled polling service
    - CIMapper: CI to resource mapping
"""

from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import ServiceNowConfig
from app.connectors.servicenow.connector import ServiceNowConnector
from app.connectors.servicenow.models import (
    IncidentFilter,
    IncidentPriority,
    IncidentState,
    ServiceNowIncident,
)

__all__ = [
    "ServiceNowClient",
    "ServiceNowConfig",
    "ServiceNowConnector",
    "IncidentFilter",
    "IncidentPriority",
    "IncidentState",
    "ServiceNowIncident",
]
