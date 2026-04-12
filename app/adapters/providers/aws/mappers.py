"""Mappers to convert AWS-specific types to generic adapter models.

All functions in this module are pure - no side effects, no API calls.
They preserve all useful AWS metadata in the generic model's metadata field.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.adapters.models import (
    AuditEvent,
    ChangeEvent,
    ChangeType,
    CostBreakdown,
    DataPoint,
    LogEntry,
    LogLevel,
    MetricSeries,
    Resource,
    ResourceHealth,
    ResourceStatus,
    ResourceType,
)


def map_cloudwatch_metric(
    metric_data: Dict[str, Any],
    metric_name: str,
    unit: str = "None",
) -> MetricSeries:
    """Map CloudWatch metric data to MetricSeries.

    Args:
        metric_data: CloudWatch metric data result
        metric_name: Name of the metric
        unit: Unit of measurement

    Returns:
        MetricSeries with data points
    """
    data_points = []

    timestamps = metric_data.get("Timestamps", [])
    values = metric_data.get("Values", [])

    for timestamp, value in zip(timestamps, values):
        data_points.append(
            DataPoint(
                timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp)),
                value=float(value),
                tags={},
            )
        )

    return MetricSeries(
        metric_name=metric_name,
        unit=unit if unit != "None" else "count",
        data_points=data_points,
    )


def map_cloudwatch_log_event(event: Dict[str, Any]) -> LogEntry:
    """Map CloudWatch Logs event to LogEntry.

    Args:
        event: CloudWatch Logs event

    Returns:
        LogEntry with parsed log data
    """
    message = event.get("message", "")
    timestamp_ms = event.get("timestamp", 0)

    # Parse log level from message if possible
    level = LogLevel.INFO
    message_upper = message.upper()
    if "ERROR" in message_upper or "FATAL" in message_upper:
        level = LogLevel.ERROR
    elif "WARN" in message_upper:
        level = LogLevel.WARNING
    elif "DEBUG" in message_upper:
        level = LogLevel.DEBUG

    return LogEntry(
        timestamp=datetime.fromtimestamp(timestamp_ms / 1000.0),
        level=level,
        message=message,
        service=event.get("logStreamName", "unknown"),
        attributes={
            "log_group": event.get("logGroupName"),
            "log_stream": event.get("logStreamName"),
            "event_id": event.get("eventId"),
        },
        trace_id=None,  # AWS X-Ray trace ID would go here if available
    )


def map_ec2_instance(instance: Dict[str, Any]) -> Resource:
    """Map EC2 instance to Resource.

    Args:
        instance: EC2 instance description

    Returns:
        Resource with EC2 instance data
    """
    instance_id = instance.get("InstanceId", "unknown")
    state = instance.get("State", {}).get("Name", "unknown")

    # Map EC2 state to ResourceStatus
    status_map = {
        "running": ResourceStatus.RUNNING,
        "stopped": ResourceStatus.STOPPED,
        "pending": ResourceStatus.PENDING,
        "stopping": ResourceStatus.PENDING,
        "terminated": ResourceStatus.STOPPED,
        "shutting-down": ResourceStatus.PENDING,
    }
    status = status_map.get(state, ResourceStatus.UNKNOWN)

    # Extract tags
    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}

    # Get name from tags
    name = tags.get("Name", instance_id)

    # Health status
    health = None
    if state == "running":
        health = ResourceHealth(
            status="healthy" if status == ResourceStatus.RUNNING else "unhealthy",
            last_check=datetime.utcnow(),
            details={"state": state},
        )

    return Resource(
        resource_id=instance_id,
        resource_type=ResourceType.COMPUTE,
        name=name,
        status=status,
        region=instance.get("Placement", {}).get("AvailabilityZone", "unknown"),
        tags=tags,
        metadata={
            "instance_type": instance.get("InstanceType"),
            "launch_time": instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None,
            "private_ip": instance.get("PrivateIpAddress"),
            "public_ip": instance.get("PublicIpAddress"),
            "vpc_id": instance.get("VpcId"),
            "subnet_id": instance.get("SubnetId"),
            "platform": instance.get("Platform", "linux"),
            "architecture": instance.get("Architecture"),
        },
        health=health,
    )


def map_ecs_service(service: Dict[str, Any], cluster_name: str) -> Resource:
    """Map ECS service to Resource.

    Args:
        service: ECS service description
        cluster_name: Name of the ECS cluster

    Returns:
        Resource with ECS service data
    """
    service_name = service.get("serviceName", "unknown")
    service_arn = service.get("serviceArn", "")

    # Determine status
    status = ResourceStatus.RUNNING
    if service.get("status") != "ACTIVE":
        status = ResourceStatus.STOPPED

    desired_count = service.get("desiredCount", 0)
    running_count = service.get("runningCount", 0)

    # Health based on desired vs running
    health_status = "healthy"
    if running_count < desired_count:
        health_status = "degraded"
    elif running_count == 0:
        health_status = "unhealthy"

    health = ResourceHealth(
        status=health_status,
        last_check=datetime.utcnow(),
        details={
            "desired_count": desired_count,
            "running_count": running_count,
            "pending_count": service.get("pendingCount", 0),
        },
    )

    # Extract tags
    tags = {tag["key"]: tag["value"] for tag in service.get("tags", [])}

    return Resource(
        resource_id=service_arn,
        resource_type=ResourceType.CONTAINER,
        name=service_name,
        status=status,
        region=service_arn.split(":")[3] if ":" in service_arn else "unknown",
        tags=tags,
        metadata={
            "cluster": cluster_name,
            "task_definition": service.get("taskDefinition"),
            "desired_count": desired_count,
            "running_count": running_count,
            "launch_type": service.get("launchType"),
            "platform_version": service.get("platformVersion"),
            "created_at": service.get("createdAt").isoformat() if service.get("createdAt") else None,
        },
        health=health,
    )


def map_eks_nodegroup(nodegroup: Dict[str, Any], cluster_name: str) -> Resource:
    """Map EKS node group to Resource.

    Args:
        nodegroup: EKS node group description
        cluster_name: Name of the EKS cluster

    Returns:
        Resource with EKS node group data
    """
    nodegroup_name = nodegroup.get("nodegroupName", "unknown")
    nodegroup_arn = nodegroup.get("nodegroupArn", "")

    # Map EKS status
    eks_status = nodegroup.get("status", "UNKNOWN")
    status_map = {
        "ACTIVE": ResourceStatus.RUNNING,
        "CREATING": ResourceStatus.PENDING,
        "UPDATING": ResourceStatus.PENDING,
        "DELETING": ResourceStatus.PENDING,
        "CREATE_FAILED": ResourceStatus.FAILED,
        "DELETE_FAILED": ResourceStatus.FAILED,
        "DEGRADED": ResourceStatus.FAILED,
    }
    status = status_map.get(eks_status, ResourceStatus.UNKNOWN)

    # Health status
    health_status = "healthy" if eks_status == "ACTIVE" else "unhealthy"
    health_issues = nodegroup.get("health", {}).get("issues", [])

    health = ResourceHealth(
        status=health_status,
        last_check=datetime.utcnow(),
        details={
            "eks_status": eks_status,
            "health_issues": [issue.get("code") for issue in health_issues],
            "desired_size": nodegroup.get("scalingConfig", {}).get("desiredSize"),
            "min_size": nodegroup.get("scalingConfig", {}).get("minSize"),
            "max_size": nodegroup.get("scalingConfig", {}).get("maxSize"),
        },
    )

    # Extract tags
    tags = nodegroup.get("tags", {})

    return Resource(
        resource_id=nodegroup_arn,
        resource_type=ResourceType.KUBERNETES_WORKLOAD,
        name=nodegroup_name,
        status=status,
        region=nodegroup_arn.split(":")[3] if ":" in nodegroup_arn else "unknown",
        tags=tags,
        metadata={
            "cluster": cluster_name,
            "version": nodegroup.get("version"),
            "release_version": nodegroup.get("releaseVersion"),
            "instance_types": nodegroup.get("instanceTypes", []),
            "ami_type": nodegroup.get("amiType"),
            "disk_size": nodegroup.get("diskSize"),
            "created_at": nodegroup.get("createdAt").isoformat() if nodegroup.get("createdAt") else None,
        },
        health=health,
    )


def map_rds_instance(db_instance: Dict[str, Any]) -> Resource:
    """Map RDS instance to Resource.

    Args:
        db_instance: RDS DB instance description

    Returns:
        Resource with RDS instance data
    """
    db_identifier = db_instance.get("DBInstanceIdentifier", "unknown")
    db_status = db_instance.get("DBInstanceStatus", "unknown")

    # Map RDS status
    status_map = {
        "available": ResourceStatus.RUNNING,
        "stopped": ResourceStatus.STOPPED,
        "starting": ResourceStatus.PENDING,
        "stopping": ResourceStatus.PENDING,
        "creating": ResourceStatus.PENDING,
        "deleting": ResourceStatus.PENDING,
        "failed": ResourceStatus.FAILED,
        "storage-full": ResourceStatus.FAILED,
    }
    status = status_map.get(db_status, ResourceStatus.UNKNOWN)

    # Health status
    health_status = "healthy" if db_status == "available" else "unhealthy"

    health = ResourceHealth(
        status=health_status,
        last_check=datetime.utcnow(),
        details={
            "db_status": db_status,
            "multi_az": db_instance.get("MultiAZ", False),
            "storage_encrypted": db_instance.get("StorageEncrypted", False),
        },
    )

    # Extract tags
    tags = {tag["Key"]: tag["Value"] for tag in db_instance.get("TagList", [])}

    return Resource(
        resource_id=db_instance.get("DBInstanceArn", db_identifier),
        resource_type=ResourceType.DATABASE,
        name=db_identifier,
        status=status,
        region=db_instance.get("AvailabilityZone", "unknown"),
        tags=tags,
        metadata={
            "engine": db_instance.get("Engine"),
            "engine_version": db_instance.get("EngineVersion"),
            "instance_class": db_instance.get("DBInstanceClass"),
            "allocated_storage": db_instance.get("AllocatedStorage"),
            "endpoint": db_instance.get("Endpoint", {}).get("Address"),
            "port": db_instance.get("Endpoint", {}).get("Port"),
            "master_username": db_instance.get("MasterUsername"),
            "created_time": db_instance.get("InstanceCreateTime").isoformat() if db_instance.get("InstanceCreateTime") else None,
        },
        health=health,
    )


def map_lambda_function(function: Dict[str, Any]) -> Resource:
    """Map Lambda function to Resource.

    Args:
        function: Lambda function configuration

    Returns:
        Resource with Lambda function data
    """
    function_name = function.get("FunctionName", "unknown")
    function_arn = function.get("FunctionArn", "")

    # Lambda functions are always "running" if they exist
    status = ResourceStatus.RUNNING

    # Extract region from ARN
    region = function_arn.split(":")[3] if ":" in function_arn else "unknown"

    # Health - check last update status
    last_update_status = function.get("LastUpdateStatus", "Successful")
    health_status = "healthy" if last_update_status == "Successful" else "unhealthy"

    health = ResourceHealth(
        status=health_status,
        last_check=datetime.utcnow(),
        details={
            "last_update_status": last_update_status,
            "state": function.get("State"),
        },
    )

    # Tags
    tags = function.get("Tags", {})

    return Resource(
        resource_id=function_arn,
        resource_type=ResourceType.SERVERLESS,
        name=function_name,
        status=status,
        region=region,
        tags=tags,
        metadata={
            "runtime": function.get("Runtime"),
            "handler": function.get("Handler"),
            "memory_size": function.get("MemorySize"),
            "timeout": function.get("Timeout"),
            "code_size": function.get("CodeSize"),
            "last_modified": function.get("LastModified"),
            "version": function.get("Version"),
            "role": function.get("Role"),
        },
        health=health,
    )


def map_cloudtrail_event(event: Dict[str, Any]) -> ChangeEvent:
    """Map CloudTrail event to ChangeEvent.

    Args:
        event: CloudTrail event

    Returns:
        ChangeEvent with audit data
    """
    event_name = event.get("EventName", "Unknown")
    event_time = event.get("EventTime")

    # Determine change type from event name
    change_type = ChangeType.INFRASTRUCTURE_CHANGE
    if "Deploy" in event_name or "Update" in event_name:
        change_type = ChangeType.DEPLOYMENT
    elif "PutParameter" in event_name or "UpdateConfiguration" in event_name:
        change_type = ChangeType.CONFIG_CHANGE
    elif "SetDesiredCapacity" in event_name or "UpdateAutoScaling" in event_name:
        change_type = ChangeType.SCALING_EVENT
    elif "Reboot" in event_name or "Restart" in event_name:
        change_type = ChangeType.RESTART

    # Extract actor
    actor = "unknown"
    if "Username" in event:
        actor = event["Username"]
    elif "UserIdentity" in event:
        user_identity = event["UserIdentity"]
        if "userName" in user_identity:
            actor = user_identity["userName"]
        elif "principalId" in user_identity:
            actor = user_identity["principalId"]

    # Extract affected resources
    affected_resources = []
    for resource in event.get("Resources", []):
        if "ResourceName" in resource:
            affected_resources.append(resource["ResourceName"])
        elif "ResourceARN" in resource:
            affected_resources.append(resource["ResourceARN"])

    return ChangeEvent(
        timestamp=event_time if isinstance(event_time, datetime) else datetime.fromisoformat(str(event_time)),
        change_type=change_type,
        description=f"{event_name} in {event.get('EventSource', 'AWS')}",
        actor=actor,
        affected_resources=affected_resources,
        metadata={
            "event_id": event.get("EventId"),
            "event_name": event_name,
            "event_source": event.get("EventSource"),
            "aws_region": event.get("AwsRegion"),
            "source_ip": event.get("SourceIPAddress"),
            "user_agent": event.get("UserAgent"),
            "error_code": event.get("ErrorCode"),
            "error_message": event.get("ErrorMessage"),
        },
    )


def map_cost_entry(
    cost_data: Dict[str, Any],
    dimension: str,
    dimension_value: str,
) -> CostBreakdown:
    """Map Cost Explorer data to CostBreakdown.

    Args:
        cost_data: Cost Explorer result
        dimension: Dimension name (SERVICE, REGION, etc.)
        dimension_value: Value for this dimension

    Returns:
        CostBreakdown with cost data
    """
    # Extract cost amount
    amount = 0.0
    if "Total" in cost_data:
        amount = float(cost_data["Total"].get("UnblendedCost", {}).get("Amount", 0))
    elif "Amount" in cost_data:
        amount = float(cost_data["Amount"])

    # Extract currency
    currency = "USD"
    if "Total" in cost_data:
        currency = cost_data["Total"].get("UnblendedCost", {}).get("Unit", "USD")
    elif "Unit" in cost_data:
        currency = cost_data["Unit"]

    return CostBreakdown(
        dimension=dimension,
        value=dimension_value,
        cost=amount,
        currency=currency,
    )
