"""Scheduled incident poller for ServiceNow."""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis

from app.connectors.servicenow.connector import ServiceNowConnector
from app.core.logging import get_logger

logger = get_logger(__name__)


class IncidentPoller:
    """Scheduled poller for ServiceNow incidents.

    Polls ServiceNow at regular intervals and caches incidents in Redis.
    """

    def __init__(
        self,
        connector: ServiceNowConnector,
        redis_client: Optional[Redis] = None,
    ) -> None:
        """Initialize incident poller.

        Args:
            connector: ServiceNow connector
            redis_client: Redis client for caching
        """
        self.connector = connector
        self.redis_client = redis_client
        self.scheduler = AsyncIOScheduler()

        # Track polling status per tenant
        self._polling_status: Dict[UUID, Dict] = {}

        logger.info("incident_poller_initialized")

    def register_tenant(
        self,
        tenant_id: UUID,
        poll_interval_seconds: int = 300,
    ) -> None:
        """Register a tenant for polling.

        Args:
            tenant_id: Tenant UUID
            poll_interval_seconds: Polling interval in seconds
        """
        logger.info(
            "registering_tenant_for_polling",
            tenant_id=str(tenant_id),
            interval=poll_interval_seconds,
        )

        # Add job to scheduler
        job_id = f"poll_incidents_{tenant_id}"

        self.scheduler.add_job(
            func=self._poll_tenant,
            trigger="interval",
            seconds=poll_interval_seconds,
            args=[tenant_id],
            id=job_id,
            replace_existing=True,
            max_instances=1,  # Prevent concurrent polls for same tenant
        )

        self._polling_status[tenant_id] = {
            "last_poll": None,
            "last_success": None,
            "last_error": None,
            "incident_count": 0,
        }

        logger.info(
            "tenant_registered_for_polling",
            tenant_id=str(tenant_id),
            job_id=job_id,
        )

    def unregister_tenant(self, tenant_id: UUID) -> None:
        """Unregister a tenant from polling.

        Args:
            tenant_id: Tenant UUID
        """
        job_id = f"poll_incidents_{tenant_id}"

        try:
            self.scheduler.remove_job(job_id)
            self._polling_status.pop(tenant_id, None)

            logger.info("tenant_unregistered_from_polling", tenant_id=str(tenant_id))
        except Exception as e:
            logger.error(
                "tenant_unregister_failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )

    async def _poll_tenant(self, tenant_id: UUID) -> None:
        """Poll incidents for a tenant.

        Args:
            tenant_id: Tenant UUID
        """
        start_time = time.time()

        logger.info("polling_incidents", tenant_id=str(tenant_id))

        self._polling_status[tenant_id]["last_poll"] = datetime.utcnow()

        try:
            # Validate credentials first
            valid = await self.connector.validate_credentials(tenant_id)

            if not valid:
                logger.warning(
                    "skipping_poll_invalid_credentials",
                    tenant_id=str(tenant_id),
                )
                self._polling_status[tenant_id]["last_error"] = "Invalid credentials"
                return

            # Fetch incidents (this will cache them)
            incidents = await self.connector._fetch_incidents(tenant_id)

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "incidents_polled",
                tenant_id=str(tenant_id),
                count=len(incidents),
                duration_ms=duration_ms,
            )

            # Update status
            self._polling_status[tenant_id].update({
                "last_success": datetime.utcnow(),
                "last_error": None,
                "incident_count": len(incidents),
            })

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "incident_poll_failed",
                tenant_id=str(tenant_id),
                error=str(e),
                duration_ms=duration_ms,
            )

            self._polling_status[tenant_id]["last_error"] = str(e)

    async def trigger_manual_refresh(self, tenant_id: UUID) -> bool:
        """Trigger manual refresh for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if successful
        """
        logger.info("manual_refresh_triggered", tenant_id=str(tenant_id))

        try:
            await self._poll_tenant(tenant_id)
            return True
        except Exception as e:
            logger.error(
                "manual_refresh_failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return False

    def get_polling_status(self, tenant_id: UUID) -> Optional[Dict]:
        """Get polling status for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Polling status dict or None
        """
        return self._polling_status.get(tenant_id)

    def start(self) -> None:
        """Start the poller."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("incident_poller_started")

    def stop(self) -> None:
        """Stop the poller."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("incident_poller_stopped")

    def is_running(self) -> bool:
        """Check if poller is running.

        Returns:
            True if running
        """
        return self.scheduler.running
