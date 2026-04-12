"""Adapter-specific exceptions."""

from typing import Any, Dict, Optional
from uuid import UUID

from app.core.exceptions import SREAgentException


class AdapterNotRegisteredError(SREAgentException):
    """Exception raised when adapter is not registered for tenant."""

    def __init__(
        self,
        tenant_id: UUID,
        provider_name: Optional[str] = None,
        message: str = "No adapter registered",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize adapter not registered error.

        Args:
            tenant_id: Tenant UUID
            provider_name: Name of the provider
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="ADAPTER_NOT_REGISTERED",
            message=message,
            details={
                **(details or {}),
                "tenant_id": str(tenant_id),
                "provider_name": provider_name,
            },
            status_code=404,
        )


class AdapterCapabilityError(SREAgentException):
    """Exception raised when adapter doesn't support requested capability."""

    def __init__(
        self,
        provider_name: str,
        capability: str,
        supported_capabilities: list[str],
        message: str = "Adapter does not support requested capability",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize adapter capability error.

        Args:
            provider_name: Name of the provider
            capability: Requested capability
            supported_capabilities: List of supported capabilities
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="ADAPTER_CAPABILITY_ERROR",
            message=message,
            details={
                **(details or {}),
                "provider_name": provider_name,
                "requested_capability": capability,
                "supported_capabilities": supported_capabilities,
            },
            status_code=400,
        )


class ProviderAuthError(SREAgentException):
    """Exception raised when provider authentication fails."""

    def __init__(
        self,
        provider_name: str,
        message: str = "Provider authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider authentication error.

        Args:
            provider_name: Name of the provider
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="PROVIDER_AUTH_ERROR",
            message=message,
            details={**(details or {}), "provider_name": provider_name},
            status_code=401,
        )


class ProviderRateLimitError(SREAgentException):
    """Exception raised when provider rate limit is exceeded."""

    def __init__(
        self,
        provider_name: str,
        retry_after: int,
        message: str = "Provider rate limit exceeded",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider rate limit error.

        Args:
            provider_name: Name of the provider
            retry_after: Seconds to wait before retrying
            message: Error message
            details: Additional error details
        """
        self.retry_after = retry_after
        super().__init__(
            error_code="PROVIDER_RATE_LIMIT_ERROR",
            message=message,
            details={
                **(details or {}),
                "provider_name": provider_name,
                "retry_after": retry_after,
            },
            status_code=429,
        )


class ProviderTimeoutError(SREAgentException):
    """Exception raised when provider request times out."""

    def __init__(
        self,
        provider_name: str,
        timeout_seconds: float,
        message: str = "Provider request timed out",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider timeout error.

        Args:
            provider_name: Name of the provider
            timeout_seconds: Timeout duration in seconds
            message: Error message
            details: Additional error details
        """
        super().__init__(
            error_code="PROVIDER_TIMEOUT_ERROR",
            message=message,
            details={
                **(details or {}),
                "provider_name": provider_name,
                "timeout_seconds": timeout_seconds,
            },
            status_code=504,
        )
