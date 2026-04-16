"""Logs specialist agent for parallel execution - optimized for speed."""

from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from boto3 import Session
import structlog

logger = structlog.get_logger(__name__)


def _use_ai_analysis(raw_findings: list, service_name: str) -> Dict[str, Any]:
    """
    Use AI to analyze raw log findings and provide detailed insights.
    
    Args:
        raw_findings: List of raw evidence strings from AWS
        service_name: Name of the service being investigated
        
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
        
        prompt = f"""Analyze these CloudWatch log findings for service '{service_name}':

{findings_text}

Provide a concise analysis. Use plain text only, NO markdown formatting.

LOG STATUS: [One line summary]

KEY FINDINGS:
• [Finding 1]
• [Finding 2]
• [Finding 3]

RECOMMENDATIONS:
• [Action 1]
• [Action 2]

Be specific. Use plain text only."""
        
        response = client.chat.completions.create(
            model=settings.llm.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert SRE analyzing CloudWatch logs. Provide specific, actionable insights."},
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
                'Review log patterns identified',
                'Check for similar issues in other services'
            ]
        }
        
    except Exception as e:
        logger.warning("ai_analysis_failed", error=str(e))
        return {
            'evidence': raw_findings,
            'recommendations': ['Review logs manually', 'Set up log monitoring alerts']
        }


class LogsAgent:
    """Analyzes CloudWatch logs for errors and patterns - optimized for speed."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def investigate(self, service_name: str, description: str) -> Dict[str, Any]:
        """
        Investigate logs quickly - optimized to complete within 30 seconds.
        
        Args:
            service_name: Name of the service to investigate
            description: Description of the issue
            
        Returns:
            Investigation results with evidence and recommendations
        """
        evidence = []
        recommendations = []
        
        try:
            logs = self.session.client('logs')
            lambda_client = self.session.client('lambda')
            
            # Find Lambda functions
            lambda_log_groups = []
            try:
                functions = lambda_client.list_functions()
                for func in functions.get('Functions', [])[:5]:  # Limit to 5 functions
                    func_name = func['FunctionName']
                    if (service_name.lower() in func_name.lower() or 
                        'payment' in func_name.lower() or
                        'processor' in func_name.lower()):
                        log_group_name = f"/aws/lambda/{func_name}"
                        lambda_log_groups.append(log_group_name)
                        evidence.append(f"Found Lambda: {func_name}")
            except Exception as e:
                logger.warning("lambda_list_failed", error=str(e))
            
            # Get log groups - prioritize Lambda log groups we found
            matching_groups = []
            try:
                all_log_groups = logs.describe_log_groups(limit=50)
                
                # First, add Lambda log groups we explicitly found
                for log_group in all_log_groups.get('logGroups', []):
                    log_group_name = log_group['logGroupName']
                    
                    if log_group_name in lambda_log_groups:
                        matching_groups.append({
                            'name': log_group_name,
                            'last_event_time': log_group.get('lastEventTimestamp', 0),
                            'stored_bytes': log_group.get('storedBytes', 0)
                        })
                
                # If we didn't find the Lambda log groups, add any log groups with data
                if not matching_groups:
                    for log_group in all_log_groups.get('logGroups', []):
                        log_group_name = log_group['logGroupName']
                        stored_bytes = log_group.get('storedBytes', 0)
                        
                        if stored_bytes > 0:
                            matching_groups.append({
                                'name': log_group_name,
                                'last_event_time': log_group.get('lastEventTimestamp', 0),
                                'stored_bytes': stored_bytes
                            })
                
                # Sort by stored bytes (most data first) and limit to 3
                matching_groups.sort(key=lambda x: x['stored_bytes'], reverse=True)
                matching_groups = matching_groups[:3]
                
                if matching_groups:
                    evidence.append(f"Analyzing {len(matching_groups)} log group(s)")
                else:
                    evidence.append("No log groups found with data")
                    
            except Exception as e:
                logger.warning("log_groups_list_failed", error=str(e))
                evidence.append(f"Error listing log groups: {str(e)}")
            
            # Quick analysis of log groups - ALWAYS try to read logs regardless of timestamp
            for log_group_info in matching_groups:
                log_group_name = log_group_info['name']
                stored_bytes = log_group_info['stored_bytes']
                last_event_time = log_group_info['last_event_time']
                
                # Show log group info
                evidence.append(f"Log group: {log_group_name}")
                if last_event_time > 0:
                    last_event = datetime.fromtimestamp(last_event_time / 1000, tz=timezone.utc)
                    evidence.append(f"  Size: {stored_bytes / 1024 / 1024:.2f} MB, Last event: {last_event.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                else:
                    evidence.append(f"  Size: {stored_bytes / 1024 / 1024:.2f} MB")
                
                # ALWAYS try to read log streams, regardless of timestamp
                try:
                    # Get the most recent stream
                    log_streams = logs.describe_log_streams(
                        logGroupName=log_group_name,
                        orderBy='LastEventTime',
                        descending=True,
                        limit=1
                    )
                    
                    streams = log_streams.get('logStreams', [])
                    if streams:
                        stream = streams[0]
                        stream_name = stream['logStreamName']
                        stream_last_event = stream.get('lastEventTimestamp', 0)
                        
                        if stream_last_event > 0:
                            stream_time = datetime.fromtimestamp(stream_last_event / 1000, tz=timezone.utc)
                            evidence.append(f"  Stream: {stream_name} (Last: {stream_time.strftime('%Y-%m-%d %H:%M:%S')})")
                        else:
                            evidence.append(f"  Stream: {stream_name}")
                        
                        # Get the most recent 20 events from this stream
                        log_events = logs.get_log_events(
                            logGroupName=log_group_name,
                            logStreamName=stream_name,
                            limit=20,
                            startFromHead=False  # Get most recent
                        )
                        
                        events = log_events.get('events', [])
                        if events:
                            evidence.append(f"  Retrieved {len(events)} log events")
                            
                            # Quick count of errors
                            error_count = sum(1 for e in events if any(k in e.get('message', '').upper() for k in ['ERROR', 'FAILED', 'FAILURE']))
                            exception_count = sum(1 for e in events if 'Exception' in e.get('message', ''))
                            warn_count = sum(1 for e in events if 'WARN' in e.get('message', '').upper())
                            
                            if error_count > 0:
                                evidence.append(f"  ⚠️ Found {error_count} ERROR entries")
                                # Show first error with full message
                                for event in events:
                                    msg = event.get('message', '')
                                    if any(k in msg.upper() for k in ['ERROR', 'FAILED', 'FAILURE']):
                                        ts = datetime.fromtimestamp(event.get('timestamp', 0) / 1000, tz=timezone.utc)
                                        evidence.append(f"    [{ts.strftime('%Y-%m-%d %H:%M:%S')}] {msg[:200]}")
                                        break
                            
                            if exception_count > 0:
                                evidence.append(f"  ⚠️ Found {exception_count} Exception entries")
                                # Show first exception
                                for event in events:
                                    msg = event.get('message', '')
                                    if 'Exception' in msg:
                                        ts = datetime.fromtimestamp(event.get('timestamp', 0) / 1000, tz=timezone.utc)
                                        evidence.append(f"    [{ts.strftime('%Y-%m-%d %H:%M:%S')}] {msg[:200]}")
                                        break
                            
                            if warn_count > 0:
                                evidence.append(f"  Found {warn_count} WARNING entries")
                            
                            if error_count == 0 and exception_count == 0:
                                evidence.append(f"  ✓ No errors in {len(events)} log events")
                                # Show 2 sample logs
                                for i, event in enumerate(events[:2]):
                                    ts = datetime.fromtimestamp(event.get('timestamp', 0) / 1000, tz=timezone.utc)
                                    msg = event.get('message', '')
                                    evidence.append(f"    Sample {i+1}: [{ts.strftime('%Y-%m-%d %H:%M:%S')}] {msg[:120]}")
                        else:
                            evidence.append(f"  No log events found in stream")
                    else:
                        evidence.append(f"  No log streams found in this log group")
                        
                except Exception as e:
                    logger.warning("log_query_failed", log_group=log_group_name, error=str(e))
                    evidence.append(f"  Error querying logs: {str(e)}")
                    
        except Exception as e:
            logger.error("logs_investigation_failed", error=str(e))
            evidence.append(f"Logs analysis error: {str(e)}")
        
        # Ensure we always return something
        if not evidence:
            evidence = ['No log groups found']
        
        if not recommendations:
            recommendations = ['Set up log monitoring', 'Review log retention']
        
        # ALWAYS use AI analysis
        return _use_ai_analysis(evidence, service_name)
