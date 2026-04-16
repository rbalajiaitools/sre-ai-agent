"""Infrastructure specialist agent for parallel execution."""

import asyncio
from typing import Dict, Any
from boto3 import Session
import structlog

logger = structlog.get_logger(__name__)


def _use_ai_analysis(raw_findings: list, service_name: str, description: str) -> Dict[str, Any]:
    """
    Use AI to analyze raw infrastructure findings and provide detailed insights.
    
    Args:
        raw_findings: List of raw evidence strings from AWS
        service_name: Name of the service being investigated
        description: Description of the issue
        
    Returns:
        Enhanced analysis with AI-generated insights
    """
    try:
        from openai import AzureOpenAI
        from app.core.config import get_settings
        
        settings = get_settings()
        
        client = AzureOpenAI(
            api_key=settings.llm.azure_openai_api_key,
            api_version=settings.llm.azure_openai_api_version,
            azure_endpoint=settings.llm.azure_openai_endpoint
        )
        
        # Compile findings
        findings_text = '\n'.join(raw_findings)
        
        prompt = f"""Analyze these AWS infrastructure findings for service '{service_name}' with issue: {description}

{findings_text}

Provide a concise, structured analysis. Use plain text only, NO markdown formatting (no **, no ##, no ###).

HEALTH STATUS: [One line summary]

KEY FINDINGS:
• [Finding 1]
• [Finding 2]
• [Finding 3]

CONFIGURATION CONCERNS:
• [Concern 1 if any]
• [Concern 2 if any]

RECOMMENDATIONS:
• [Action 1]
• [Action 2]
• [Action 3]

Keep it concise. Use bullet points with •. Reference actual AWS resources found. Use plain text only."""
        
        response = client.chat.completions.create(
            model=settings.llm.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert SRE analyzing AWS infrastructure. Provide specific, actionable insights based on actual resource data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        ai_analysis = response.choices[0].message.content
        
        return {
            'evidence': raw_findings,
            'ai_analysis': ai_analysis,  # Separate field for AI analysis
            'recommendations': [
                'Review infrastructure health assessment',
                'Address configuration issues identified',
                'Monitor resource capacity and scaling'
            ]
        }
        
    except Exception as e:
        logger.warning("ai_analysis_failed", error=str(e))
        # Return raw findings if AI fails
        return {
            'evidence': raw_findings,
            'recommendations': ['Review infrastructure manually', 'Check resource configurations']
        }


class InfrastructureAgent:
    """Analyzes infrastructure health and recent changes."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def investigate(self, service_name: str, description: str) -> Dict[str, Any]:
        """
        Investigate infrastructure issues with comprehensive AWS resource analysis.
        Dynamically checks ALL relevant AWS services based on service name and description.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with detailed evidence and recommendations
        """
        evidence = []
        recommendations = []
        services_checked = []
        
        try:
            # Determine which AWS services to check based on service name and description
            desc_lower = description.lower()
            service_lower = service_name.lower()
            
            # Check S3 buckets (for static sites, storage, etc.)
            if 's3' in service_lower or 's3' in desc_lower or 'bucket' in desc_lower or 'static' in desc_lower or 'website' in desc_lower or 'dashboard' in service_lower:
                services_checked.append('S3')
                s3 = self.session.client('s3')
                try:
                    buckets = s3.list_buckets()
                    s3_count = 0
                    
                    for bucket in buckets.get('Buckets', []):
                        bucket_name = bucket['Name']
                        if service_name.lower() in bucket_name.lower() or any(keyword in bucket_name.lower() for keyword in ['demo', 'dashboard', 'cloudscore']):
                            s3_count += 1
                            creation_date = bucket.get('CreationDate', 'unknown')
                            evidence.append(f"S3 Bucket: {bucket_name} - Created: {creation_date}")
                            
                            # Check bucket configuration
                            try:
                                # Check website configuration
                                try:
                                    website_config = s3.get_bucket_website(Bucket=bucket_name)
                                    index_doc = website_config.get('IndexDocument', {}).get('Suffix', 'N/A')
                                    error_doc = website_config.get('ErrorDocument', {}).get('Key', 'N/A')
                                    evidence.append(f"✓ S3 {bucket_name} has website hosting enabled - Index: {index_doc}, Error: {error_doc}")
                                    evidence.append(f"Website URL: http://{bucket_name}.s3-website-{self.session.region_name}.amazonaws.com")
                                except Exception:
                                    evidence.append(f"⚠️ S3 {bucket_name} does NOT have website hosting enabled")
                                    recommendations.append(f"Enable website hosting on bucket {bucket_name} if needed")
                                
                                # Check bucket policy
                                try:
                                    policy = s3.get_bucket_policy(Bucket=bucket_name)
                                    evidence.append(f"✓ S3 {bucket_name} has bucket policy configured")
                                except Exception:
                                    evidence.append(f"⚠️ S3 {bucket_name} has NO bucket policy - may not be publicly accessible")
                                    recommendations.append(f"Configure bucket policy for {bucket_name} to allow public read access")
                                
                                # Check public access block
                                try:
                                    public_access = s3.get_public_access_block(Bucket=bucket_name)
                                    config = public_access.get('PublicAccessBlockConfiguration', {})
                                    if config.get('BlockPublicAcls') or config.get('BlockPublicPolicy'):
                                        evidence.append(f"⚠️ S3 {bucket_name} has public access BLOCKED - website may not be accessible")
                                        recommendations.append(f"Review public access settings for {bucket_name}")
                                    else:
                                        evidence.append(f"✓ S3 {bucket_name} allows public access")
                                except Exception:
                                    evidence.append(f"S3 {bucket_name} public access block not configured (default allows public)")
                                
                                # Check bucket versioning
                                try:
                                    versioning = s3.get_bucket_versioning(Bucket=bucket_name)
                                    status = versioning.get('Status', 'Disabled')
                                    evidence.append(f"S3 {bucket_name} versioning: {status}")
                                except Exception:
                                    pass
                                    
                            except Exception as config_error:
                                logger.warning("s3_config_check_failed", bucket=bucket_name, error=str(config_error))
                    
                    if s3_count == 0:
                        evidence.append(f"No S3 buckets found matching service name '{service_name}'")
                    else:
                        evidence.append(f"Found {s3_count} S3 bucket(s) for service")
                        
                except Exception as e:
                    logger.warning("s3_check_failed", error=str(e))
                    evidence.append(f"S3 check failed: {str(e)}")
            
            # Check CloudFront distributions (for CDN, static sites)
            if 'cloudfront' in service_lower or 'cloudfront' in desc_lower or 'cdn' in desc_lower or 's3' in service_lower or 'static' in desc_lower:
                services_checked.append('CloudFront')
                try:
                    cloudfront = self.session.client('cloudfront')
                    distributions = cloudfront.list_distributions()
                    cf_count = 0
                    
                    for dist in distributions.get('DistributionList', {}).get('Items', []):
                        dist_id = dist.get('Id', '')
                        domain_name = dist.get('DomainName', '')
                        status = dist.get('Status', 'unknown')
                        enabled = dist.get('Enabled', False)
                        
                        # Check if related to our service
                        origins = dist.get('Origins', {}).get('Items', [])
                        for origin in origins:
                            origin_domain = origin.get('DomainName', '')
                            if service_name.lower() in origin_domain.lower():
                                cf_count += 1
                                evidence.append(f"CloudFront Distribution: {dist_id} - Domain: {domain_name}, Status: {status}, Enabled: {enabled}")
                                evidence.append(f"Origin: {origin_domain}")
                                
                                if not enabled:
                                    recommendations.append(f"CloudFront distribution {dist_id} is disabled")
                                break
                    
                    if cf_count > 0:
                        evidence.append(f"Found {cf_count} CloudFront distribution(s)")
                        
                except Exception as e:
                    logger.warning("cloudfront_check_failed", error=str(e))
            
            # Check EC2 instances
            if 'ec2' in service_lower or 'ec2' in desc_lower or 'instance' in desc_lower or 'vm' in desc_lower:
                services_checked.append('EC2')
                ec2 = self.session.client('ec2')
                try:
                    instances = ec2.describe_instances(
                        Filters=[
                            {'Name': 'tag:Name', 'Values': [f'*{service_name}*']},
                            {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}
                        ]
                    )
                    
                    instance_count = 0
                    for reservation in instances.get('Reservations', []):
                        for instance in reservation.get('Instances', []):
                            instance_count += 1
                            state = instance['State']['Name']
                            instance_id = instance['InstanceId']
                            instance_type = instance.get('InstanceType', 'unknown')
                            
                            if state != 'running':
                                evidence.append(f"⚠️ EC2 instance {instance_id} ({instance_type}) is {state}")
                                recommendations.append(f"Investigate EC2 instance {instance_id}")
                            else:
                                evidence.append(f"✓ EC2 instance {instance_id} ({instance_type}) is running")
                    
                    if instance_count > 0:
                        evidence.append(f"Found {instance_count} EC2 instance(s)")
                        
                except Exception as e:
                    logger.warning("ec2_check_failed", error=str(e))
            
            # Check Lambda functions
            if 'lambda' in service_lower or 'lambda' in desc_lower or 'function' in desc_lower or 'serverless' in desc_lower:
                services_checked.append('Lambda')
                lambda_client = self.session.client('lambda')
                try:
                    functions = lambda_client.list_functions()
                    lambda_count = 0
                    
                    for func in functions.get('Functions', []):
                        if service_name.lower() in func['FunctionName'].lower():
                            lambda_count += 1
                            func_name = func['FunctionName']
                            runtime = func.get('Runtime', 'unknown')
                            memory = func.get('MemorySize', 0)
                            
                            evidence.append(f"Lambda: {func_name} - Runtime: {runtime}, Memory: {memory}MB")
                            
                            try:
                                config = lambda_client.get_function_configuration(FunctionName=func_name)
                                if config.get('LastUpdateStatus') == 'Failed':
                                    evidence.append(f"⚠️ Lambda {func_name} last update FAILED")
                                    recommendations.append(f"Fix Lambda function {func_name} deployment")
                            except Exception:
                                pass
                    
                    if lambda_count > 0:
                        evidence.append(f"Found {lambda_count} Lambda function(s)")
                        
                except Exception as e:
                    logger.warning("lambda_check_failed", error=str(e))
            
            # Check ECS services
            if 'ecs' in service_lower or 'ecs' in desc_lower or 'container' in desc_lower or 'docker' in desc_lower:
                services_checked.append('ECS')
                ecs = self.session.client('ecs')
                try:
                    clusters = ecs.list_clusters()
                    ecs_count = 0
                    
                    for cluster_arn in clusters.get('clusterArns', [])[:5]:
                        services_list = ecs.list_services(cluster=cluster_arn)
                        
                        for service_arn in services_list.get('serviceArns', []):
                            service_details = ecs.describe_services(cluster=cluster_arn, services=[service_arn])
                            
                            for svc in service_details.get('services', []):
                                svc_name = svc.get('serviceName', '')
                                if service_name.lower() in svc_name.lower():
                                    ecs_count += 1
                                    running = svc.get('runningCount', 0)
                                    desired = svc.get('desiredCount', 0)
                                    
                                    if running < desired:
                                        evidence.append(f"⚠️ ECS service {svc_name}: {running}/{desired} tasks running")
                                        recommendations.append(f"Scale up ECS service {svc_name}")
                                    else:
                                        evidence.append(f"✓ ECS service {svc_name}: {running}/{desired} tasks running")
                    
                    if ecs_count > 0:
                        evidence.append(f"Found {ecs_count} ECS service(s)")
                        
                except Exception as e:
                    logger.warning("ecs_check_failed", error=str(e))
            
            # Check Load Balancers
            if 'elb' in service_lower or 'elb' in desc_lower or 'load' in desc_lower or 'balancer' in desc_lower or 'alb' in desc_lower:
                services_checked.append('ELB')
                try:
                    elb = self.session.client('elbv2')
                    load_balancers = elb.describe_load_balancers()
                    lb_count = 0
                    
                    for lb in load_balancers.get('LoadBalancers', []):
                        lb_name = lb.get('LoadBalancerName', '')
                        if service_name.lower() in lb_name.lower():
                            lb_count += 1
                            lb_state = lb.get('State', {}).get('Code', 'unknown')
                            lb_type = lb.get('Type', 'unknown')
                            
                            evidence.append(f"Load Balancer: {lb_name} - Type: {lb_type}, State: {lb_state}")
                            
                            if lb_state != 'active':
                                recommendations.append(f"Investigate Load Balancer {lb_name}")
                    
                    if lb_count > 0:
                        evidence.append(f"Found {lb_count} Load Balancer(s)")
                        
                except Exception as e:
                    logger.warning("elb_check_failed", error=str(e))
            
            # Check RDS databases
            if 'rds' in service_lower or 'rds' in desc_lower or 'database' in desc_lower or 'db' in desc_lower or 'postgres' in desc_lower or 'mysql' in desc_lower:
                services_checked.append('RDS')
                try:
                    rds = self.session.client('rds')
                    databases = rds.describe_db_instances()
                    rds_count = 0
                    
                    for db in databases.get('DBInstances', []):
                        db_id = db.get('DBInstanceIdentifier', '')
                        if service_name.lower() in db_id.lower():
                            rds_count += 1
                            db_status = db.get('DBInstanceStatus', 'unknown')
                            db_engine = db.get('Engine', 'unknown')
                            
                            evidence.append(f"RDS Database: {db_id} - Engine: {db_engine}, Status: {db_status}")
                            
                            if db_status != 'available':
                                recommendations.append(f"Investigate RDS database {db_id}")
                    
                    if rds_count > 0:
                        evidence.append(f"Found {rds_count} RDS database(s)")
                        
                except Exception as e:
                    logger.warning("rds_check_failed", error=str(e))
            
            # Check DynamoDB tables
            if 'dynamodb' in service_lower or 'dynamodb' in desc_lower or 'nosql' in desc_lower:
                services_checked.append('DynamoDB')
                try:
                    dynamodb = self.session.client('dynamodb')
                    tables = dynamodb.list_tables()
                    ddb_count = 0
                    
                    for table_name in tables.get('TableNames', []):
                        if service_name.lower() in table_name.lower():
                            ddb_count += 1
                            table_desc = dynamodb.describe_table(TableName=table_name)
                            table_status = table_desc.get('Table', {}).get('TableStatus', 'unknown')
                            
                            evidence.append(f"DynamoDB Table: {table_name} - Status: {table_status}")
                    
                    if ddb_count > 0:
                        evidence.append(f"Found {ddb_count} DynamoDB table(s)")
                        
                except Exception as e:
                    logger.warning("dynamodb_check_failed", error=str(e))
            
            # Check API Gateway
            if 'api' in service_lower or 'api' in desc_lower or 'gateway' in desc_lower or 'rest' in desc_lower:
                services_checked.append('API Gateway')
                try:
                    apigw = self.session.client('apigateway')
                    apis = apigw.get_rest_apis()
                    api_count = 0
                    
                    for api in apis.get('items', []):
                        api_name = api.get('name', '')
                        if service_name.lower() in api_name.lower():
                            api_count += 1
                            api_id = api.get('id', '')
                            
                            evidence.append(f"API Gateway: {api_name} (ID: {api_id})")
                    
                    if api_count > 0:
                        evidence.append(f"Found {api_count} API Gateway(s)")
                        
                except Exception as e:
                    logger.warning("apigateway_check_failed", error=str(e))
            
            # If no specific services matched, do a broad scan
            if not services_checked:
                services_checked = ['S3', 'EC2', 'Lambda', 'ELB']
                evidence.append(f"Performing broad infrastructure scan for '{service_name}'")
                
                # Quick S3 check
                try:
                    s3 = self.session.client('s3')
                    buckets = s3.list_buckets()
                    for bucket in buckets.get('Buckets', [])[:10]:
                        if service_name.lower() in bucket['Name'].lower():
                            evidence.append(f"S3 Bucket: {bucket['Name']}")
                except Exception:
                    pass
                
                # Quick Lambda check
                try:
                    lambda_client = self.session.client('lambda')
                    functions = lambda_client.list_functions(MaxItems=20)
                    for func in functions.get('Functions', []):
                        if service_name.lower() in func['FunctionName'].lower():
                            evidence.append(f"Lambda: {func['FunctionName']}")
                except Exception:
                    pass
                
        except Exception as e:
            logger.error("infrastructure_investigation_failed", error=str(e))
            evidence.append(f"Infrastructure investigation error: {str(e)}")
        
        # Add summary of services checked
        if services_checked:
            evidence.insert(0, f"Checked AWS services: {', '.join(services_checked)}")
        
        # Ensure we always return something meaningful
        if len(evidence) <= 1:  # Only the services checked message
            evidence.append(f"No infrastructure resources found matching '{service_name}'")
            recommendations.append('Verify service name and check resource tagging')
        
        if not recommendations:
            recommendations = ['Continue monitoring infrastructure health', 'Review resource configurations']
        
        # Use AI to enhance analysis if we have meaningful findings
        if len(evidence) > 3:
            return _use_ai_analysis(evidence, service_name, description)
        
        return {
            'evidence': evidence,
            'recommendations': recommendations
        }
