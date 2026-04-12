"""Connectors for external incident management systems.

Connectors differ from adapters:
- Adapters: Monitor infrastructure/observability (AWS, Datadog, etc.)
- Connectors: Integrate with incident management systems (ServiceNow, PagerDuty, etc.)

Connectors are the source of incidents that trigger agent investigations.
"""

from app.connectors.base import BaseConnector
from app.connectors.servicenow import ServiceNowConnector

__all__ = [
    "BaseConnector",
    "ServiceNowConnector",
]
