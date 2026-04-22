"""Connectors package."""

from connectors.registry import ConnectorRegistry
from connectors.sdk import BaseConnector
from connectors.aws import AWSConnector
from connectors.slack import SlackConnector
from connectors.github import GitHubConnector

__all__ = [
    "ConnectorRegistry",
    "BaseConnector",
    "AWSConnector",
    "SlackConnector",
    "GitHubConnector",
]
