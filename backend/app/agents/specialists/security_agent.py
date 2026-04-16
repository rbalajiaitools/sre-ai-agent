"""Security specialist agent for parallel execution."""

from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from boto3 import Session
import structlog

logger = structlog.get_logger(__name__)


def _use_ai_analysis(raw_findings: list, service_name: str, description: str) -> Dict[str, Any]:
    """
    Use AI to analyze raw security findings and provide detailed insights.
    
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
        
        prompt = f"""Analyze these AWS security findings for service '{service_name}' with issue: {description}

{findings_text}

Provide a concise, structured analysis. Use plain text only, NO markdown formatting (no **, no ##, no ###).

SECURITY STATUS: [One line summary]

KEY FINDINGS:
• [Finding 1]
• [Finding 2]
• [Finding 3]

SECURITY CONCERNS:
• [Concern 1 if any]
• [Concern 2 if any]

RECOMMENDATIONS:
• [Action 1]
• [Action 2]
• [Action 3]

Keep it concise. Use bullet points with •. Reference actual IAM roles, policies, and events found. Use plain text only."""
        
        response = client.chat.completions.create(
            model=settings.llm.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert SRE analyzing AWS security and IAM. Provide specific, actionable insights based on actual security data."},
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
                'Review security findings and IAM permissions',
                'Address access denied events if found',
                'Ensure least privilege principle'
            ]
        }
        
    except Exception as e:
        logger.warning("ai_analysis_failed", error=str(e))
        # Return raw findings if AI fails
        return {
            'evidence': raw_findings,
            'recommendations': ['Review security manually', 'Check IAM policies']
        }


class SecurityAgent:
    """Analyzes security events and IAM issues."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def investigate(self, service_name: str, description: str) -> Dict[str, Any]:
        """
        Investigate security and IAM issues.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with evidence and recommendations
        """
        evidence = []
        recommendations = []
        
        try:
            # Check IAM roles and policies
            iam = self.session.client('iam')
            
            try:
                # List roles related to the service
                roles = iam.list_roles()
                for role in roles.get('Roles', []):
                    if service_name.lower() in role['RoleName'].lower():
                        evidence.append(f"Found IAM role: {role['RoleName']}")
                        
                        # Check if role has necessary permissions
                        try:
                            attached_policies = iam.list_attached_role_policies(
                                RoleName=role['RoleName']
                            )
                            policy_count = len(attached_policies.get('AttachedPolicies', []))
                            
                            if policy_count == 0:
                                evidence.append(f"IAM role {role['RoleName']} has no attached policies")
                                recommendations.append(f"Attach necessary policies to IAM role {role['RoleName']}")
                            else:
                                evidence.append(f"IAM role {role['RoleName']} has {policy_count} attached policies")
                                
                        except Exception as e:
                            logger.warning("iam_policy_check_failed", role=role['RoleName'], error=str(e))
                            
            except Exception as e:
                logger.warning("iam_roles_check_failed", error=str(e))
            
            # Check CloudTrail for access denied events
            try:
                cloudtrail = self.session.client('cloudtrail')
                
                # Look for AccessDenied errors in the last hour
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)
                
                events = cloudtrail.lookup_events(
                    LookupAttributes=[
                        {'AttributeKey': 'EventName', 'AttributeValue': 'AccessDenied'}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    MaxResults=10
                )
                
                access_denied_count = len(events.get('Events', []))
                if access_denied_count > 0:
                    evidence.append(f"Found {access_denied_count} AccessDenied events in CloudTrail")
                    recommendations.append("Review IAM permissions for the service")
                    
                    # Get sample events
                    for event in events.get('Events', [])[:3]:
                        event_name = event.get('EventName', 'Unknown')
                        username = event.get('Username', 'Unknown')
                        evidence.append(f"AccessDenied: {event_name} by {username}")
                        
            except Exception as e:
                logger.warning("cloudtrail_check_failed", error=str(e))
                
        except Exception as e:
            logger.error("security_investigation_failed", error=str(e))
            evidence.append(f"Security check encountered error: {str(e)}")
        
        # Ensure we always return something
        if not evidence:
            evidence = ['No security issues detected']
        
        if not recommendations:
            recommendations = ['Continue monitoring security events']
        
        # ALWAYS use AI to enhance analysis, even with minimal findings
        return _use_ai_analysis(evidence, service_name, description)
