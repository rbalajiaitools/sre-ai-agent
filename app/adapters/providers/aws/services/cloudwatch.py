"""CloudWatch service implementation for metrics and logs."""

import time
from datetime import datetime
from typing import List

import boto3
from botocore.exceptions import ClientError

from app.adapters.models import LogsRequest, LogsResponse, MetricsRequest, MetricsResponse
from app.adapters.providers.aws.mappers import (
    map_cloudwatch_log_event,
    map_cloudwatch_metric,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class CloudWatchService:
    """Service for interacting with AWS CloudWatch."""

    def __init__(self, session: boto3.Session) -> None:
        """Initialize CloudWatch service.

        Args:
            session: Authenticated boto3 session
        """
        self.session = session
        self.cw_client = session.client("cloudwatch")
        self.logs_client = session.client("logs")

    def get_metrics(self, request: MetricsRequest) -> MetricsResponse:
        """Get metrics from CloudWatch.

        Args:
            request: Metrics request

        Returns:
            MetricsResponse with time series data
        """
        start_time = time.time()

        logger.info(
            "fetching_cloudwatch_metrics",
            service=request.service_name,
            metrics=request.metric_names,
        )

        metrics = []

        # Build metric queries
        metric_data_queries = []
        for idx, metric_name in enumerate(request.metric_names):
            # Parse namespace and metric from metric_name
            # Format: namespace/metric or just metric (defaults to AWS/EC2)
            if "/" in metric_name:
                namespace, metric = metric_name.split("/", 1)
            else:
                namespace = "AWS/EC2"
                metric = metric_name

            query = {
                "Id": f"m{idx}",
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric,
                        "Dimensions": self._build_dimensions(request),
                    },
                    "Period": request.granularity_seconds,
                    "Stat": "Average",  # Could be parameterized
                },
            }
            metric_data_queries.append(query)

        try:
            # Get metric data
            response = self.cw_client.get_metric_data(
                MetricDataQueries=metric_data_queries,
                StartTime=request.start_time,
                EndTime=request.end_time,
            )

            # Map results
            for result in response.get("MetricDataResults", []):
                metric_series = map_cloudwatch_metric(
                    metric_data=result,
                    metric_name=result.get("Label", "unknown"),
                    unit="None",
                )
                metrics.append(metric_series)

            # Handle pagination
            while response.get("NextToken"):
                response = self.cw_client.get_metric_data(
                    MetricDataQueries=metric_data_queries,
                    StartTime=request.start_time,
                    EndTime=request.end_time,
                    NextToken=response["NextToken"],
                )

                for result in response.get("MetricDataResults", []):
                    metric_series = map_cloudwatch_metric(
                        metric_data=result,
                        metric_name=result.get("Label", "unknown"),
                        unit="None",
                    )
                    metrics.append(metric_series)

        except ClientError as e:
            logger.error(
                "cloudwatch_metrics_error",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            raise

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "cloudwatch_metrics_fetched",
            metric_count=len(metrics),
            duration_ms=duration_ms,
        )

        return MetricsResponse(
            metrics=metrics,
            source_provider="aws",
            query_duration_ms=duration_ms,
        )

    def query_logs(self, request: LogsRequest) -> LogsResponse:
        """Query logs from CloudWatch Logs.

        Args:
            request: Logs request

        Returns:
            LogsResponse with log entries
        """
        logger.info(
            "querying_cloudwatch_logs",
            service=request.service_name,
            query=request.query,
        )

        logs = []
        total_count = 0

        try:
            # Find log groups matching service name
            log_groups = self._find_log_groups(request.service_name)

            if not log_groups:
                logger.warning(
                    "no_log_groups_found",
                    service=request.service_name,
                )
                return LogsResponse(
                    logs=[],
                    total_count=0,
                    source_provider="aws",
                )

            # Start CloudWatch Logs Insights query
            query_string = self._build_logs_query(request)

            response = self.logs_client.start_query(
                logGroupNames=log_groups,
                startTime=int(request.start_time.timestamp()),
                endTime=int(request.end_time.timestamp()),
                queryString=query_string,
                limit=request.limit,
            )

            query_id = response["queryId"]

            # Poll for query completion
            max_attempts = 30
            attempt = 0

            while attempt < max_attempts:
                time.sleep(1)  # Wait 1 second between polls

                result = self.logs_client.get_query_results(queryId=query_id)

                status = result["status"]

                if status == "Complete":
                    # Process results
                    for record in result.get("results", []):
                        # Convert record to dict
                        log_dict = {field["field"]: field["value"] for field in record}

                        # Create log entry
                        log_entry = map_cloudwatch_log_event({
                            "message": log_dict.get("@message", ""),
                            "timestamp": int(log_dict.get("@timestamp", 0)),
                            "logStreamName": log_dict.get("@logStream", ""),
                            "logGroupName": log_groups[0] if log_groups else "",
                        })
                        logs.append(log_entry)

                    total_count = len(logs)
                    break

                elif status == "Failed" or status == "Cancelled":
                    logger.error("cloudwatch_logs_query_failed", status=status)
                    break

                attempt += 1

            if attempt >= max_attempts:
                logger.warning("cloudwatch_logs_query_timeout")

        except ClientError as e:
            logger.error(
                "cloudwatch_logs_error",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            raise

        logger.info(
            "cloudwatch_logs_fetched",
            log_count=len(logs),
            total_count=total_count,
        )

        return LogsResponse(
            logs=logs,
            total_count=total_count,
            source_provider="aws",
        )

    def _build_dimensions(self, request: MetricsRequest) -> List[dict]:
        """Build CloudWatch dimensions from request filters.

        Args:
            request: Metrics request

        Returns:
            List of dimension dicts
        """
        dimensions = []

        # Add service name as dimension if provided
        if request.service_name:
            dimensions.append({
                "Name": "ServiceName",
                "Value": request.service_name,
            })

        # Add other filters as dimensions
        for key, value in request.filters.items():
            dimensions.append({
                "Name": key,
                "Value": value,
            })

        return dimensions

    def _find_log_groups(self, service_name: str) -> List[str]:
        """Find log groups matching service name.

        Args:
            service_name: Service name to search for

        Returns:
            List of log group names
        """
        log_groups = []

        try:
            response = self.logs_client.describe_log_groups(
                logGroupNamePrefix=f"/aws/{service_name}",
                limit=50,
            )

            for group in response.get("logGroups", []):
                log_groups.append(group["logGroupName"])

            # Also try without prefix
            if not log_groups:
                response = self.logs_client.describe_log_groups(
                    logGroupNamePrefix=service_name,
                    limit=50,
                )

                for group in response.get("logGroups", []):
                    log_groups.append(group["logGroupName"])

        except ClientError as e:
            logger.warning("error_finding_log_groups", error=str(e))

        return log_groups

    def _build_logs_query(self, request: LogsRequest) -> str:
        """Build CloudWatch Logs Insights query string.

        Args:
            request: Logs request

        Returns:
            Query string
        """
        # Start with basic query
        query_parts = ["fields @timestamp, @message, @logStream"]

        # Add filter if provided
        if request.query:
            # Simple text search
            query_parts.append(f"| filter @message like /{request.query}/")

        # Add log level filter if provided
        if request.log_level:
            query_parts.append(f"| filter @message like /{request.log_level.value.upper()}/")

        # Sort by timestamp
        query_parts.append("| sort @timestamp desc")

        # Limit results
        query_parts.append(f"| limit {request.limit}")

        return " ".join(query_parts)
