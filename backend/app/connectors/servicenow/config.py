"""ServiceNow connection configuration."""

from enum import Enum
from typing import Optional

from pydantic import Field

from app.models.base import BaseSchema


class AuthType(str, Enum):
    """ServiceNow authentication type."""

    BASIC = "basic"
    OAUTH2 = "oauth2"


class ServiceNowConfig(BaseSchema):
    """ServiceNow connection configuration.

    Supports both basic auth and OAuth2 client credentials.
    """

    instance: str = Field(..., description="ServiceNow instance name (e.g., 'dev12345')")
    auth_type: AuthType = Field(default=AuthType.BASIC, description="Authentication type")

    # Basic auth
    username: Optional[str] = Field(default=None, description="Username for basic auth")
    password: Optional[str] = Field(default=None, description="Password for basic auth")

    # OAuth2
    client_id: Optional[str] = Field(default=None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth2 client secret")

    # Polling configuration
    poll_interval_seconds: int = Field(
        default=300, description="Polling interval in seconds"
    )
    assignment_groups: list[str] = Field(
        default_factory=list, description="Assignment groups to monitor"
    )

    @property
    def base_url(self) -> str:
        """Get ServiceNow base URL.

        Returns:
            Base URL for API calls
        """
        return f"https://{self.instance}.service-now.com/api"

    def validate_config(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if self.auth_type == AuthType.BASIC:
            if not self.username or not self.password:
                raise ValueError("Username and password required for basic auth")
        elif self.auth_type == AuthType.OAUTH2:
            if not self.client_id or not self.client_secret:
                raise ValueError("Client ID and secret required for OAuth2")

        return True
