"""AWS Connector implementation."""

import boto3
from typing import Any, Optional
from datetime import datetime, timedelta

from connectors.sdk import BaseConnector, retry
from shared.logging import get_logger

logger = get_logger(__name__)


class AWSConnector(BaseConnector):
    """AWS connector for EC2, Lambda, ECS, CloudWatch, etc."""
    
    def __init__(self, config: dict):
        """Initialize AWS connector.
        
        Args:
            config: Configuration with aws_access_key_id, aws_secret_access_key, region
        """
        super().__init__(config)
        self.session: Optional[boto3.Session] = None
        self.clients = {}
    
    async def connect(self) -> bool:
        """Establish AWS connection."""
        try:
            if not self.validate_config(["aws_access_key_id", "aws_secret_access_key", "region"]):
                return False
            
            self.session = boto3.Session(
                aws_access_key_id=self.get_config("aws_access_key_id"),
                aws_secret_access_key=self.get_config("aws_secret_access_key"),
                region_name=self.get_config("region", "us-east-1")
            )
            
            # Test connection with STS
            sts = self.session.client("sts")
            identity = sts.get_caller_identity()
            
            self.connected = True
            logger.info("aws_connected", account_id=identity["Account"])
            return True
            
        except Exception as e:
            logger.error("aws_connection_failed", error=str(e))
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close AWS connection."""
        self.clients.clear()
        self.session = None
        self.connected = False
        logger.info("aws_disconnected")
        return True
    
    async def health_check(self) -> dict:
        """Check AWS connection health."""
        try:
            if not self.session:
                return {"status": "disconnected", "healthy": False}
            
            sts = self.session.client("sts")
            identity = sts.get_caller_identity()
            
            self.last_health_check = datetime.utcnow()
            self.health_status = "healthy"
            
            return {
                "status": "healthy",
                "healthy": True,
                "account_id": identity["Account"],
                "region": self.get_config("region"),
                "last_check": self.last_health_check.isoformat()
            }
            
        except Exception as e:
            self.health_status = "unhealthy"
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    def get_client(self, service: str):
        """Get or create AWS service client.
        
        Args:
            service: AWS service name (ec2, lambda, ecs, etc.)
            
        Returns:
            Boto3 client for the service
        """
        if service not in self.clients:
            self.clients[service] = self.session.client(service)
        return self.clients[service]
    
    @retry(max_attempts=3)
    async def execute(self, method: str, **kwargs) -> Any:
        """Execute AWS connector method.
        
        Args:
            method: Method name (list_ec2_instances, get_cloudwatch_metrics, etc.)
            **kwargs: Method parameters
            
        Returns:
            Method execution result
        """
        if not self.connected:
            await self.connect()
        
        method_map = {
            "list_ec2_instances": self.list_ec2_instances,
            "get_ec2_instance": self.get_ec2_instance,
            "list_lambda_functions": self.list_lambda_functions,
            "get_lambda_function": self.get_lambda_function,
            "list_ecs_services": self.list_ecs_services,
            "get_cloudwatch_metrics": self.get_cloudwatch_metrics,
            "get_cloudwatch_logs": self.get_cloudwatch_logs,
            "list_cloudtrail_events": self.list_cloudtrail_events,
            "get_cost_and_usage": self.get_cost_and_usage,
        }
        
        if method not in method_map:
            raise ValueError(f"Unknown method: {method}")
        
        return await method_map[method](**kwargs)
    
    async def list_ec2_instances(self, filters: Optional[list] = None) -> list:
        """List EC2 instances.
        
        Args:
            filters: EC2 filters
            
        Returns:
            List of EC2 instances
        """
        ec2 = self.get_client("ec2")
        
        params = {}
        if filters:
            params["Filters"] = filters
        
        response = ec2.describe_instances(**params)
        
        instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append({
                    "instance_id": instance["InstanceId"],
                    "instance_type": instance["InstanceType"],
                    "state": instance["State"]["Name"],
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "launch_time": instance["LaunchTime"].isoformat(),
                    "tags": {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                })
        
        return instances
    
    async def get_ec2_instance(self, instance_id: str) -> dict:
        """Get EC2 instance details.
        
        Args:
            instance_id: EC2 instance ID
            
        Returns:
            Instance details
        """
        instances = await self.list_ec2_instances(
            filters=[{"Name": "instance-id", "Values": [instance_id]}]
        )
        return instances[0] if instances else None
    
    async def list_lambda_functions(self) -> list:
        """List Lambda functions.
        
        Returns:
            List of Lambda functions
        """
        lambda_client = self.get_client("lambda")
        
        response = lambda_client.list_functions()
        
        functions = []
        for func in response["Functions"]:
            functions.append({
                "function_name": func["FunctionName"],
                "runtime": func["Runtime"],
                "handler": func["Handler"],
                "memory_size": func["MemorySize"],
                "timeout": func["Timeout"],
                "last_modified": func["LastModified"]
            })
        
        return functions
    
    async def get_lambda_function(self, function_name: str) -> dict:
        """Get Lambda function details.
        
        Args:
            function_name: Lambda function name
            
        Returns:
            Function details
        """
        lambda_client = self.get_client("lambda")
        
        response = lambda_client.get_function(FunctionName=function_name)
        
        return {
            "function_name": response["Configuration"]["FunctionName"],
            "runtime": response["Configuration"]["Runtime"],
            "handler": response["Configuration"]["Handler"],
            "code_size": response["Configuration"]["CodeSize"],
            "memory_size": response["Configuration"]["MemorySize"],
            "timeout": response["Configuration"]["Timeout"],
            "last_modified": response["Configuration"]["LastModified"]
        }
    
    async def list_ecs_services(self, cluster: str) -> list:
        """List ECS services.
        
        Args:
            cluster: ECS cluster name
            
        Returns:
            List of ECS services
        """
        ecs = self.get_client("ecs")
        
        response = ecs.list_services(cluster=cluster)
        
        if not response["serviceArns"]:
            return []
        
        services_response = ecs.describe_services(
            cluster=cluster,
            services=response["serviceArns"]
        )
        
        services = []
        for service in services_response["services"]:
            services.append({
                "service_name": service["serviceName"],
                "status": service["status"],
                "desired_count": service["desiredCount"],
                "running_count": service["runningCount"],
                "pending_count": service["pendingCount"],
                "launch_type": service.get("launchType", "UNKNOWN")
            })
        
        return services
    
    async def get_cloudwatch_metrics(
        self,
        namespace: str,
        metric_name: str,
        dimensions: list,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: list = ["Average"]
    ) -> list:
        """Get CloudWatch metrics.
        
        Args:
            namespace: CloudWatch namespace
            metric_name: Metric name
            dimensions: Metric dimensions
            start_time: Start time
            end_time: End time
            period: Period in seconds
            statistics: Statistics to retrieve
            
        Returns:
            List of metric data points
        """
        cloudwatch = self.get_client("cloudwatch")
        
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=statistics
        )
        
        return [
            {
                "timestamp": dp["Timestamp"].isoformat(),
                "value": dp.get("Average", dp.get("Sum", dp.get("Maximum", 0))),
                "unit": dp["Unit"]
            }
            for dp in response["Datapoints"]
        ]
    
    async def get_cloudwatch_logs(
        self,
        log_group: str,
        log_stream: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filter_pattern: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get CloudWatch logs.
        
        Args:
            log_group: Log group name
            log_stream: Log stream name (optional)
            start_time: Start time (optional)
            end_time: End time (optional)
            filter_pattern: Filter pattern (optional)
            limit: Maximum number of events
            
        Returns:
            List of log events
        """
        logs = self.get_client("logs")
        
        params = {
            "logGroupName": log_group,
            "limit": limit
        }
        
        if log_stream:
            params["logStreamNames"] = [log_stream]
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        if filter_pattern:
            params["filterPattern"] = filter_pattern
        
        response = logs.filter_log_events(**params)
        
        return [
            {
                "timestamp": datetime.fromtimestamp(event["timestamp"] / 1000).isoformat(),
                "message": event["message"],
                "log_stream": event["logStreamName"]
            }
            for event in response["events"]
        ]
    
    async def list_cloudtrail_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 50
    ) -> list:
        """List CloudTrail events.
        
        Args:
            start_time: Start time (optional, defaults to 1 hour ago)
            end_time: End time (optional, defaults to now)
            max_results: Maximum number of events
            
        Returns:
            List of CloudTrail events
        """
        cloudtrail = self.get_client("cloudtrail")
        
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        response = cloudtrail.lookup_events(
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=max_results
        )
        
        return [
            {
                "event_id": event["EventId"],
                "event_name": event["EventName"],
                "event_time": event["EventTime"].isoformat(),
                "username": event.get("Username", "Unknown"),
                "resources": event.get("Resources", [])
            }
            for event in response["Events"]
        ]
    
    async def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "DAILY",
        metrics: list = ["UnblendedCost"]
    ) -> dict:
        """Get cost and usage data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY or MONTHLY
            metrics: Metrics to retrieve
            
        Returns:
            Cost and usage data
        """
        ce = self.get_client("ce")
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                "Start": start_date,
                "End": end_date
            },
            Granularity=granularity,
            Metrics=metrics
        )
        
        return {
            "results": [
                {
                    "start": result["TimePeriod"]["Start"],
                    "end": result["TimePeriod"]["End"],
                    "amount": float(result["Total"]["UnblendedCost"]["Amount"]),
                    "unit": result["Total"]["UnblendedCost"]["Unit"]
                }
                for result in response["ResultsByTime"]
            ]
        }
