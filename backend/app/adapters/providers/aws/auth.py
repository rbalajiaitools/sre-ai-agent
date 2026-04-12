"""AWS credential management using STS AssumeRole.

This module handles secure credential management for AWS using STS AssumeRole
with ExternalId for confused deputy protection.

Security Features:
    - ExternalId prevents confused deputy attacks
    - Credentials cached in memory only
    - Automatic refresh 5 minutes before expiry
    - No credentials logged or exposed
    - Support for custom endpoints (LocalStack testing)
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of role validation."""

    valid: bool
    error_message: Optional[str] = None
    account_id: Optional[str] = None
    role_name: Optional[str] = None


@dataclass
class CachedCredentials:
    """Cached AWS credentials with expiry."""

    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    region: str

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if credentials are expired or will expire soon.

        Args:
            buffer_seconds: Refresh buffer in seconds (default 5 minutes)

        Returns:
            True if credentials should be refreshed
        """
        return datetime.utcnow() >= (self.expiration - timedelta(seconds=buffer_seconds))


class AWSCredentialManager:
    """Manages AWS credentials using STS AssumeRole.

    This class handles secure credential management with automatic refresh
    and caching. It uses STS AssumeRole with ExternalId for security.

    Attributes:
        role_arn: ARN of the IAM role to assume
        external_id: External ID for confused deputy protection
        region: AWS region
        session_name: Session name for CloudTrail auditing
        endpoint_url: Optional custom endpoint (for LocalStack)
    """

    def __init__(
        self,
        role_arn: str,
        external_id: str,
        region: str = "us-east-1",
        session_name: str = "SREAgentSession",
        endpoint_url: Optional[str] = None,
    ) -> None:
        """Initialize AWS credential manager.

        Args:
            role_arn: ARN of the IAM role to assume
            external_id: External ID for security
            region: AWS region
            session_name: Session name for auditing
            endpoint_url: Optional custom endpoint URL
        """
        self.role_arn = role_arn
        self.external_id = external_id
        self.region = region
        self.session_name = session_name
        self.endpoint_url = endpoint_url

        self._cached_credentials: Optional[CachedCredentials] = None

        logger.info(
            "aws_credential_manager_initialized",
            role_arn=role_arn,
            region=region,
        )

    def get_session(self) -> boto3.Session:
        """Get boto3 session with valid credentials.

        Automatically refreshes credentials if expired or near expiry.

        Returns:
            boto3.Session with valid credentials

        Raises:
            ProviderAuthError: If unable to assume role
        """
        # Refresh credentials if needed
        if self._cached_credentials is None or self._cached_credentials.is_expired():
            self._refresh_credentials()

        # Create session from cached credentials
        session = boto3.Session(
            aws_access_key_id=self._cached_credentials.access_key_id,
            aws_secret_access_key=self._cached_credentials.secret_access_key,
            aws_session_token=self._cached_credentials.session_token,
            region_name=self._cached_credentials.region,
        )

        return session

    def _refresh_credentials(self) -> None:
        """Refresh credentials by assuming role.

        Raises:
            ProviderAuthError: If unable to assume role
        """
        from app.adapters.exceptions import ProviderAuthError

        logger.info("refreshing_aws_credentials", role_arn=self.role_arn)

        try:
            # Create STS client
            sts_client = boto3.client(
                "sts",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            )

            # Assume role with external ID
            response = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName=self.session_name,
                ExternalId=self.external_id,
                DurationSeconds=3600,  # 1 hour
            )

            credentials = response["Credentials"]

            # Cache credentials
            self._cached_credentials = CachedCredentials(
                access_key_id=credentials["AccessKeyId"],
                secret_access_key=credentials["SecretAccessKey"],
                session_token=credentials["SessionToken"],
                expiration=credentials["Expiration"],
                region=self.region,
            )

            logger.info(
                "aws_credentials_refreshed",
                expires_at=credentials["Expiration"].isoformat(),
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "aws_credential_refresh_failed",
                error_code=error_code,
                error_message=error_message,
                role_arn=self.role_arn,
            )

            raise ProviderAuthError(
                provider_name="aws",
                message=f"Failed to assume role: {error_message}",
                details={
                    "error_code": error_code,
                    "role_arn": self.role_arn,
                },
            )

    def validate_role(self, role_arn: Optional[str] = None) -> ValidationResult:
        """Validate that the role can be assumed and has basic permissions.

        Args:
            role_arn: Optional role ARN to validate (uses self.role_arn if None)

        Returns:
            ValidationResult with validation status and details
        """
        role_to_validate = role_arn or self.role_arn

        logger.info("validating_aws_role", role_arn=role_to_validate)

        try:
            # Create STS client
            sts_client = boto3.client(
                "sts",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            )

            # Try to assume role
            response = sts_client.assume_role(
                RoleArn=role_to_validate,
                RoleSessionName=f"{self.session_name}-validation",
                ExternalId=self.external_id,
                DurationSeconds=900,  # 15 minutes
            )

            # Get caller identity to verify
            temp_credentials = response["Credentials"]
            temp_sts = boto3.client(
                "sts",
                aws_access_key_id=temp_credentials["AccessKeyId"],
                aws_secret_access_key=temp_credentials["SecretAccessKey"],
                aws_session_token=temp_credentials["SessionToken"],
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            )

            identity = temp_sts.get_caller_identity()

            logger.info(
                "aws_role_validated",
                role_arn=role_to_validate,
                account_id=identity["Account"],
            )

            return ValidationResult(
                valid=True,
                account_id=identity["Account"],
                role_name=role_to_validate.split("/")[-1],
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "aws_role_validation_failed",
                error_code=error_code,
                error_message=error_message,
                role_arn=role_to_validate,
            )

            # Provide specific error messages
            if error_code == "AccessDenied":
                message = (
                    f"Access denied when assuming role. "
                    f"Verify the trust policy allows our account to assume this role "
                    f"and the ExternalId matches."
                )
            elif error_code == "InvalidClientTokenId":
                message = "Invalid AWS credentials. Check your AWS configuration."
            elif error_code == "NoSuchEntity":
                message = f"Role does not exist: {role_to_validate}"
            else:
                message = f"Failed to validate role: {error_message}"

            return ValidationResult(
                valid=False,
                error_message=message,
            )

        except Exception as e:
            logger.exception("unexpected_error_validating_role", role_arn=role_to_validate)
            return ValidationResult(
                valid=False,
                error_message=f"Unexpected error: {str(e)}",
            )

    def clear_cache(self) -> None:
        """Clear cached credentials.

        Useful for testing or forcing credential refresh.
        """
        self._cached_credentials = None
        logger.debug("aws_credentials_cache_cleared")
