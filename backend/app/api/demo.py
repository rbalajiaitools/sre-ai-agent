"""Demo API endpoints for testing without external dependencies."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(tags=["demo"])

# In-memory storage
demo_users = {
    "demo@example.com": {
        "id": "user-001",
        "email": "demo@example.com",
        "name": "Demo User",
        "role": "admin",
        "tenant_id": "tenant-001",
    }
}

demo_incidents = [
    {
        "sys_id": "inc-001",
        "number": "INC0001234",
        "short_description": "Payment service experiencing high latency",
        "description": "Users reporting slow payment processing. Average response time increased from 200ms to 5000ms.",
        "priority": 1,
        "state": "2",
        "opened_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        "updated_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "assigned_to": "John Doe",
        "assignment_group": "Platform Team",
        "cmdb_ci": "payment-service",
        "work_notes": "Investigating database connection pool exhaustion",
        "investigation_status": "investigating",
        "investigation_id": "inv-001",
    },
    {
        "sys_id": "inc-002",
        "number": "INC0001235",
        "short_description": "API Gateway returning 502 errors",
        "description": "Multiple 502 Bad Gateway errors reported by monitoring system.",
        "priority": 1,
        "state": "1",
        "opened_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "updated_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "assigned_to": "Jane Smith",
        "assignment_group": "Infrastructure Team",
        "cmdb_ci": "api-gateway",
        "work_notes": "",
        "investigation_status": None,
        "investigation_id": None,
    },
    {
        "sys_id": "inc-003",
        "number": "INC0001236",
        "short_description": "Database backup failed",
        "description": "Nightly database backup job failed with timeout error.",
        "priority": 2,
        "state": "2",
        "opened_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "updated_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        "assigned_to": "Bob Johnson",
        "assignment_group": "Database Team",
        "cmdb_ci": "postgres-primary",
        "work_notes": "Checking disk space and backup retention policy",
        "investigation_status": None,
        "investigation_id": None,
    },
]

demo_investigations = {}
demo_chat_threads = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict
    tenant: dict


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Demo login endpoint."""
    user = demo_users.get(request.email)
    
    if not user or request.password != "demo123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return LoginResponse(
        token="demo-token-12345",
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
        tenant={
            "id": user["tenant_id"],
            "name": "Demo Company",
        }
    )


@router.get("/incidents")
async def get_incidents(tenant_id: str = Query(...)):
    """Get incidents for tenant."""
    return demo_incidents


@router.get("/incidents/{incident_number}")
async def get_incident(incident_number: str, tenant_id: str = Query(...)):
    """Get single incident."""
    incident = next((i for i in demo_incidents if i["number"] == incident_number), None)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


class RefreshIncidentsRequest(BaseModel):
    tenant_id: str


@router.post("/incidents/refresh")
async def refresh_incidents(request: RefreshIncidentsRequest):
    """Refresh incidents from ServiceNow."""
    return {"message": "Incidents refreshed", "count": len(demo_incidents)}


@router.post("/incidents/{incident_number}/investigate")
async def start_investigation_legacy(incident_number: str, tenant_id: str = Query(...)):
    """Start investigation for incident (legacy endpoint)."""
    return await start_investigation_impl(incident_number)


class StartInvestigationRequest(BaseModel):
    tenant_id: str
    incident_number: str


@router.post("/investigations/start")
async def start_investigation(request: StartInvestigationRequest):
    """Start investigation for incident."""
    return await start_investigation_impl(request.incident_number)


async def start_investigation_impl(incident_number: str):
    """Implementation of start investigation."""
    incident = next((i for i in demo_incidents if i["number"] == incident_number), None)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    investigation_id = f"inv-{incident_number}"
    chat_thread_id = f"thread-{incident_number}"
    
    # Update incident
    incident["investigation_status"] = "started"
    incident["investigation_id"] = investigation_id
    
    # Create investigation
    demo_investigations[investigation_id] = {
        "id": investigation_id,
        "incident_number": incident_number,
        "status": "started",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    
    # Create chat thread
    demo_chat_threads[chat_thread_id] = {
        "id": chat_thread_id,
        "title": f"Investigation: {incident['short_description']}",
        "created_at": datetime.now().isoformat(),
        "last_message_at": datetime.now().isoformat(),
        "investigation_id": investigation_id,
        "incident_number": incident_number,
    }
    
    return {
        "investigation_id": investigation_id,
        "chat_thread_id": chat_thread_id,
        "status": "started",
    }


@router.get("/investigations")
async def get_investigations(tenant_id: str = Query(...)):
    """Get all investigations."""
    return list(demo_investigations.values())


@router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str):
    """Get investigation details."""
    investigation = demo_investigations.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Add full details
    return {
        **investigation,
        "agent_results": [
            {
                "agent_name": "Logs Agent",
                "status": "completed",
                "findings": "Found connection pool exhaustion errors in application logs",
                "evidence_count": 15,
                "duration_seconds": 45,
            },
            {
                "agent_name": "Metrics Agent",
                "status": "completed",
                "findings": "Database connection count reached maximum limit of 100",
                "evidence_count": 8,
                "duration_seconds": 30,
            },
        ],
        "rca_output": {
            "root_cause": "Database connection pool exhausted due to connection leak in payment processing code",
            "confidence": 0.92,
            "timeline": [
                {
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "event": "Connection pool utilization started increasing",
                    "source": "Metrics",
                },
            ],
            "affected_resources": [
                {"name": "payment-service", "type": "service", "provider": "AWS", "status": "degraded"},
            ],
            "contributing_factors": [
                "Missing connection.close() in error handling path",
            ],
        },
        "resolution_output": {
            "recommended_fix": "Add proper connection cleanup in error handlers",
            "fix_steps": [
                "Deploy hotfix with connection cleanup",
                "Restart payment service pods",
            ],
            "commands": [
                "kubectl rollout restart deployment/payment-service",
            ],
            "estimated_impact": "Low - rolling restart with zero downtime",
            "requires_human_approval": True,
            "approved": False,
        },
    }


