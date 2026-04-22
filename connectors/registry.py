"""Connector registry for managing all connectors."""

from typing import Type, Dict
from connectors.sdk import BaseConnector
from connectors.aws import AWSConnector
from connectors.slack import SlackConnector
from connectors.github import GitHubConnector


class ConnectorRegistry:
    """Registry for all available connectors."""
    
    _connectors: Dict[str, Type[BaseConnector]] = {
        "aws": AWSConnector,
        "slack": SlackConnector,
        "github": GitHubConnector,
    }
    
    @classmethod
    def get_connector_class(cls, connector_type: str) -> Type[BaseConnector]:
        """Get connector class by type.
        
        Args:
            connector_type: Connector type (aws, slack, github, etc.)
            
        Returns:
            Connector class
            
        Raises:
            ValueError: If connector type not found
        """
        if connector_type not in cls._connectors:
            raise ValueError(f"Unknown connector type: {connector_type}")
        
        return cls._connectors[connector_type]
    
    @classmethod
    def create_connector(cls, connector_type: str, config: dict) -> BaseConnector:
        """Create connector instance.
        
        Args:
            connector_type: Connector type
            config: Connector configuration
            
        Returns:
            Connector instance
        """
        connector_class = cls.get_connector_class(connector_type)
        return connector_class(config)
    
    @classmethod
    def list_connector_types(cls) -> list[str]:
        """List all available connector types.
        
        Returns:
            List of connector type names
        """
        return list(cls._connectors.keys())
    
    @classmethod
    def register_connector(cls, connector_type: str, connector_class: Type[BaseConnector]):
        """Register a new connector type.
        
        Args:
            connector_type: Connector type name
            connector_class: Connector class
        """
        cls._connectors[connector_type] = connector_class
