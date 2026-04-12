"""AWS adapter implementing BaseAdapter interface.

This module provides a complete implementation of the BaseAdapter interface
for Amazon Web Services. It delegates to service-specific modules and ensures
no AWS-specific types leak outside this module.
"""

import asyncio
from typing import Optional

from botocore.exceptions import ClientError, ConnectionError as BotoConnectionError

from app.adapters.base import BaseAdapter
from app.adapters.exceptions import (
    ProviderAuthError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.adapters.models import (
    AdapterCapability,
    AdapterHealthResponse,
    AuditRequest,
    AuditResponse,
    ChangesRequest,
    ChangesResponse,
    CostRequest,
    CostResponse,
    LogsRequest,
    LogsResponse,
    MetricsRequest,
    MetricsResponse,
    ProviderType,
    ResourcesRequest,
    ResourcesResponse,
    TopologyRequest,
    TopologyResponse,
)
from app.adapters.providers.aws.auth import AWSCredentialManager
from app.adapters.providers.aws.services.cloudtrail import CloudTrailService
from app.adapters.providers.aws.services.cloudwatch import CloudWatchService
from app.adapters.providers.aws.services.cost import CostExplorerService
from app.adapters.providers.aws.services.resources import AWSResourceService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AWSAdapter(BaseAdapter):
    """AWS adapter implementing all BaseAdapter methods.

    This adapter provides access to AWS services through a provider-agnostic
    interface. It uses STS AssumeRole for secure credential management.

    Attributes:
        SUPPORTED_CAPABILITIES: All capabilities are supported by AWS
    """

    SUPPORTED_CAPABILITIES = {
        AdapterCapability.METRICS,
        AdapterCapability.LOGS,
        AdapterCapability.RESOURCES,
        AdapterCapability.AUDIT,
        AdapterCapability.COST,
        AdapterCapability.CHANGES,
        AdapterCapability.TOPOLOGY,
    }

    def __init__(
        self,
        role_arn: str,
        external_id: str,
        region: str = "us-east-1",
        session_name: str = "SREAgentSession",
        endpoint_url: Optional[str] = None,
    ) -> None:
        """Initialize AWS adapter.

        Args:
            role_arn: ARN of the IAM role to assume
            external_id: External ID for security
            region: AWS region
            session_name: Session name for auditing
            endpoint_url: Optional custom endpoint (for LocalStack)
        """
        self.role_arn = role_arn
        self.external_id = external_id
        self.region = region

        # Initialize credential manager
        self.credential_manager = AWSCredentialManager(
            role_arn=role_arn,
            external_id=external_id,
            region=region,
            session_name=session_name,
            endpoint_url=endpoint_url,
        )

        logger.info(
            "aws_adapter_initialized",
            role_arn=role_arn,
            region=region,
        )

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name "aws"
        """
        return "aws"

    @property
    def provider_type(self) -> ProviderType:
        """Get provider type.

        Returns:
            ProviderType.CLOUD
        """
        return ProviderType.CLOUD

    async def validate_credentials(self) -> bool:
        """Validate AWS credentials.

        Returns:
            True if credentials are valid

        Raises:
            ProviderAuthError: If validation fails
        """
        def _sync_validate():
            result = self.credential_manager.validate_role()
            return result.valid

        try:
            return await asyncio.to_thread(_sync_validate)
        except Exception as e:
            logger.error("credential_validation_failed", error=str(e))
            raise ProviderAuthError(
                provider_name=self.provider_name,
                message=f"Credential validation failed: {str(e)}",
            )

    async def health_check(self) -> AdapterHealthResponse:
        """Perform health check on AWS adapter.

        Returns:
            AdapterHealthResponse with health status
        """
        import time

        start = time.time()

        try:
            # Try to get a session and make a simple API call
            def _sync_health_check():
                session = self.credential_manager.get_session()
                sts = session.client("sts")
                sts.get_caller_identity()
                return True

            await asyncio.to_thread(_sync_health_check)

            latency_ms = int((time.time() - start) * 1000)

            return AdapterHealthResponse(
                healthy=True,
                provider_name=self.provider_name,
                provider_type=self.provider_type,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error("aws_health_check_failed", error=str(e))

            return AdapterHealthResponse(
                healthy=False,
                provider_name=self.provider_name,
                provider_type=self.provider_type,
                error_message=str(e),
            )

    async def get_metrics(self, request: MetricsRequest) -> MetricsResponse:
        """Get metrics from CloudWatch.

        Args:
            request: Metrics request

        Returns:
            MetricsResponse with time series data

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            def _sync_get_metrics():
                session = self.credential_manager.get_session()
                service = CloudWatchService(session)
                return service.get_metrics(request)

            return await asyncio.to_thread(_sync_get_metrics)

        except ClientError as e:
            self._handle_client_error(e)

    async def query_logs(self, request: LogsRequest) -> LogsResponse:
        """Query logs from CloudWatch Logs.

        Args:
            request: Logs request

        Returns:
            LogsResponse with log entries

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            def _sync_query_logs():
                session = self.credential_manager.get_session()
                service = CloudWatchService(session)
                return service.query_logs(request)

            return await asyncio.to_thread(_sync_query_logs)

        except ClientError as e:
            self._handle_client_error(e)

    async def get_resources(self, request: ResourcesRequest) -> ResourcesResponse:
        """Get AWS resources.

        Args:
            request: Resources request

        Returns:
            ResourcesResponse with discovered resources

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            session = self.credential_manager.get_session()
            service = AWSResourceService(session)
            return await service.discover_all(request)

        except ClientError as e:
            self._handle_client_error(e)

    async def get_topology(self, request: TopologyRequest) -> TopologyResponse:
        """Get service topology.

        Note: AWS doesn't provide a native topology API. This would need to be
        built from resource relationships (VPC, security groups, etc.).

        Args:
            request: Topology request

        Returns:
            TopologyResponse with nodes and edges
        """
        # TODO: Implement topology discovery from AWS resources
        # This would involve analyzing VPC connections, security groups,
        # load balancer targets, etc.

        logger.warning("aws_topology_not_implemented")

        return TopologyResponse(
            nodes=[],
            edges=[],
            source_provider=self.provider_name,
        )

    async def get_audit_events(self, request: AuditRequest) -> AuditResponse:
        """Get audit events from CloudTrail.

        Args:
            request: Audit request

        Returns:
            AuditResponse with audit events

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            def _sync_get_audit():
                session = self.credential_manager.get_session()
                service = CloudTrailService(session)
                return service.get_audit_events(request)

            return await asyncio.to_thread(_sync_get_audit)

        except ClientError as e:
            self._handle_client_error(e)

    async def get_cost(self, request: CostRequest) -> CostResponse:
        """Get cost data from Cost Explorer.

        Args:
            request: Cost request

        Returns:
            CostResponse with cost breakdown

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            def _sync_get_cost():
                session = self.credential_manager.get_session()
                service = CostExplorerService(session)
                return service.get_cost(request)

            return await asyncio.to_thread(_sync_get_cost)

        except ClientError as e:
            self._handle_client_error(e)

    async def get_recent_changes(self, request: ChangesRequest) -> ChangesResponse:
        """Get recent changes from CloudTrail.

        Args:
            request: Changes request

        Returns:
            ChangesResponse with change events

        Raises:
            ProviderAuthError: If authentication fails
            ProviderRateLimitError: If rate limit exceeded
            ProviderTimeoutError: If request times out
        """
        try:
            def _sync_get_changes():
                session = self.credential_manager.get_session()
                service = CloudTrailService(session)
                return service.get_recent_changes(request)

            return await asyncio.to_thread(_sync_get_changes)

        except ClientError as e:
            self._handle_client_error(e)

    def _handle_client_error(self, error: ClientError) -> None:
        """Handle boto3 ClientError and translate to adapter exceptions.

        Args:
            error: boto3 ClientError

        Raises:
            ProviderAuthError: For authentication errors
            ProviderRateLimitError: For throttling errors
            ProviderConnectionError: For connection errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        logger.error(
            "aws_client_error",
            error_code=error_code,
            error_message=error_message,
        )

        # Throttling errors
        if error_code in ["ThrottlingException", "TooManyRequestsException", "RequestLimitExceeded"]:
            # Try to extract retry-after from response
            retry_after = 60  # Default to 60 seconds

            raise ProviderRateLimitError(
                provider_name=self.provider_name,
                retry_after=retry_after,
                message=error_message,
            )

        # Authentication errors
        elif error_code in ["AccessDenied", "UnauthorizedOperation", "InvalidClientTokenId", "SignatureDoesNotMatch"]:
            raise ProviderAuthError(
                provider_name=self.provider_name,
                message=error_message,
                details={"error_code": error_code},
            )

        # Connection errors
        elif error_code in ["ServiceUnavailable", "RequestTimeout"]:
            raise ProviderConnectionError(
                provider=self.provider_name,
                message=error_message,
                details={"error_code": error_code},
            )

        # Re-raise as generic connection error
        else:
            raise ProviderConnectionError(
                provider=self.provider_name,
                message=f"{error_code}: {error_message}",
                details={"error_code": error_code},
            )
