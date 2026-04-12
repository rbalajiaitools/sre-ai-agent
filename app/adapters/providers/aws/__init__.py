"""AWS adapter implementation.

This module provides a complete implementation of the BaseAdapter interface
for Amazon Web Services using boto3.

Components:
    - AWSAdapter: Main adapter class implementing BaseAdapter
    - AWSCredentialManager: STS AssumeRole credential management
    - AWSOnboardingService: Customer onboarding and IAM setup
    - Service modules: CloudWatch, Resources, CloudTrail, Cost Explorer
    - Mappers: AWS types to generic adapter models

Security:
    - Uses STS AssumeRole with ExternalId for confused deputy protection
    - Credentials cached in memory with automatic refresh
    - No credentials logged or exposed
    - Least-privilege IAM policies

Usage:
    ```python
    from app.adapters.providers.aws import AWSAdapter

    adapter = AWSAdapter(
        role_arn="arn:aws:iam::123456789012:role/SREAgentRole",
        external_id="unique-external-id",
        region="us-east-1",
    )

    # Use like any BaseAdapter
    metrics = await adapter.get_metrics(request)
    ```
"""

from app.adapters.providers.aws.adapter import AWSAdapter
from app.adapters.providers.aws.auth import AWSCredentialManager
from app.adapters.providers.aws.onboarding import AWSOnboardingService

__all__ = [
    "AWSAdapter",
    "AWSCredentialManager",
    "AWSOnboardingService",
]
