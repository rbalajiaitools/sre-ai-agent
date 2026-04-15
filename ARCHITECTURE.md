# CloudScore Astra AI - Architecture & Multi-Agent System

## Overview

CloudScore Astra AI is an intelligent SRE assistant that uses multiple specialized AI agents to investigate incidents, analyze infrastructure, and provide actionable insights. The system integrates with ServiceNow for incident management and AWS for infrastructure monitoring.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  - Chat Interface                                                │
│  - Incident Management                                           │
│  - Topology Visualization                                        │
│  - Dashboard & Simulation                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Multi-Agent Orchestration                   │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │  Logs    │  │ Metrics  │  │  Infra   │  │Security │ │   │
│  │  │  Agent   │  │  Agent   │  │  Agent   │  │ Agent   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │   │
│  │                                                           │   │
│  │  ┌──────────┐                                            │   │
│  │  │  Code    │                                            │   │
│  │  │  Agent   │                                            │   │
│  │  └──────────┘                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Adapters Layer                         │   │
│  │  - ServiceNow Connector                                  │   │
│  │  - AWS Adapter (CloudWatch, CloudTrail, Cost Explorer)  │   │
│  │  - Azure/GCP Adapters (Future)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Database (SQLite)                      │   │
│  │  - Tenants, Integrations, Incidents                     │   │
│  │  - Investigations, Chat Threads, Messages               │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                     │
                     │ External APIs
┌────────────────────▼────────────────────────────────────────────┐
│                    External Services                             │
│  - ServiceNow (Incident Management)                             │
│  - AWS CloudWatch (Logs & Metrics)                              │
│  - AWS CloudTrail (Change Tracking)                             │
│  - Azure OpenAI (GPT-4o for AI Analysis)                        │
└─────────────────────────────────────────────────────────────────┘
```

## How Chat Works

### 1. User Asks a Question

When a user sends a message in the chat:

```
User: "Show me all running AWS services in my account"
```

**Frontend Flow:**
1. User types message in `ChatWindow.tsx`
2. Message sent to `/api/v1/chat/threads/{thread_id}/messages` (POST)
3. Frontend displays user message immediately

**Backend Flow:**
1. Backend receives message in `real.py::send_chat_message()`
2. Message stored in database (`ChatMessage` table)
3. System determines if this requires:
   - Simple query (AWS account info)
   - Incident investigation
   - Multi-agent analysis

### 2. Simple Query Processing

For questions about AWS account:

```python
# Backend: app/api/real.py

async def send_chat_message(thread_id: str, message: str, tenant_id: str):
    # 1. Store user message
    await crud.create_chat_message(db, thread_id, "user", message)
    
    # 2. Determine intent
    if "aws" in message.lower() and "services" in message.lower():
        # Query AWS using adapter
        aws_adapter = get_aws_adapter(tenant_id)
        services = await aws_adapter.list_running_services()
        
        # 3. Format response
        response = format_service_list(services)
        
        # 4. Store AI response
        await crud.create_chat_message(db, thread_id, "assistant", response)
        
        return {"message": response}
```

**AWS Adapter Flow:**
```python
# app/adapters/providers/aws/adapter.py

class AWSAdapter:
    async def list_running_services(self):
        # 1. Get AWS credentials from database
        credentials = await self.get_credentials()
        
        # 2. Query EC2 instances
        ec2_client = boto3.client('ec2', **credentials)
        instances = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        # 3. Query RDS databases
        rds_client = boto3.client('rds', **credentials)
        databases = rds_client.describe_db_instances()
        
        # 4. Query Lambda functions
        lambda_client = boto3.client('lambda', **credentials)
        functions = lambda_client.list_functions()
        
        # 5. Aggregate and return
        return {
            'ec2_instances': instances,
            'rds_databases': databases,
            'lambda_functions': functions
        }