@router.get("/chat/threads")
async def get_chat_threads(tenant_id: str = Query(...)):
    """Get chat threads."""
    return list(demo_chat_threads.values())


@router.post("/chat/threads")
async def create_chat_thread(tenant_id: str = Query(...)):
    """Create new chat thread."""
    thread_id = f"thread-{len(demo_chat_threads) + 1}"
    thread = {
        "id": thread_id,
        "title": "New conversation",
        "created_at": datetime.now().isoformat(),
        "last_message_at": datetime.now().isoformat(),
    }
    demo_chat_threads[thread_id] = thread
    return thread


@router.get("/chat/threads/{thread_id}/messages")
async def get_chat_messages(thread_id: str):
    """Get messages for thread."""
    # Get thread info if it exists
    thread = demo_chat_threads.get(thread_id)
    
    # If thread doesn't exist, return empty messages
    if not thread:
        return []
    
    # Get investigation info from thread
    investigation_id = thread.get("investigation_id")
    incident_number = thread.get("incident_number")
    
    # Return investigation-related messages
    if investigation_id and incident_number:
        incident = next((i for i in demo_incidents if i["number"] == incident_number), None)
        incident_description = incident["short_description"] if incident else "the incident"
        
        return [
            {
                "id": f"msg-{thread_id}-001",
                "thread_id": thread_id,
                "role": "user",
                "content": f"What is causing {incident_description}?",
                "message_type": "text",
                "metadata": {},
                "created_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
            },
            {
                "id": f"msg-{thread_id}-002",
                "thread_id": thread_id,
                "role": "assistant",
                "content": f"I am investigating {incident_description}. Let me analyze the logs, metrics, and recent changes...",
                "message_type": "investigation_start",
                "metadata": {
                    "investigation_id": investigation_id,
                    "incident_number": incident_number,
                },
                "created_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
            },
            {
                "id": f"msg-{thread_id}-003",
                "thread_id": thread_id,
                "role": "assistant",
                "content": "Investigation complete",
                "message_type": "rca_result",
                "metadata": {
                    "investigation_id": investigation_id,
                    "incident_number": incident_number,
                    "root_cause": "Database connection pool exhausted due to connection leak in payment processing code",
                    "confidence": 0.92,
                    "timeline": [
                        {
                            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                            "event": "Connection pool utilization started increasing",
                            "source": "Metrics",
                        },
                        {
                            "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
                            "event": "First connection timeout errors logged",
                            "source": "Logs",
                        },
                        {
                            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                            "event": "Service latency exceeded SLA threshold",
                            "source": "Monitoring",
                        },
                    ],
                    "affected_resources": [
                        {"name": "payment-service", "type": "service", "provider": "AWS", "status": "degraded"},
                        {"name": "postgres-primary", "type": "database", "provider": "AWS", "status": "healthy"},
                    ],
                    "contributing_factors": [
                        "Missing connection.close() in error handling path",
                        "Connection pool size not configured for peak load",
                        "No connection leak detection enabled",
                    ],
                    "evidence": [
                        {
                            "description": "Found 15 connection timeout errors in application logs",
                            "source_agent": "Logs Agent",
                            "provider": "CloudWatch",
                        },
                        {
                            "description": "Database connection count reached maximum limit of 100",
                            "source_agent": "Metrics Agent",
                            "provider": "CloudWatch",
                        },
                    ],
                },
                "created_at": (datetime.now() - timedelta(minutes=2)).isoformat(),
            },
        ]
    
    # Return generic messages for non-investigation threads
    return [
        {
            "id": f"msg-{thread_id}-001",
            "thread_id": thread_id,
            "role": "user",
            "content": "Hello, I need help with an issue.",
            "message_type": "text",
            "metadata": {},
            "created_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
        },
        {
            "id": f"msg-{thread_id}-002",
            "thread_id": thread_id,
            "role": "assistant",
            "content": "Hello! I'm here to help. What issue are you experiencing?",
            "message_type": "text",
            "metadata": {},
            "created_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
        },
    ]


@router.get("/topology/services")
async def get_services(tenant_id: str = Query(...)):
    """Get services."""
    return [
        {
            "id": "svc-001",
            "name": "payment-service",
            "type": "service",
            "provider": "aws",
            "region": "us-east-1",
            "status": "degraded",
            "dependencies": ["postgres-primary", "redis-cache"],
        },
        {
            "id": "svc-002",
            "name": "api-gateway",
            "type": "service",
            "provider": "aws",
            "region": "us-east-1",
            "status": "down",
            "dependencies": ["payment-service", "auth-service"],
        },
    ]


@router.get("/dashboard/stats")
async def get_dashboard_stats(tenant_id: str = Query(...)):
    """Get dashboard stats."""
    return {
        "open_incidents": 12,
        "p1_open": 2,
        "p2_open": 5,
        "resolved_today": 8,
        "avg_mttr_hours": 2.5,
        "investigations_today": 3,
        "auto_resolved": 1,
    }
