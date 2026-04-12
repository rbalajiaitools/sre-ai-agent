"""AWS customer onboarding and IAM setup.

This module provides tools for onboarding new AWS customers:
- Generate Terraform/CloudFormation for IAM role setup
- Validate onboarding configuration
- Discover services in customer account
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OnboardingResult:
    """Result of onboarding validation."""

    success: bool
    account_id: Optional[str] = None
    role_arn: Optional[str] = None
    error_message: Optional[str] = None
    permissions_validated: bool = False
    discovered_services: Optional[List[str]] = None


@dataclass
class DiscoveryResult:
    """Result of service discovery."""

    services: Dict[str, List[str]]
    total_resources: int
    regions_scanned: List[str]


class AWSOnboardingService:
    """Service for onboarding AWS customers.

    Provides tools for generating IAM configuration and validating setup.
    """

    # Required IAM permissions for the SRE Agent role
    REQUIRED_PERMISSIONS = [
        # CloudWatch
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        # CloudWatch Logs
        "logs:FilterLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:StartQuery",
        "logs:GetQueryResults",
        # EC2
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        # ECS
        "ecs:ListClusters",
        "ecs:ListServices",
        "ecs:ListTasks",
        "ecs:DescribeClusters",
        "ecs:DescribeServices",
        "ecs:DescribeTasks",
        "ecs:DescribeTaskDefinition",
        # EKS
        "eks:ListClusters",
        "eks:DescribeCluster",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        # RDS
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBSnapshots",
        # Lambda
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        # CloudTrail
        "cloudtrail:LookupEvents",
        # Cost Explorer
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        # STS (for validation)
        "sts:GetCallerIdentity",
    ]

    def generate_terraform_snippet(
        self,
        our_aws_account_id: str,
        external_id: str,
        role_name: str = "SREAgentRole",
    ) -> str:
        """Generate Terraform HCL for customer IAM setup.

        Args:
            our_aws_account_id: Our AWS account ID that will assume the role
            external_id: Unique external ID for this customer
            role_name: Name for the IAM role

        Returns:
            Complete Terraform HCL code
        """
        terraform = f'''# SRE AI Agent - AWS IAM Role Configuration
# Deploy this in your AWS account to grant SRE Agent access

terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

# IAM Role that SRE Agent will assume
resource "aws_iam_role" "{role_name}" {{
  name               = "{role_name}"
  description        = "Role for SRE AI Agent to access AWS resources"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Principal = {{
          AWS = "arn:aws:iam::{our_aws_account_id}:root"
        }}
        Action = "sts:AssumeRole"
        Condition = {{
          StringEquals = {{
            "sts:ExternalId" = "{external_id}"
          }}
        }}
      }}
    ]
  }})

  tags = {{
    ManagedBy = "SREAgent"
    Purpose   = "Observability"
  }}
}}

# IAM Policy with required permissions
resource "aws_iam_policy" "{role_name}Policy" {{
  name        = "{role_name}Policy"
  description = "Permissions for SRE AI Agent"
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Sid    = "CloudWatchAccess"
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricData",
          "cloudwatch:ListMetrics",
          "cloudwatch:DescribeAlarms"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "CloudWatchLogsAccess"
        Effect = "Allow"
        Action = [
          "logs:FilterLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:StartQuery",
          "logs:GetQueryResults"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "EC2ReadAccess"
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:DescribeVolumes",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "ECSReadAccess"
        Effect = "Allow"
        Action = [
          "ecs:ListClusters",
          "ecs:ListServices",
          "ecs:ListTasks",
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:DescribeTasks",
          "ecs:DescribeTaskDefinition"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "EKSReadAccess"
        Effect = "Allow"
        Action = [
          "eks:ListClusters",
          "eks:DescribeCluster",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "RDSReadAccess"
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:DescribeDBSnapshots"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "LambdaReadAccess"
        Effect = "Allow"
        Action = [
          "lambda:ListFunctions",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "CloudTrailAccess"
        Effect = "Allow"
        Action = [
          "cloudtrail:LookupEvents"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "CostExplorerAccess"
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "STSAccess"
        Effect = "Allow"
        Action = [
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      }}
    ]
  }})
}}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "{role_name}_attachment" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = aws_iam_policy.{role_name}Policy.arn
}}

# Output the role ARN for configuration
output "role_arn" {{
  description = "ARN of the IAM role for SRE Agent"
  value       = aws_iam_role.{role_name}.arn
}}

output "external_id" {{
  description = "External ID for role assumption"
  value       = "{external_id}"
  sensitive   = true
}}
'''
        return terraform

    def validate_onboarding(
        self,
        role_arn: str,
        external_id: str,
        region: str = "us-east-1",
    ) -> OnboardingResult:
        """Validate customer onboarding configuration.

        Tests the role by assuming it and performing sample API calls.

        Args:
            role_arn: ARN of the customer's IAM role
            external_id: External ID for role assumption
            region: AWS region

        Returns:
            OnboardingResult with validation status
        """
        logger.info("validating_aws_onboarding", role_arn=role_arn)

        try:
            # Create STS client
            sts_client = boto3.client("sts", region_name=region)

            # Assume role
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="SREAgentOnboardingValidation",
                ExternalId=external_id,
                DurationSeconds=900,
            )

            credentials = response["Credentials"]

            # Get caller identity
            temp_sts = boto3.client(
                "sts",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )

            identity = temp_sts.get_caller_identity()
            account_id = identity["Account"]

            # Test basic permissions
            permissions_valid = self._test_permissions(credentials, region)

            # Discover services
            discovered = self._quick_discovery(credentials, region)

            logger.info(
                "aws_onboarding_validated",
                account_id=account_id,
                permissions_valid=permissions_valid,
                services_found=len(discovered),
            )

            return OnboardingResult(
                success=True,
                account_id=account_id,
                role_arn=role_arn,
                permissions_validated=permissions_valid,
                discovered_services=discovered,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "aws_onboarding_validation_failed",
                error_code=error_code,
                error_message=error_message,
            )

            return OnboardingResult(
                success=False,
                error_message=f"{error_code}: {error_message}",
            )

    def _test_permissions(self, credentials: Dict, region: str) -> bool:
        """Test that required permissions are available.

        Args:
            credentials: Temporary credentials
            region: AWS region

        Returns:
            True if permissions are valid
        """
        try:
            # Test CloudWatch
            cw_client = boto3.client(
                "cloudwatch",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            cw_client.list_metrics(MaxRecords=1)

            # Test EC2
            ec2_client = boto3.client(
                "ec2",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            ec2_client.describe_instances(MaxResults=5)

            return True

        except ClientError as e:
            logger.warning("permission_test_failed", error=str(e))
            return False

    def _quick_discovery(self, credentials: Dict, region: str) -> List[str]:
        """Quick discovery of available services.

        Args:
            credentials: Temporary credentials
            region: AWS region

        Returns:
            List of discovered service types
        """
        discovered = []

        # Check EC2
        try:
            ec2 = boto3.client(
                "ec2",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            instances = ec2.describe_instances(MaxResults=5)
            if instances["Reservations"]:
                discovered.append("EC2")
        except:
            pass

        # Check ECS
        try:
            ecs = boto3.client(
                "ecs",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            clusters = ecs.list_clusters(maxResults=10)
            if clusters.get("clusterArns"):
                discovered.append("ECS")
        except:
            pass

        # Check RDS
        try:
            rds = boto3.client(
                "rds",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            instances = rds.describe_db_instances(MaxRecords=20)
            if instances.get("DBInstances"):
                discovered.append("RDS")
        except:
            pass

        # Check Lambda
        try:
            lambda_client = boto3.client(
                "lambda",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
            functions = lambda_client.list_functions(MaxItems=10)
            if functions.get("Functions"):
                discovered.append("Lambda")
        except:
            pass

        return discovered

    def discover_services(
        self,
        session: boto3.Session,
        regions: Optional[List[str]] = None,
    ) -> DiscoveryResult:
        """Comprehensive service discovery across regions.

        Args:
            session: Authenticated boto3 session
            regions: List of regions to scan (defaults to current region)

        Returns:
            DiscoveryResult with discovered services
        """
        if regions is None:
            regions = [session.region_name]

        services: Dict[str, List[str]] = {}
        total_resources = 0

        for region in regions:
            logger.info("discovering_services", region=region)

            # EC2 instances
            try:
                ec2 = session.client("ec2", region_name=region)
                response = ec2.describe_instances()
                instances = []
                for reservation in response.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        instances.append(instance["InstanceId"])
                if instances:
                    services.setdefault("EC2", []).extend(instances)
                    total_resources += len(instances)
            except Exception as e:
                logger.warning("ec2_discovery_failed", region=region, error=str(e))

            # ECS clusters
            try:
                ecs = session.client("ecs", region_name=region)
                response = ecs.list_clusters()
                clusters = response.get("clusterArns", [])
                if clusters:
                    services.setdefault("ECS", []).extend(clusters)
                    total_resources += len(clusters)
            except Exception as e:
                logger.warning("ecs_discovery_failed", region=region, error=str(e))

            # RDS instances
            try:
                rds = session.client("rds", region_name=region)
                response = rds.describe_db_instances()
                instances = [
                    db["DBInstanceIdentifier"]
                    for db in response.get("DBInstances", [])
                ]
                if instances:
                    services.setdefault("RDS", []).extend(instances)
                    total_resources += len(instances)
            except Exception as e:
                logger.warning("rds_discovery_failed", region=region, error=str(e))

            # Lambda functions
            try:
                lambda_client = session.client("lambda", region_name=region)
                response = lambda_client.list_functions()
                functions = [f["FunctionName"] for f in response.get("Functions", [])]
                if functions:
                    services.setdefault("Lambda", []).extend(functions)
                    total_resources += len(functions)
            except Exception as e:
                logger.warning("lambda_discovery_failed", region=region, error=str(e))

        logger.info(
            "service_discovery_complete",
            total_resources=total_resources,
            service_types=len(services),
        )

        return DiscoveryResult(
            services=services,
            total_resources=total_resources,
            regions_scanned=regions,
        )
