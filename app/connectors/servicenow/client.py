"""ServiceNow REST API client."""

import asyncio
from typing import Dict, List, Optional

import httpx
from httpx import AsyncClient, Response

from app.connectors.servicenow.config import AuthType, ServiceNowConfig
from app.connectors.servicenow.models import IncidentFilter, RawIncident
from app.core.logging import get_logger

logger = get_logger(__name__)


class ServiceNowClient:
    """ServiceNow REST API client.

    Handles authentication, rate limiting, retries, and API calls.
    """

    def __init__(self, config: ServiceNowConfig) -> None:
        """Initialize ServiceNow client.

        Args:
            config: ServiceNow configuration
        """
        self.config = config
        self.base_url = config.base_url

        # Create httpx client with connection pooling
        self._client: Optional[AsyncClient] = None

        logger.info(
            "servicenow_client_initialized",
            instance=config.instance,
            auth_type=config.auth_type.value,
        )

    async def _get_client(self) -> AsyncClient:
        """Get or create httpx client.

        Returns:
            AsyncClient instance
        """
        if self._client is None:
            # Build auth
            auth = None
            headers = {}

            if self.config.auth_type == AuthType.BASIC:
                auth = (self.config.username, self.config.password)
            elif self.config.auth_type == AuthType.OAUTH2:
                # For OAuth2, we'd need to get a token first
                # Simplified here - in production, implement token refresh
                token = await self._get_oauth_token()
                headers["Authorization"] = f"Bearer {token}"

            self._client = AsyncClient(
                base_url=self.base_url,
                auth=auth,
                headers=headers,
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )

        return self._client

    async def _get_oauth_token(self) -> str:
        """Get OAuth2 access token.

        Returns:
            Access token

        Raises:
            Exception: If token request fails
        """
        # Simplified OAuth2 implementation
        # In production, implement full OAuth2 flow with token caching
        token_url = f"https://{self.config.instance}.service-now.com/oauth_token.do"

        async with AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        retries: int = 3,
    ) -> Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            retries: Number of retries

        Returns:
            Response object

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        client = await self._get_client()

        for attempt in range(retries):
            try:
                logger.debug(
                    "servicenow_request",
                    method=method,
                    endpoint=endpoint,
                    attempt=attempt + 1,
                )

                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json,
                )

                # Check rate limiting
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = int(response.headers["X-RateLimit-Remaining"])
                    if remaining < 10:
                        logger.warning(
                            "servicenow_rate_limit_low",
                            remaining=remaining,
                        )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        "servicenow_rate_limited",
                        retry_after=retry_after,
                        attempt=attempt + 1,
                    )

                    if attempt < retries - 1:
                        await asyncio.sleep(retry_after)
                        continue

                # Handle server errors with exponential backoff
                if response.status_code >= 500:
                    if attempt < retries - 1:
                        backoff = 2**attempt
                        logger.warning(
                            "servicenow_server_error",
                            status_code=response.status_code,
                            backoff=backoff,
                        )
                        await asyncio.sleep(backoff)
                        continue

                response.raise_for_status()

                logger.debug(
                    "servicenow_request_success",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                )

                return response

            except httpx.HTTPError as e:
                logger.error(
                    "servicenow_request_error",
                    method=method,
                    endpoint=endpoint,
                    error=str(e),
                    attempt=attempt + 1,
                )

                if attempt == retries - 1:
                    raise

        raise Exception("Max retries exceeded")

    async def get_incidents(self, filters: IncidentFilter) -> List[RawIncident]:
        """Get incidents matching filters.

        Args:
            filters: Incident filter criteria

        Returns:
            List of raw incidents
        """
        logger.info("fetching_servicenow_incidents", filters=filters.model_dump())

        # Build query parameters
        params = {
            "sysparm_limit": filters.limit,
            "sysparm_display_value": "false",
        }

        # Build query string
        query_parts = []

        # Filter by states
        if filters.states:
            state_values = [state.value for state in filters.states]
            query_parts.append(f"stateIN{','.join(state_values)}")

        # Filter by priorities
        if filters.priorities:
            priority_values = [p.value for p in filters.priorities]
            query_parts.append(f"priorityIN{','.join(priority_values)}")

        # Filter by assignment groups
        if filters.assignment_groups:
            groups = ",".join(filters.assignment_groups)
            query_parts.append(f"assignment_group.nameIN{groups}")

        # Filter by update time
        if filters.updated_after:
            timestamp = filters.updated_after.strftime("%Y-%m-%d %H:%M:%S")
            query_parts.append(f"sys_updated_on>{timestamp}")

        if query_parts:
            params["sysparm_query"] = "^".join(query_parts)

        # Make request
        response = await self._request(
            method="GET",
            endpoint="/now/table/incident",
            params=params,
        )

        data = response.json()
        incidents = []

        for item in data.get("result", []):
            incident = RawIncident(
                sys_id=item.get("sys_id", ""),
                number=item.get("number", ""),
                short_description=item.get("short_description", ""),
                description=item.get("description", ""),
                priority=item.get("priority", "5"),
                state=item.get("state", "1"),
                category=item.get("category", ""),
                subcategory=item.get("subcategory", ""),
                cmdb_ci=item.get("cmdb_ci", {}),
                assignment_group=item.get("assignment_group", {}),
                assigned_to=item.get("assigned_to", {}),
                opened_at=item.get("opened_at", ""),
                sys_updated_on=item.get("sys_updated_on", ""),
                resolved_at=item.get("resolved_at"),
                work_notes=item.get("work_notes", ""),
            )
            incidents.append(incident)

        logger.info("servicenow_incidents_fetched", count=len(incidents))

        return incidents

    async def get_incident(self, incident_id: str) -> Optional[RawIncident]:
        """Get a specific incident.

        Args:
            incident_id: Incident sys_id or number

        Returns:
            Raw incident if found, None otherwise
        """
        logger.info("fetching_servicenow_incident", incident_id=incident_id)

        # Try by number first
        params = {
            "sysparm_query": f"number={incident_id}",
            "sysparm_limit": 1,
        }

        response = await self._request(
            method="GET",
            endpoint="/now/table/incident",
            params=params,
        )

        data = response.json()
        results = data.get("result", [])

        if not results:
            # Try by sys_id
            try:
                response = await self._request(
                    method="GET",
                    endpoint=f"/now/table/incident/{incident_id}",
                )
                results = [response.json().get("result", {})]
            except:
                return None

        if results:
            item = results[0]
            return RawIncident(
                sys_id=item.get("sys_id", ""),
                number=item.get("number", ""),
                short_description=item.get("short_description", ""),
                description=item.get("description", ""),
                priority=item.get("priority", "5"),
                state=item.get("state", "1"),
                category=item.get("category", ""),
                subcategory=item.get("subcategory", ""),
                cmdb_ci=item.get("cmdb_ci", {}),
                assignment_group=item.get("assignment_group", {}),
                assigned_to=item.get("assigned_to", {}),
                opened_at=item.get("opened_at", ""),
                sys_updated_on=item.get("sys_updated_on", ""),
                resolved_at=item.get("resolved_at"),
                work_notes=item.get("work_notes", ""),
            )

        return None

    async def update_incident(self, incident_id: str, data: Dict) -> bool:
        """Update an incident.

        Args:
            incident_id: Incident sys_id
            data: Update data

        Returns:
            True if successful
        """
        logger.info("updating_servicenow_incident", incident_id=incident_id)

        try:
            await self._request(
                method="PATCH",
                endpoint=f"/now/table/incident/{incident_id}",
                json=data,
            )
            return True
        except Exception as e:
            logger.error("incident_update_failed", incident_id=incident_id, error=str(e))
            return False

    async def add_work_note(self, incident_id: str, note: str) -> bool:
        """Add work note to incident.

        Args:
            incident_id: Incident sys_id
            note: Work note text

        Returns:
            True if successful
        """
        logger.info("adding_work_note", incident_id=incident_id)

        return await self.update_incident(
            incident_id=incident_id,
            data={"work_notes": note},
        )

    async def close_incident(
        self, incident_id: str, resolution_code: str, notes: str
    ) -> bool:
        """Close an incident.

        Args:
            incident_id: Incident sys_id
            resolution_code: Resolution code
            notes: Closing notes

        Returns:
            True if successful
        """
        logger.info("closing_servicenow_incident", incident_id=incident_id)

        return await self.update_incident(
            incident_id=incident_id,
            data={
                "state": IncidentState.RESOLVED.value,
                "close_code": resolution_code,
                "close_notes": notes,
            },
        )

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
