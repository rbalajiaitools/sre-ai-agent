"""Base connector class for all integrations."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
import asyncio
from functools import wraps

from shared.logging import get_logger

logger = get_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for connector methods."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "connector_retry",
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            error=str(e)
                        )
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


class BaseConnector(ABC):
    """Base class for all connectors."""
    
    def __init__(self, config: dict):
        """Initialize connector with configuration.
        
        Args:
            config: Connector configuration dictionary
        """
        self.config = config
        self.connected = False
        self.last_health_check: Optional[datetime] = None
        self.health_status = "unknown"
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the service.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the service.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> dict:
        """Check health of the connection.
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    @abstractmethod
    async def execute(self, method: str, **kwargs) -> Any:
        """Execute a connector method.
        
        Args:
            method: Method name to execute
            **kwargs: Method parameters
            
        Returns:
            Method execution result
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def validate_config(self, required_keys: list[str]) -> bool:
        """Validate required configuration keys.
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            True if all required keys present, False otherwise
        """
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            logger.error("connector_config_invalid", missing_keys=missing_keys)
            return False
        return True
