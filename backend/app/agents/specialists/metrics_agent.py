"""Metrics specialist agent for parallel execution."""

from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from boto3 import Session
import structlog

logger = structlog.get_logger(__name__)


def _use_ai_analysis(raw_findings: list, service_name: str, description: str) -> Dict[str, Any]:
    """
    Use AI to analyze raw metrics findings and provide detailed insights.
    
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
        
        prompt = f"""Analyze these CloudWatch metrics for service '{service_name}' with issue: {description}

{findings_text}

Provide a concise, structured analysis. Use plain text only, NO markdown formatting (no **, no ##, no ###).

PERFORMANCE STATUS: [One line summary]

METRICS SUMMARY:
• Invocations: [count and trend]
• Error Rate: [percentage and assessment]
• Duration: [avg/max and assessment]
• Throttles: [count if any]

ANOMALIES DETECTED:
• [Anomaly 1 if any]
• [Anomaly 2 if any]

CAPACITY ASSESSMENT:
• [Assessment of resource capacity]

OPTIMIZATION ACTIONS:
• [Action 1]
• [Action 2]
• [Action 3]

Keep it concise. Use bullet points with •. Reference actual metric values. Use plain text only."""
        
        response = client.chat.completions.create(
            model=settings.llm.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert SRE analyzing CloudWatch metrics. Provide specific, actionable insights based on actual performance data."},
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
                'Review performance assessment and anomalies',
                'Address capacity concerns identified',
                'Implement optimization recommendations'
            ]
        }
        
    except Exception as e:
        logger.warning("ai_analysis_failed", error=str(e))
        # Return raw findings if AI fails
        return {
            'evidence': raw_findings,
            'recommendations': ['Review metrics manually', 'Set up CloudWatch alarms']
        }


class MetricsAgent:
    """Analyzes CloudWatch metrics for anomalies."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def investigate(self, service_name: str, description: str) -> Dict[str, Any]:
        """
        Investigate metrics for anomalies with detailed analysis.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with detailed evidence and recommendations
        """
        evidence = []
        recommendations = []
        
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            # Time range: last 24 hours (expanded from 1 hour)
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            evidence.append(f"Analyzing CloudWatch metrics for last 24 hours ({start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} UTC)")
            
            # Check Lambda metrics - find ALL Lambda functions first
            lambda_client = self.session.client('lambda')
            try:
                functions = lambda_client.list_functions()
                # Match by service name or common patterns
                lambda_functions = []
                for f in functions.get('Functions', []):
                    func_name = f['FunctionName']
                    if (service_name.lower() in func_name.lower() or 
                        'payment' in func_name.lower() or
                        'api' in func_name.lower() or
                        'processor' in func_name.lower()):
                        lambda_functions.append(f)
                
                # If no matches, take first 3 functions
                if not lambda_functions:
                    lambda_functions = functions.get('Functions', [])[:3]
                
                for func in lambda_functions[:3]:  # Limit to 3 functions
                    func_name = func['FunctionName']
                    
                    # Get invocations
                    invocations = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Invocations',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Sum']
                    )
                    
                    total_invocations = sum(dp['Sum'] for dp in invocations.get('Datapoints', []))
                    if total_invocations > 0:
                        evidence.append(f"Lambda {func_name}: {int(total_invocations)} invocations in last hour")
                    
                    # Get errors
                    errors = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Errors',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Sum']
                    )
                    
                    total_errors = sum(dp['Sum'] for dp in errors.get('Datapoints', []))
                    if total_errors > 0:
                        error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0
                        evidence.append(f"⚠️ Lambda {func_name}: {int(total_errors)} errors ({error_rate:.1f}% error rate)")
                        recommendations.append(f"Investigate Lambda {func_name} error causes - error rate above threshold")
                    
                    # Get duration
                    duration = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Duration',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average', 'Maximum']
                    )
                    
                    if duration.get('Datapoints'):
                        avg_duration = sum(dp['Average'] for dp in duration['Datapoints']) / len(duration['Datapoints'])
                        max_duration = max(dp['Maximum'] for dp in duration['Datapoints'])
                        evidence.append(f"Lambda {func_name}: Avg duration {avg_duration:.0f}ms, Max {max_duration:.0f}ms")
                        
                        if max_duration > 10000:  # 10 seconds
                            recommendations.append(f"Optimize Lambda {func_name} - duration exceeds 10s")
                    
                    # Get throttles
                    throttles = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Throttles',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Sum']
                    )
                    
                    total_throttles = sum(dp['Sum'] for dp in throttles.get('Datapoints', []))
                    if total_throttles > 0:
                        evidence.append(f"⚠️ Lambda {func_name}: {int(total_throttles)} throttles detected")
                        recommendations.append(f"Increase Lambda {func_name} reserved concurrency")
                    
                    # Get concurrent executions
                    concurrent = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='ConcurrentExecutions',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Maximum']
                    )
                    
                    if concurrent.get('Datapoints'):
                        max_concurrent = max(dp['Maximum'] for dp in concurrent['Datapoints'])
                        evidence.append(f"Lambda {func_name}: Peak concurrent executions: {int(max_concurrent)}")
                        
            except Exception as e:
                logger.warning("lambda_metrics_failed", error=str(e))
                evidence.append(f"Lambda metrics check: {str(e)}")
            
            # Check RDS metrics if database-related
            if 'database' in description.lower() or 'db' in description.lower() or 'rds' in description.lower():
                try:
                    rds = self.session.client('rds')
                    db_instances = rds.describe_db_instances()
                    
                    for db in db_instances.get('DBInstances', [])[:2]:  # Limit to 2 instances
                        db_id = db['DBInstanceIdentifier']
                        
                        # Get CPU
                        cpu = cloudwatch.get_metric_statistics(
                            Namespace='AWS/RDS',
                            MetricName='CPUUtilization',
                            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Average', 'Maximum']
                        )
                        
                        if cpu.get('Datapoints'):
                            avg_cpu = sum(dp['Average'] for dp in cpu['Datapoints']) / len(cpu['Datapoints'])
                            max_cpu = max(dp['Maximum'] for dp in cpu['Datapoints'])
                            evidence.append(f"RDS {db_id}: CPU Avg {avg_cpu:.1f}%, Max {max_cpu:.1f}%")
                            
                            if max_cpu > 80:
                                recommendations.append(f"RDS {db_id} CPU high - consider scaling up")
                        
                        # Get connections
                        connections = cloudwatch.get_metric_statistics(
                            Namespace='AWS/RDS',
                            MetricName='DatabaseConnections',
                            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Average', 'Maximum']
                        )
                        
                        if connections.get('Datapoints'):
                            avg_conn = sum(dp['Average'] for dp in connections['Datapoints']) / len(connections['Datapoints'])
                            max_conn = max(dp['Maximum'] for dp in connections['Datapoints'])
                            evidence.append(f"RDS {db_id}: Connections Avg {avg_conn:.0f}, Max {max_conn:.0f}")
                            
                except Exception as e:
                    logger.warning("rds_metrics_failed", error=str(e))
            
            # Check API Gateway metrics
            try:
                apigateway = self.session.client('apigateway')
                apis = apigateway.get_rest_apis()
                
                for api in apis.get('items', [])[:2]:  # Limit to 2 APIs
                    api_name = api.get('name', '')
                    api_id = api.get('id', '')
                    
                    if service_name.lower() in api_name.lower() or 'payment' in api_name.lower():
                        # Get API Gateway metrics
                        count = cloudwatch.get_metric_statistics(
                            Namespace='AWS/ApiGateway',
                            MetricName='Count',
                            Dimensions=[{'Name': 'ApiName', 'Value': api_name}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Sum']
                        )
                        
                        total_requests = sum(dp['Sum'] for dp in count.get('Datapoints', []))
                        if total_requests > 0:
                            evidence.append(f"API Gateway {api_name}: {int(total_requests)} requests in last hour")
                        
                        # Get 4XX errors
                        errors_4xx = cloudwatch.get_metric_statistics(
                            Namespace='AWS/ApiGateway',
                            MetricName='4XXError',
                            Dimensions=[{'Name': 'ApiName', 'Value': api_name}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Sum']
                        )
                        
                        total_4xx = sum(dp['Sum'] for dp in errors_4xx.get('Datapoints', []))
                        if total_4xx > 0:
                            evidence.append(f"API Gateway {api_name}: {int(total_4xx)} 4XX errors")
                        
                        # Get 5XX errors
                        errors_5xx = cloudwatch.get_metric_statistics(
                            Namespace='AWS/ApiGateway',
                            MetricName='5XXError',
                            Dimensions=[{'Name': 'ApiName', 'Value': api_name}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Sum']
                        )
                        
                        total_5xx = sum(dp['Sum'] for dp in errors_5xx.get('Datapoints', []))
                        if total_5xx > 0:
                            evidence.append(f"⚠️ API Gateway {api_name}: {int(total_5xx)} 5XX errors")
                            recommendations.append(f"Investigate API Gateway {api_name} backend errors")
                        
            except Exception as e:
                logger.warning("apigateway_metrics_failed", error=str(e))
            
            # Summary
            if not any('⚠️' in e for e in evidence):
                evidence.append("✓ No critical metric anomalies detected in monitored resources")
                recommendations.append("Continue monitoring metrics for baseline establishment")
                
        except Exception as e:
            logger.error("metrics_investigation_failed", error=str(e))
            evidence.append(f"Metrics analysis encountered error: {str(e)}")
        
        # Ensure we always return something
        if not evidence:
            evidence = ['Metrics analysis completed - no CloudWatch metrics found']
        
        if not recommendations:
            recommendations = ['Set up CloudWatch alarms for key metrics', 'Establish performance baselines']
        
        # ALWAYS use AI to enhance analysis, even with minimal findings
        return _use_ai_analysis(evidence, service_name, description)
