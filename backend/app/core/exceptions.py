"""Custom exception hierarchy for SRE Agent."""

from typing import Any, Dict, Optional
from uuid import UUID


class SREAgentException(Exception):
    """Base exception for all SRE Agent errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        """Initialize base exception.

        Args:
            error_code: Unique error code for this exception type
            message: Human-readable error message
            details: Additional error details
            status_code: HTTP status code
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation.

        Returns:
            Dict containing error information
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ProviderConnectionError(SREAgentException):
    """Exception raised when connection to external provider fails."""

    def __init__(
        self,
        provider: str,
        message: str = "Failed to connect to provider",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider connection error.

        Args:
            provider: Name of the provider
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="PROVIDER_CONNECTION_ERROR",
            message=f"{message}: {provider}",
            details={**(details or {}), "provider": provider},
            status_code=503,
        )


class TenantNotFoundError(SREAgentException):
    """Exception raised when tenant is not found."""

    def __init__(
        self,
        tenant_id: UUID,
        message: str = "Tenant not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tenant not found error.

        Args:
            tenant_id: UUID of the tenant
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="TENANT_NOT_FOUND",
            message=message,
            details={**(details or {}), "tenant_id": str(tenant_id)},
            status_code=404,
        )


class InvestigationError(SREAgentException):
    """Exception raised during investigation process."""

    def __init__(
        self,
        investigation_id: str,
        message: str = "Investigation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize investigation error.

        Args:
            investigation_id: ID of the investigation
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="INVESTIGATION_ERROR",
            message=message,
            details={**(details or {}), "investigation_id": investigation_id},
            status_code=500,
        )


class ConfigurationError(SREAgentException):
    """Exception raised when configuration is invalid."""

    def __init__(
        self,
        config_key: str,
        message: str = "Invalid configuration",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            config_key: Configuration key that is invalid
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="CONFIGURATION_ERROR",
            message=message,
            details={**(details or {}), "config_key": config_key},
            status_code=500,
        )


class AuthenticationError(SREAgentException):
    """Exception raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            details=details,
            status_code=401,
        )
