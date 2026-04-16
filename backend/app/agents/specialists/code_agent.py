"""Code specialist agent for parallel execution."""

from typing import Dict, Any
from boto3 import Session
import structlog

logger = structlog.get_logger(__name__)


def _use_ai_analysis(raw_findings: list, service_name: str, description: str) -> Dict[str, Any]:
    """
    Use AI to analyze raw code/deployment findings and provide detailed insights.
    
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
        
        prompt = f"""Analyze these AWS code and deployment findings for service '{service_name}' with issue: {description}

{findings_text}

Provide a concise, structured analysis. Use plain text only, NO markdown formatting (no **, no ##, no ###).

DEPLOYMENT STATUS: [One line summary]

KEY FINDINGS:
• [Finding 1]
• [Finding 2]
• [Finding 3]

CODE CONCERNS:
• [Concern 1 if any]
• [Concern 2 if any]

RECOMMENDATIONS:
• [Action 1]
• [Action 2]
• [Action 3]

Keep it concise. Use bullet points with •. Reference actual Lambda functions, deployments, and configurations found. Use plain text only."""
        
        response = client.chat.completions.create(
            model=settings.llm.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert SRE analyzing AWS code deployments and Lambda functions. Provide specific, actionable insights based on actual deployment data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        ai_analysis = response.choices[0].message.content
        
        return {
            'evidence': raw_findings,
            'ai_analysis': ai_analysis,
            'recommendations': [
                'Review deployment status and configuration',
                'Check Lambda function settings',
                'Monitor deployment success rate'
            ]
        }
        
    except Exception as e:
        logger.warning("ai_analysis_failed", error=str(e))
        # Return raw findings if AI fails
        return {
            'evidence': raw_findings,
            'recommendations': ['Review code manually', 'Check deployment logs']
        }


class CodeAgent:
    """Analyzes code deployments and configuration."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def investigate(self, service_name: str, description: str) -> Dict[str, Any]:
        """
        Investigate code and deployment issues.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with evidence and recommendations
        """
        evidence = []
        recommendations = []
        
        try:
            # Check Lambda function configuration
            if 'lambda' in description.lower() or 'function' in description.lower():
                try:
                    lambda_client = self.session.client('lambda')
                    
                    # Get function configuration
                    config = lambda_client.get_function_configuration(
                        FunctionName=service_name
                    )
                    
                    # Check runtime
                    runtime = config.get('Runtime', 'unknown')
                    evidence.append(f"Lambda runtime: {runtime}")
                    
                    # Check memory and timeout
                    memory = config.get('MemorySize', 0)
                    timeout = config.get('Timeout', 0)
                    evidence.append(f"Lambda configuration: {memory}MB memory, {timeout}s timeout")
                    
                    if timeout < 30:
                        recommendations.append(f"Consider increasing Lambda timeout (currently {timeout}s)")
                    
                    # Check environment variables
                    env_vars = config.get('Environment', {}).get('Variables', {})
                    evidence.append(f"Lambda has {len(env_vars)} environment variables configured")
                    
                    # Check last update status
                    last_update_status = config.get('LastUpdateStatus', 'Unknown')
                    if last_update_status == 'Failed':
                        evidence.append(f"Lambda last update status: {last_update_status}")
                        recommendations.append("Review Lambda deployment logs for errors")
                    
                    # Get function code info
                    try:
                        func_info = lambda_client.get_function(FunctionName=service_name)
                        code_size = func_info.get('Configuration', {}).get('CodeSize', 0)
                        evidence.append(f"Lambda code size: {code_size / 1024:.1f} KB")
                        
                        # Check if code is too large
                        if code_size > 50 * 1024 * 1024:  # 50MB
                            recommendations.append("Lambda code size is large, consider using layers")
                            
                    except Exception as e:
                        logger.warning("lambda_code_info_failed", error=str(e))
                        
                except Exception as e:
                    logger.warning("lambda_config_check_failed", error=str(e))
            
            # Check CodeDeploy deployments
            try:
                codedeploy = self.session.client('codedeploy')
                
                # List applications
                applications = codedeploy.list_applications()
                for app_name in applications.get('applications', []):
                    if service_name.lower() in app_name.lower():
                        evidence.append(f"Found CodeDeploy application: {app_name}")
                        
                        # Get recent deployments
                        try:
                            deployment_groups = codedeploy.list_deployment_groups(
                                applicationName=app_name
                            )
                            
                            for dg_name in deployment_groups.get('deploymentGroups', [])[:3]:
                                deployments = codedeploy.list_deployments(
                                    applicationName=app_name,
                                    deploymentGroupName=dg_name,
                                    includeOnlyStatuses=['Failed', 'Stopped']
                                )
                                
                                failed_count = len(deployments.get('deployments', []))
                                if failed_count > 0:
                                    evidence.append(f"Found {failed_count} failed deployments in {dg_name}")
                                    recommendations.append(f"Review failed deployments in {dg_name}")
                                    
                        except Exception as e:
                            logger.warning("codedeploy_deployments_failed", error=str(e))
                            
            except Exception as e:
                logger.warning("codedeploy_check_failed", error=str(e))
                
        except Exception as e:
            logger.error("code_investigation_failed", error=str(e))
            evidence.append(f"Code check encountered error: {str(e)}")
        
        # Ensure we always return something
        if not evidence:
            evidence = ['No code or deployment issues detected']
        
        if not recommendations:
            recommendations = ['Continue monitoring deployments']
        
        # ALWAYS use AI to enhance analysis, even with minimal findings
        return _use_ai_analysis(evidence, service_name, description)