```

### 3. Incident Investigation Flow

When user asks to investigate an incident:

```
User: "Investigate incident INC0012345"
```

**Multi-Agent Orchestration:**

```python
# Backend: app/orchestration/orchestrator.py

class InvestigationOrchestrator:
    async def investigate_incident(self, incident_number: str):
        # 1. Get incident details from ServiceNow
        incident = await servicenow_connector.get_incident(incident_number)
        
        # 2. Select relevant agents based on incident type
        agents = self.select_agents(incident)
        # Returns: [LogsAgent, MetricsAgent, InfraAgent, SecurityAgent, CodeAgent]
        
        # 3. Run agents in parallel
        results = await asyncio.gather(*[
            agent.analyze(incident) for agent in agents
        ])
        
        # 4. Synthesize findings
        rca = await self.synthesize_rca(results)
        
        # 5. Generate resolution steps
        resolution = await self.generate_resolution(rca)
        
        return {
            'agent_results': results,
            'root_cause': rca,
            'resolution_steps': resolution
        }
```

## Multi-Agent System Deep Dive

### Agent Architecture

Each agent is specialized for a specific domain:

#### 1. Logs Agent
**Purpose:** Analyze CloudWatch logs for errors, patterns, and anomalies

```python
# app/agents/specialists/logs_agent.py

class LogsAgent(BaseAgent):
    async def analyze(self, incident: Incident):
        # 1. Determine time range from incident
        time_range = self.get_time_range(incident.opened_at)
        
        # 2. Identify relevant log groups
        service = incident.cmdb_ci  # e.g., "payment-service"
        log_groups = await self.find_log_groups(service)
        
        # 3. Query CloudWatch Logs
        logs = await cloudwatch.query_logs(
            log_groups=log_groups,
            start_time=time_range.start,
            end_time=time_range.end,
            filter_pattern='ERROR OR Exception OR "status code 5"'
        )
        
        # 4. Analyze patterns
        findings = {
            'error_count': len(logs),
            'error_types': self.categorize_errors(logs),
            'error_spike_time': self.detect_spike(logs),
            'stack_traces': self.extract_stack_traces(logs),
            'common_patterns': self.find_patterns(logs)
        }
        
        # 5. Use LLM to summarize
        summary = await self.llm_summarize(findings)
        
        return {
            'agent': 'logs',
            'status': 'success',
            'findings': findings,
            'summary': summary,
            'confidence': 0.85
        }
```

**Example Output:**
```json
{
  "agent": "logs",
  "status": "success",
  "findings": {
    "error_count": 1862,
    "error_types": {
      "NullPointerException": 1200,
      "OutOfMemoryError": 450,
      "ConnectionTimeout": 212
    },
    "error_spike_time": "2024-04-15T10:17:59Z",
    "stack_traces": ["..."],
    "common_patterns": [
      "Memory leak in payment processing",
      "Database connection pool exhausted"
    ]
  },
  "summary": "Found 1,862 error logs in payment-service. Memory leak pattern detected starting at 10:17:59. Error rate increased from 0.1% to 61.2%.",
  "confidence": 0.85
}
```

#### 2. Metrics Agent
**Purpose:** Analyze CloudWatch metrics for performance issues

```python
# app/agents/specialists/metrics_agent.py

class MetricsAgent(BaseAgent):
    async def analyze(self, incident: Incident):
        # 1. Get relevant metrics
        service = incident.cmdb_ci
        metrics = await cloudwatch.get_metrics(
            namespace='AWS/EC2',
            dimensions={'Service': service},
            metric_names=['CPUUtilization', 'MemoryUtilization', 'NetworkIn', 'NetworkOut'],
            start_time=time_range.start,
            end_time=time_range.end
        )
        
        # 2. Detect anomalies
        anomalies = self.detect_anomalies(metrics)
        
        # 3. Correlate with incident time
        correlations = self.correlate_with_incident(metrics, incident.opened_at)
        
        # 4. Calculate trends
        trends = self.calculate_trends(metrics)
        
        return {
            'agent': 'metrics',
            'status': 'success',
            'findings': {
                'cpu_spike': anomalies.get('cpu'),
                'memory_growth': anomalies.get('memory'),
                'latency_increase': correlations.get('latency'),
                'trends': trends
            },
            'summary': await self.llm_summarize(anomalies, correlations, trends)
        }
