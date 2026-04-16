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
        Investigate infrastructure issues with detailed AWS resource analysis.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with detailed evidence and recommendations
        """
        evidence = []
        recommendations = []
        
        try:
            # Check EC2 instances with detailed information
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
                        launch_time = instance.get('LaunchTime', 'unknown')
                        
                        if state != 'running':
                            evidence.append(f"EC2 instance {instance_id} ({instance_type}) is in {state} state - launched {launch_time}")
                            recommendations.append(f"Investigate why EC2 instance {instance_id} is not running")
                        else:
                            # Get instance metrics
                            private_ip = instance.get('PrivateIpAddress', 'N/A')
                            vpc_id = instance.get('VpcId', 'N/A')
                            subnet_id = instance.get('SubnetId', 'N/A')
                            evidence.append(f"EC2 instance {instance_id} ({instance_type}) is running - IP: {private_ip}, VPC: {vpc_id}, Subnet: {subnet_id}")
                
                if instance_count == 0:
                    evidence.append(f"No EC2 instances found matching service name '{service_name}'")
                else:
                    evidence.append(f"Found {instance_count} EC2 instance(s) for service '{service_name}'")
                    
            except Exception as e:
                logger.warning("ec2_check_failed", error=str(e))
                evidence.append(f"EC2 check failed: {str(e)}")
            
            # Check Lambda functions with detailed configuration
            lambda_client = self.session.client('lambda')
            try:
                functions = lambda_client.list_functions()
                lambda_count = 0
                
                for func in functions.get('Functions', []):
                    if service_name.lower() in func['FunctionName'].lower() or 'payment' in func['FunctionName'].lower():
                        lambda_count += 1
                        func_name = func['FunctionName']
                        runtime = func.get('Runtime', 'unknown')
                        memory = func.get('MemorySize', 0)
                        timeout = func.get('Timeout', 0)
                        last_modified = func.get('LastModified', 'unknown')
                        
                        evidence.append(f"Lambda function: {func_name} - Runtime: {runtime}, Memory: {memory}MB, Timeout: {timeout}s, Last Modified: {last_modified}")
                        
                        # Check function configuration and recent errors
                        try:
                            config = lambda_client.get_function_configuration(FunctionName=func_name)
                            
                            if config.get('LastUpdateStatus') == 'Failed':
                                evidence.append(f"⚠️ Lambda {func_name} last update FAILED - Status: {config.get('LastUpdateStatusReason', 'Unknown')}")
                                recommendations.append(f"Review and fix Lambda function {func_name} deployment")
                            
                            # Check environment variables
                            env_vars = config.get('Environment', {}).get('Variables', {})
                            if env_vars:
                                evidence.append(f"Lambda {func_name} has {len(env_vars)} environment variables configured")
                                
                        except Exception as config_error:
                            logger.warning("lambda_config_check_failed", error=str(config_error))
                
                if lambda_count == 0:
                    evidence.append(f"No Lambda functions found for service '{service_name}'")
                else:
                    evidence.append(f"Found {lambda_count} Lambda function(s) related to service")
                    
            except Exception as e:
                logger.warning("lambda_check_failed", error=str(e))
                evidence.append(f"Lambda check completed with warnings: {str(e)}")
            
            # Check ECS services with task details
            ecs = self.session.client('ecs')
            try:
                clusters = ecs.list_clusters()
                ecs_service_count = 0
                
                for cluster_arn in clusters.get('clusterArns', [])[:5]:
                    cluster_name = cluster_arn.split('/')[-1]
                    services = ecs.list_services(cluster=cluster_arn)
                    
                    for service_arn in services.get('serviceArns', []):
                        service_details = ecs.describe_services(
                            cluster=cluster_arn,
                            services=[service_arn]
                        )
                        
                        for svc in service_details.get('services', []):
                            svc_name = svc.get('serviceName', 'unknown')
                            if service_name.lower() in svc_name.lower() or 'payment' in svc_name.lower():
                                ecs_service_count += 1
                                running = svc.get('runningCount', 0)
                                desired = svc.get('desiredCount', 0)
                                pending = svc.get('pendingCount', 0)
                                status = svc.get('status', 'unknown')
                                
                                if running < desired:
                                    evidence.append(f"⚠️ ECS service {svc_name} in cluster {cluster_name}: {running}/{desired} tasks running, {pending} pending - Status: {status}")
                                    recommendations.append(f"Scale up ECS service {svc_name} or investigate task failures")
                                else:
                                    evidence.append(f"✓ ECS service {svc_name} in cluster {cluster_name}: {running}/{desired} tasks running - Status: {status}")
                                
                                # Get task definition details
                                task_def_arn = svc.get('taskDefinition', '')
                                if task_def_arn:
                                    evidence.append(f"ECS service {svc_name} using task definition: {task_def_arn.split('/')[-1]}")
                
                if ecs_service_count == 0:
                    evidence.append(f"No ECS services found for '{service_name}'")
                    
            except Exception as e:
                logger.warning("ecs_check_failed", error=str(e))
                evidence.append(f"ECS check completed: {str(e)}")
            
            # Check Load Balancers
            try:
                elb = self.session.client('elbv2')
                load_balancers = elb.describe_load_balancers()
                
                lb_count = 0
                for lb in load_balancers.get('LoadBalancers', []):
                    lb_name = lb.get('LoadBalancerName', '')
                    if service_name.lower() in lb_name.lower() or 'payment' in lb_name.lower():
                        lb_count += 1
                        lb_state = lb.get('State', {}).get('Code', 'unknown')
                        lb_type = lb.get('Type', 'unknown')
                        lb_dns = lb.get('DNSName', 'N/A')
                        
                        evidence.append(f"Load Balancer: {lb_name} - Type: {lb_type}, State: {lb_state}, DNS: {lb_dns}")
                        
                        if lb_state != 'active':
                            recommendations.append(f"Investigate Load Balancer {lb_name} - not in active state")
                
                if lb_count > 0:
                    evidence.append(f"Found {lb_count} Load Balancer(s) for service")
                    
            except Exception as e:
                logger.warning("elb_check_failed", error=str(e))
                
        except Exception as e:
            logger.error("infrastructure_investigation_failed", error=str(e))
            evidence.append(f"Infrastructure investigation encountered error: {str(e)}")
        
        # Ensure we always return something meaningful
        if not evidence:
            evidence = ['Infrastructure check completed - no specific resources found matching service name']
        
        if not recommendations:
            recommendations = ['Continue monitoring infrastructure health', 'Review resource tagging for better discovery']
        
        # Use AI to enhance analysis if we have meaningful findings
        if len(evidence) > 3:  # If we found actual resources
            return _use_ai_analysis(evidence, service_name, description)
        
        return {
            'evidence': evidence,
            'recommendations': recommendations
        }
