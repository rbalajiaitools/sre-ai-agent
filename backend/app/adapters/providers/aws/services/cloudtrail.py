"""CloudTrail service for audit events and changes."""

from typing import List

import boto3
from botocore.exceptions import ClientError

from app.adapters.models import (
    AuditRequest,
    AuditResponse,
    ChangesRequest,
    ChangesResponse,
)
from app.adapters.providers.aws.mappers import map_cloudtrail_event
from app.core.logging import get_logger

logger = get_logger(__name__)


class CloudTrailService:
    """Service for querying CloudTrail events."""

    def __init__(self, session: boto3.Session) -> None:
        """Initialize CloudTrail service.

        Args:
            session: Authenticated boto3 session
        """
        self.session = session
        self.cloudtrail = session.client("cloudtrail")

    def get_audit_events(self, request: AuditRequest) -> AuditResponse:
        """Get audit events from CloudTrail.

        Args:
            request: Audit request

        Returns:
            AuditResponse with audit events
        """
        logger.info(
            "fetching_cloudtrail_events",
            start_time=request.start_time,
            end_time=request.end_time,
        )

        events = []

        try:
            # Build lookup attributes
            lookup_attributes = []

            if request.actor:
                lookup_attributes.append({
                    "AttributeKey": "Username",
                    "AttributeValue": request.actor,
                })

            if request.resource:
                lookup_attributes.append({
                    "AttributeKey": "ResourceName",
                    "AttributeValue": request.resource,
                })

            # Lookup events
            response = self.cloudtrail.lookup_events(
                LookupAttributes=lookup_attributes if lookup_attributes else [],
                StartTime=request.start_time,
                EndTime=request.end_time,
                MaxResults=min(request.limit, 50),  # CloudTrail max is 50
            )

            for event in response.get("Events", []):
                # Map to audit event
                audit_event = {
                    "event_id": event.get("EventId"),
                    "timestamp": event.get("EventTime"),
                    "actor": event.get("Username", "unknown"),
                    "action": event.get("EventName"),
                    "resource": event.get("Resources", [{}])[0].get("ResourceName", "unknown") if event.get("Resources") else "unknown",
                    "result": "success" if not event.get("ErrorCode") else "failure",
                    "metadata": {
                        "event_source": event.get("EventSource"),
                        "aws_region": event.get("AwsRegion"),
                        "source_ip": event.get("SourceIPAddress"),
                        "user_agent": event.get("UserAgent"),
                        "error_code": event.get("ErrorCode"),
                        "error_message": event.get("ErrorMessage"),
                    },
                }

                from app.adapters.models import AuditEvent
                events.append(AuditEvent(**audit_event))

            # Handle pagination
            while response.get("NextToken") and len(events) < request.limit:
                response = self.cloudtrail.lookup_events(
                    LookupAttributes=lookup_attributes if lookup_attributes else [],
                    StartTime=request.start_time,
                    EndTime=request.end_time,
                    NextToken=response["NextToken"],
                    MaxResults=min(request.limit - len(events), 50),
                )

                for event in response.get("Events", []):
                    audit_event = {
                        "event_id": event.get("EventId"),
                        "timestamp": event.get("EventTime"),
                        "actor": event.get("Username", "unknown"),
                        "action": event.get("EventName"),
                        "resource": event.get("Resources", [{}])[0].get("ResourceName", "unknown") if event.get("Resources") else "unknown",
                        "result": "success" if not event.get("ErrorCode") else "failure",
                        "metadata": {
                            "event_source": event.get("EventSource"),
                            "aws_region": event.get("AwsRegion"),
                        },
                    }

                    from app.adapters.models import AuditEvent
                    events.append(AuditEvent(**audit_event))

        except ClientError as e:
            logger.error(
                "cloudtrail_error",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            raise

        logger.info("cloudtrail_events_fetched", count=len(events))

        return AuditResponse(
            events=events,
            total_count=len(events),
            source_provider="aws",
        )

    def get_recent_changes(self, request: ChangesRequest) -> ChangesResponse:
        """Get recent changes from CloudTrail.

        Args:
            request: Changes request

        Returns:
            ChangesResponse with change events
        """
        logger.info(
            "fetching_cloudtrail_changes",
            service=request.service_name,
        )

        changes = []

        try:
            # Lookup events
            response = self.cloudtrail.lookup_events(
                StartTime=request.start_time,
                EndTime=request.end_time,
                MaxResults=50,
            )

            for event in response.get("Events", []):
                change_event = map_cloudtrail_event(event)

                # Filter by change types if specified
                if request.change_types and change_event.change_type not in request.change_types:
                    continue

                changes.append(change_event)

        except ClientError as e:
            logger.error(
                "cloudtrail_changes_error",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            raise

        logger.info("cloudtrail_changes_fetched", count=len(changes))

        return ChangesResponse(
            changes=changes,
            source_provider="aws",
        )