```

**Example Output:**
```json
{
  "agent": "metrics",
  "status": "success",
  "findings": {
    "cpu_spike": {
      "time": "2024-04-15T10:17:59Z",
      "value": 95.2,
      "baseline": 45.0,
      "increase_percent": 112
    },
    "memory_growth": {
      "start": "2GB",
      "peak": "8GB",
      "growth_rate": "400%"
    },
    "latency_increase": {
      "baseline_ms": 50,
      "peak_ms": 250,
      "increase_percent": 400
    }
  },
  "summary": "CPU usage spiked to 95% at 10:17:59. Memory usage grew from 2GB to 8GB. Request latency increased 400%."
}
```

#### 3. Infrastructure Agent
**Purpose:** Check AWS resource configurations and changes

```python
# app/agents/specialists/infra_agent.py

class InfraAgent(BaseAgent):
    async def analyze(self, incident: Incident):
        # 1. Get resource configuration
        service = incident.cmdb_ci
        resources = await aws_adapter.get_service_resources(service)
        
        # 2. Check recent changes via CloudTrail
        changes = await cloudtrail.get_recent_changes(
            resource_name=service,
            start_time=time_range.start
        )
        
        # 3. Check resource health
        health = await self.check_resource_health(resources)
        
        # 4. Check scaling configuration
        scaling = await self.check_auto_scaling(resources)
        
        return {
            'agent': 'infrastructure',
            'status': 'success',
            'findings': {
                'recent_changes': changes,
                'resource_health': health,
                'scaling_config': scaling,
                'capacity_issues': self.detect_capacity_issues(resources)
            }
        }
```

#### 4. Security Agent
**Purpose:** Check for security issues and access patterns

```python
# app/agents/specialists/security_agent.py

class SecurityAgent(BaseAgent):
    async def analyze(self, incident: Incident):
        # 1. Check IAM access patterns
        access_logs = await cloudtrail.get_access_logs(
            service=incident.cmdb_ci,
            start_time=time_range.start
        )
        
        # 2. Check security groups
        security_groups = await ec2.describe_security_groups(
            filters={'service': incident.cmdb_ci}
        )
        
        # 3. Check for suspicious activity
        suspicious = self.detect_suspicious_activity(access_logs)
        
        # 4. Check compliance
        compliance = await self.check_compliance(security_groups)
        
        return {
            'agent': 'security',
            'status': 'success',
            'findings': {
                'suspicious_activity': suspicious,
                'security_group_changes': self.detect_sg_changes(security_groups),
                'compliance_issues': compliance
            }
        }
```

#### 5. Code Agent
**Purpose:** Analyze code changes and deployments

```python
# app/agents/specialists/code_agent.py

class CodeAgent(BaseAgent):
    async def analyze(self, incident: Incident):
        # 1. Get recent deployments
        deployments = await self.get_recent_deployments(
            service=incident.cmdb_ci,
            start_time=time_range.start
        )
        
        # 2. Check code changes
        if deployments:
            code_changes = await self.get_code_changes(deployments)
            
            # 3. Analyze changes for potential issues
            issues = await self.analyze_code_changes(code_changes)
            
            return {
                'agent': 'code',
                'status': 'success',
                'findings': {
                    'recent_deployments': deployments,
                    'code_changes': code_changes,
                    'potential_issues': issues
                }
            }
