"""Concrete provider adapter implementations.

This package contains implementations of the BaseAdapter interface for
specific providers (AWS, Azure, GCP, Datadog, etc.).

Each provider is in its own subpackage to maintain clean separation.
"""

from app.adapters.providers.aws import AWSAdapter

__all__ = ["AWSAdapter"]