```

### RCA Synthesis

After all agents complete, the orchestrator synthesizes findings:

```python
async def synthesize_rca(self, agent_results):
    # 1. Combine all findings
    all_findings = {
        'logs': agent_results[0],
        'metrics': agent_results[1],
        'infrastructure': agent_results[2],
        'security': agent_results[3],
        'code': agent_results[4]
    }
    
    # 2. Use LLM to generate RCA
    prompt = f"""
    Analyze these findings from multiple agents and provide a root cause analysis:
    
    Logs: {all_findings['logs']['summary']}
    Metrics: {all_findings['metrics']['summary']}
    Infrastructure: {all_findings['infrastructure']['summary']}
    Security: {all_findings['security']['summary']}
    Code: {all_findings['code']['summary']}
    
    Provide:
    1. Root Cause
    2. Contributing Factors
    3. Timeline of Events
    4. Impact Assessment
    """
    
    rca = await azure_openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return rca.choices[0].message.content
```

### Resolution Generation

```python
async def generate_resolution(self, rca):
    prompt = f"""
    Based on this root cause analysis:
    {rca}
    
    Provide:
    1. Immediate Actions (to stop the bleeding)
    2. Short-term Fixes (to resolve the issue)
    3. Long-term Improvements (to prevent recurrence)
    4. Monitoring Recommendations
    """
    
    resolution = await azure_openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return resolution.choices[0].message.content
```

## Data Flow Example

### Complete Investigation Flow

```
1. User clicks "Investigate" on incident INC0012345
   ↓
2. Frontend sends POST /api/v1/investigations/start
   {
     "tenant_id": "tenant-001",
     "incident_number": "INC0012345"
   }
   ↓
3. Backend creates investigation record in database
   ↓
4. Backend starts multi-agent orchestration
   ↓
5. Logs Agent queries CloudWatch Logs
   - Finds 1,862 errors
   - Detects memory leak pattern
   ↓
6. Metrics Agent queries CloudWatch Metrics
   - CPU spike to 95%
   - Memory growth 2GB → 8GB
   ↓
7. Infrastructure Agent checks AWS resources
   - No recent changes
   - Auto-scaling not triggered
   ↓
8. Security Agent checks access logs
   - No suspicious activity
   ↓
9. Code Agent checks deployments
   - New deployment 30 minutes before incident
   - Code change in payment processing
   ↓
10. Orchestrator synthesizes RCA using GPT-4o
    Root Cause: Memory leak in payment processing code
    introduced in recent deployment
    ↓
11. Orchestrator generates resolution steps
    1. Rollback deployment
    2. Restart service
    3. Fix memory leak in code
    4. Add memory monitoring
    ↓
12. Backend stores results in database
    ↓
13. Frontend displays results in chat
    - Agent execution progress
    - Findings from each agent
    - Root cause analysis
    - Resolution steps
```

## Current Implementation Status

### ✅ Implemented
- ServiceNow integration (fetch incidents)
- AWS adapter (basic resource listing)
- Database models (Incidents, Investigations, ChatThreads)
- Chat UI with message rendering
- Simplified AI investigation using Azure OpenAI

### 🚧 Partially Implemented
- Multi-agent orchestration (code exists in `app/orchestration/` but has pydantic v1/v2 conflicts)
- CloudWatch logs/metrics querying
- CloudTrail change tracking

### ❌ Not Yet Implemented
- Full agent execution with real AWS data
- Automatic resolution execution
- Feedback loop for agent improvement

## How to Enable Full Multi-Agent System

The full orchestration system exists but requires fixing pydantic dependency conflicts:

```bash
# Current issue: langchain/langgraph use pydantic v1, FastAPI uses pydantic v2

# To enable:
1. Resolve pydantic version conflicts
2. Update app/main.py to include orchestration router
3. Frontend already supports agent execution display
```

## Configuration

All integrations are configured via Settings page:

1. **ServiceNow**: Instance URL, username, password
2. **AWS**: Access key, secret key, region
3. **Azure OpenAI**: Endpoint, API key, deployment name

Credentials are encrypted in database using Fernet encryption.
