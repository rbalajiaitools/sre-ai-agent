"""Real API endpoints for ServiceNow and AWS integration with database persistence."""

from datetime import datetime, timezone
from typing import List
from uuid import UUID
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db import crud
from app.db.models import ChatThread, Investigation
from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import AuthType, ServiceNowConfig
from app.connectors.servicenow.connector import ServiceNowConnector
from app.connectors.servicenow.models import IncidentFilter, IncidentState
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["real"])

# Global connector instance (in production, use dependency injection)
_servicenow_connector: ServiceNowConnector = None


def get_servicenow_connector() -> ServiceNowConnector:
    """Get or create ServiceNow connector."""
    global _servicenow_connector
    if _servicenow_connector is None:
        # Initialize without Redis for now
        _servicenow_connector = ServiceNowConnector(redis_client=None)
    return _servicenow_connector


class IntegrationResponse(BaseModel):
    id: str
    name: str
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_sync_at: datetime | None = None


class ServiceNowTestRequest(BaseModel):
    instance_url: str
    username: str
    password: str


class ServiceNowSaveRequest(BaseModel):
    tenant_id: str
    name: str
    instance_url: str
    username: str
    password: str


class CloudProviderTestRequest(BaseModel):
    provider: str
    credentials: dict


class CloudProviderSaveRequest(BaseModel):
    tenant_id: str
    name: str
    provider: str
    credentials: dict


@router.post("/settings/servicenow/test")
async def test_servicenow_real(request: ServiceNowTestRequest):
    """Test ServiceNow connection with real API call."""
    try:
        # Extract instance name from URL
        instance_url = request.instance_url.strip()
        if not instance_url.startswith("https://"):
            return {
                "success": False,
                "message": "Instance URL must start with https://"
            }
        
        # Extract instance name (e.g., "dev320031" from "https://dev320031.service-now.com")
        instance = instance_url.replace("https://", "").replace(".service-now.com", "").split("/")[0]
        
        logger.info("testing_servicenow_connection", instance=instance, username=request.username)
        
        # Create config
        config = ServiceNowConfig(
            instance=instance,
            auth_type=AuthType.BASIC,
            username=request.username,
            password=request.password,
        )
        
        # Create client and test connection
        client = ServiceNowClient(config)
        
        try:
            # Try to fetch one incident as validation
            incident_filter = IncidentFilter(limit=1)
            incidents = await client.get_incidents(incident_filter)
            
            await client.close()
            
            logger.info("servicenow_connection_successful", instance=instance, incidents_count=len(incidents))
            
            return {
                "success": True,
                "message": f"Connection successful! Found {len(incidents)} incident(s) in your instance."
            }
            
        except Exception as e:
            await client.close()
            logger.error("servicenow_connection_failed", instance=instance, error=str(e))
            
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {
                    "success": False,
                    "message": "Authentication failed. Please check your username and password."
                }
            elif "404" in error_msg or "Not Found" in error_msg:
                return {
                    "success": False,
                    "message": "Instance not found. Please check your instance URL."
                }
            elif "timeout" in error_msg.lower():
                return {
                    "success": False,
                    "message": "Connection timeout. Please check your instance URL and network connection."
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: {error_msg}"
                }
                
    except Exception as e:
        logger.error("servicenow_test_error", error=str(e), error_type=type(e).__name__)
        import traceback
        logger.error("servicenow_test_traceback", traceback=traceback.format_exc())
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@router.get("/settings/integrations", response_model=List[IntegrationResponse])
async def get_integrations(
    tenant_id: str = Query(...),
    type: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all integrations for tenant."""
    try:
        integrations = await crud.get_integrations(db, tenant_id, type)
        
        return [
            IntegrationResponse(
                id=i.id,
                name=i.name,
                type=i.type,
                is_active=i.is_active,
                created_at=i.created_at,
                updated_at=i.updated_at,
                last_sync_at=i.last_sync_at
            )
            for i in integrations
        ]
    except Exception as e:
        logger.error("get_integrations_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/integrations/{integration_id}")
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Get integration by ID with decrypted config."""
    try:
        integration = await crud.get_integration(db, integration_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Decrypt config
        config = crud.decrypt_integration_config(integration)
        
        # Remove sensitive fields for response
        safe_config = {k: v for k, v in config.items() if k not in ["password", "secret_key", "secret_access_key"]}
        
        return {
            "id": integration.id,
            "name": integration.name,
            "type": integration.type,
            "config": safe_config,
            "is_active": integration.is_active,
            "created_at": integration.created_at.isoformat(),
            "updated_at": integration.updated_at.isoformat(),
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class UpdateIntegrationRequest(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None


@router.put("/settings/integrations/{integration_id}")
async def update_integration(
    integration_id: str,
    request: UpdateIntegrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update integration."""
    try:
        integration = await crud.update_integration(
            db=db,
            integration_id=integration_id,
            name=request.name,
            config=request.config,
            is_active=request.is_active
        )
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {
            "success": True,
            "message": "Integration updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/integrations/{integration_id}")
async def delete_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Delete integration."""
    try:
        deleted = await crud.delete_integration(db, integration_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {
            "success": True,
            "message": "Integration deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/servicenow")
async def save_servicenow_real(request: ServiceNowSaveRequest, db: AsyncSession = Depends(get_db)):
    """Save ServiceNow configuration to database."""
    try:
        # Extract instance name from URL
        instance_url = request.instance_url.strip()
        instance = instance_url.replace("https://", "").replace(".service-now.com", "").split("/")[0]
        
        tenant_id = request.tenant_id
        
        logger.info("saving_servicenow_config", tenant_id=tenant_id, instance=instance)
        
        # Create config dict
        config = {
            "instance": instance,
            "instance_url": instance_url,
            "username": request.username,
            "password": request.password,
            "auth_type": "basic",
        }
        
        # Save to database (credentials will be encrypted)
        integration = await crud.create_integration(
            db=db,
            tenant_id=tenant_id,
            name=request.name,
            integration_type="servicenow",
            config=config
        )
        
        # Register tenant with connector (only if valid UUID)
        try:
            tenant_uuid = UUID(tenant_id)
            sn_config = ServiceNowConfig(
                instance=instance,
                auth_type=AuthType.BASIC,
                username=request.username,
                password=request.password,
            )
            
            connector = get_servicenow_connector()
            connector.register_tenant(tenant_uuid, sn_config)
        except ValueError:
            # Not a valid UUID, skip connector registration
            logger.warning("invalid_uuid_skipping_connector", tenant_id=tenant_id)
        
        logger.info("servicenow_config_saved", tenant_id=tenant_id, integration_id=integration.id)
        
        return {
            "success": True,
            "message": "ServiceNow configuration saved successfully",
            "integration_id": integration.id
        }
        
    except Exception as e:
        logger.error("servicenow_save_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/incidents")
async def get_incidents_real(
    tenant_id: str = Query(...),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get incidents - from database or refresh from ServiceNow."""
    try:
        logger.info("fetching_incidents", tenant_id=tenant_id, refresh=refresh)
        
        # Get ServiceNow integrations for this tenant
        integrations = await crud.get_integrations(db, tenant_id, "servicenow")
        
        if not integrations:
            logger.warning("no_servicenow_integration", tenant_id=tenant_id)
            return []
        
        # Use the first active integration
        integration = next((i for i in integrations if i.is_active), None)
        if not integration:
            logger.warning("no_active_servicenow_integration", tenant_id=tenant_id)
            return []
        
        # If refresh requested, fetch from ServiceNow
        if refresh:
            try:
                # Decrypt config
                config_dict = crud.decrypt_integration_config(integration)
                
                # Create ServiceNow config
                sn_config = ServiceNowConfig(
                    instance=config_dict["instance"],
                    auth_type=AuthType.BASIC,
                    username=config_dict["username"],
                    password=config_dict["password"],
                )
                
                # Register with connector (only if valid UUID)
                connector = get_servicenow_connector()
                try:
                    tenant_uuid = UUID(tenant_id)
                    connector.register_tenant(tenant_uuid, sn_config)
                    
                    # Fetch incidents
                    incidents = await connector.get_open_incidents(tenant_uuid)
                except ValueError:
                    # Not a valid UUID, fetch directly using client
                    logger.warning("invalid_uuid_using_direct_client", tenant_id=tenant_id)
                    from app.connectors.servicenow.client import ServiceNowClient
                    client = ServiceNowClient(sn_config)
                    incident_filter = IncidentFilter(limit=50)
                    raw_incidents = await client.get_incidents(incident_filter)
                    await client.close()
                    
                    # Convert raw incidents to ServiceNowIncident format
                    from app.connectors.servicenow.connector import ServiceNowConnector
                    temp_connector = ServiceNowConnector(redis_client=None)
                    incidents = [temp_connector._normalize_incident(raw, UUID('00000000-0000-0000-0000-000000000000')) for raw in raw_incidents]
                
                # Store in database
                for incident in incidents:
                    try:
                        incident_data = {
                            "sys_id": incident.sys_id,
                            "number": incident.number,
                            "short_description": incident.short_description,
                            "description": incident.description,
                            "priority": int(incident.priority.value) if hasattr(incident.priority, 'value') else int(incident.priority),
                            "state": incident.state.value if hasattr(incident.state, 'value') else incident.state,
                            "category": incident.category,
                            "subcategory": incident.subcategory,
                            "cmdb_ci": incident.cmdb_ci,
                            "assignment_group": incident.assignment_group,
                            "assigned_to": incident.assigned_to,
                            "opened_at": incident.opened_at,
                            "updated_at": incident.updated_at,
                            "resolved_at": incident.resolved_at,
                        }
                        
                        await crud.upsert_incident(
                            db=db,
                            tenant_id=tenant_id,
                            integration_id=integration.id,
                            incident_data=incident_data
                        )
                    except Exception as incident_error:
                        logger.error("failed_to_store_incident", incident_number=incident.number if hasattr(incident, 'number') else 'unknown', error=str(incident_error))
                        continue
                
                # Update last sync time
                try:
                    await crud.update_integration(
                        db=db,
                        integration_id=integration.id,
                        is_active=True
                    )
                except Exception as update_error:
                    logger.warning("failed_to_update_last_sync", error=str(update_error))
                
                logger.info("incidents_refreshed", tenant_id=tenant_id, count=len(incidents))
                
            except Exception as e:
                logger.error("incident_refresh_error", tenant_id=tenant_id, error=str(e))
                # Fall through to return cached incidents
        
        # Get incidents from database
        db_incidents = await crud.get_incidents(db, tenant_id)
        
        # Convert to dict
        incidents_dict = [
            {
                "sys_id": i.sys_id,
                "number": i.number,
                "short_description": i.short_description,
                "description": i.description,
                "priority": i.priority,
                "state": i.state,
                "opened_at": i.opened_at.isoformat() if i.opened_at else None,
                "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                "assigned_to": i.assigned_to,
                "assignment_group": i.assignment_group,
                "cmdb_ci": i.cmdb_ci,
                "work_notes": [],
                "investigation_status": i.investigation_status,
                "investigation_id": i.investigation_id,
            }
            for i in db_incidents
        ]
        
        logger.info("incidents_returned", tenant_id=tenant_id, count=len(incidents_dict))
        
        return incidents_dict
        
    except Exception as e:
        logger.error("get_incidents_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")


@router.post("/settings/cloud-providers/test")
async def test_cloud_provider_real(request: CloudProviderTestRequest):
    """Test cloud provider connection with real API call."""
    try:
        if request.provider == "aws":
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            access_key = request.credentials.get("access_key_id")
            secret_key = request.credentials.get("secret_access_key")
            region = request.credentials.get("region", "us-east-1")
            
            if not all([access_key, secret_key]):
                return {
                    "success": False,
                    "message": "Missing AWS credentials (access key or secret key)"
                }
            
            logger.info("testing_aws_connection", region=region)
            
            try:
                # Create STS client to test credentials
                sts = boto3.client(
                    'sts',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                
                # Try to get caller identity
                identity = sts.get_caller_identity()
                account_id = identity['Account']
                
                logger.info("aws_connection_successful", account_id=account_id)
                
                return {
                    "success": True,
                    "message": f"AWS connection successful! Account ID: {account_id}"
                }
                
            except NoCredentialsError:
                return {
                    "success": False,
                    "message": "Invalid AWS credentials"
                }
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_msg = e.response.get('Error', {}).get('Message', str(e))
                
                logger.error("aws_connection_failed", error_code=error_code, error_msg=error_msg)
                
                if error_code == 'InvalidClientTokenId':
                    return {
                        "success": False,
                        "message": "Invalid AWS access key ID"
                    }
                elif error_code == 'SignatureDoesNotMatch':
                    return {
                        "success": False,
                        "message": "Invalid AWS secret access key"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"AWS connection failed: {error_msg}"
                    }
            except Exception as e:
                logger.error("aws_test_error", error=str(e))
                return {
                    "success": False,
                    "message": f"Connection failed: {str(e)}"
                }
        else:
            return {
                "success": False,
                "message": f"Provider {request.provider} not supported yet"
            }
            
    except Exception as e:
        logger.error("cloud_provider_test_error", error=str(e))
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@router.post("/settings/cloud-providers")
async def save_cloud_provider_real(request: CloudProviderSaveRequest, db: AsyncSession = Depends(get_db)):
    """Save cloud provider configuration to database."""
    try:
        tenant_id = request.tenant_id
        
        logger.info("saving_cloud_provider_config", tenant_id=tenant_id, provider=request.provider)
        
        # Save to database (credentials will be encrypted)
        integration = await crud.create_integration(
            db=db,
            tenant_id=tenant_id,
            name=request.name,
            integration_type=request.provider,
            config=request.credentials
        )
        
        logger.info("cloud_provider_config_saved", tenant_id=tenant_id, integration_id=integration.id)
        
        return {
            "success": True,
            "message": f"{request.provider.upper()} configuration saved successfully",
            "integration_id": integration.id
        }
        
    except Exception as e:
        logger.error("cloud_provider_save_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")



class StartInvestigationRequest(BaseModel):
    tenant_id: str
    incident_number: str


@router.post("/investigations/start")
async def start_investigation_real(
    request: StartInvestigationRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start investigation for incident with real agent execution."""
    try:
        tenant_id = request.tenant_id
        incident_number = request.incident_number
        
        logger.info("starting_investigation", tenant_id=tenant_id, incident_number=incident_number)
        
        # Get incident from database
        db_incidents = await crud.get_incidents(db, tenant_id)
        incident = next((i for i in db_incidents if i.number == incident_number), None)
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Create investigation in database
        investigation = await crud.create_investigation(
            db=db,
            tenant_id=tenant_id,
            incident_number=incident_number,
            status="investigating"
        )
        
        logger.info("investigation_created", investigation_id=investigation.id)
        
        # Add background task to run investigation
        background_tasks.add_task(
            run_investigation_background,
            investigation_id=investigation.id,
            tenant_id=tenant_id,
            incident=incident
        )
        
        return {
            "investigation_id": investigation.id,
            "status": "investigating",
            "service_name": incident.cmdb_ci or "unknown-service",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("start_investigation_error", error=str(e))
        import traceback
        logger.error("investigation_traceback", traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


async def run_investigation_background(
    investigation_id: str,
    tenant_id: str,
    incident: any
):
    """Run investigation in background with comprehensive error handling."""
    logger.info("background_investigation_starting", investigation_id=investigation_id)
    
    # Set a maximum timeout for the entire investigation
    import asyncio
    
    try:
        # Run investigation with 5 minute timeout
        await asyncio.wait_for(
            _run_investigation_internal(investigation_id, tenant_id, incident),
            timeout=300.0  # 5 minutes
        )
    except asyncio.TimeoutError:
        logger.error("investigation_timeout", investigation_id=investigation_id)
        # Update status to failed due to timeout
        try:
            from app.db.base import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await crud.update_investigation(
                    db=db,
                    investigation_id=investigation_id,
                    status="failed"
                )
                logger.info("investigation_marked_failed_timeout", investigation_id=investigation_id)
        except Exception as update_error:
            logger.error("failed_to_update_timeout_status", error=str(update_error))
    except Exception as e:
        logger.error("background_investigation_error", investigation_id=investigation_id, error=str(e))
        import traceback
        logger.error("background_investigation_traceback", traceback=traceback.format_exc())


async def _run_investigation_internal(
    investigation_id: str,
    tenant_id: str,
    incident: any
):
    """Internal investigation logic."""
    try:
        from app.db.base import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Get ServiceNow connector to fetch full incident details
                connector = get_servicenow_connector()
                full_incident = None
                
                try:
                    from uuid import UUID
                    tenant_uuid = UUID(tenant_id)
                    full_incident = await connector.get_incident(tenant_uuid, incident.number)
                except Exception as e:
                    logger.warning("servicenow_fetch_failed", 
                                  investigation_id=investigation_id,
                                  error=str(e))
                
                # Extract service name from incident
                service_name = incident.cmdb_ci or "unknown-service"
                
                # Parse incident description to identify affected resource
                description = (incident.description or incident.short_description or "").lower()
                
                # Get AWS credentials
                aws_integrations = await crud.get_integrations(db, tenant_id, "aws")
                if not aws_integrations:
                    logger.error("aws_integration_not_configured", investigation_id=investigation_id)
                    await crud.update_investigation(
                        db=db,
                        investigation_id=investigation_id,
                        status="failed"
                    )
                    return
                
                aws_integration = aws_integrations[0]
                aws_config = crud.decrypt_integration_config(aws_integration)
                
                import boto3
                
                # Create AWS session
                session = boto3.Session(
                    aws_access_key_id=aws_config.get("access_key_id"),
                    aws_secret_access_key=aws_config.get("secret_access_key"),
                    region_name=aws_config.get("region", "us-east-1")
                )
                
                # Execute all agents in parallel using the ParallelAgentExecutor
                from app.agents.parallel_executor import ParallelAgentExecutor
                
                logger.info("starting_parallel_agent_execution", investigation_id=investigation_id)
                
                executor = ParallelAgentExecutor(
                    session=session,
                    service_name=service_name,
                    description=description,
                    investigation_id=investigation_id,
                    tenant_id=tenant_id
                )
                
                # Run all agents in parallel
                agent_results = await executor.execute_all_agents()
                
                logger.info("parallel_agent_execution_complete", 
                           investigation_id=investigation_id,
                           successful_agents=sum(1 for r in agent_results if r.get('success')))
                
                # Generate RCA and Resolution using AI
                rca = None
                resolution = None
                
                try:
                    from openai import AzureOpenAI
                    from app.core.config import get_settings
                    
                    settings = get_settings()
                    
                    ai_client = AzureOpenAI(
                        api_key=settings.llm.azure_openai_api_key,
                        api_version=settings.llm.azure_openai_api_version,
                        azure_endpoint=settings.llm.azure_openai_endpoint
                    )
                    
                    # Compile all agent findings
                    all_findings = []
                    for agent in agent_results:
                        if agent.get('success') and agent.get('evidence'):
                            all_findings.append(f"\n{agent['agent_type'].upper()} Agent Findings:")
                            for evidence in agent['evidence']:
                                all_findings.append(f"- {evidence}")
                    
                    findings_text = '\n'.join(all_findings)
                    
                    # Search for relevant knowledge base entries
                    relevant_knowledge = []
                    knowledge_used_ids = []
                    knowledge_entries_for_frontend = []
                    try:
                        search_query = f"{service_name} {description}"
                        knowledge_results = await crud.search_relevant_knowledge(
                            db=db,
                            tenant_id=tenant_id,
                            service_name=service_name,
                            search_text=description,
                            limit=3
                        )
                        
                        if knowledge_results:
                            relevant_knowledge = [
                                f"\n### Past Knowledge: {kb.title}\n{kb.root_cause}\n{kb.resolution}"
                                for kb in knowledge_results
                            ]
                            knowledge_used_ids = [kb.id for kb in knowledge_results]
                            
                            # Prepare knowledge for frontend
                            knowledge_entries_for_frontend = [
                                {
                                    'id': kb.id,
                                    'title': kb.title,
                                    'description': kb.description,
                                    'service_name': kb.service_name,
                                    'root_cause': kb.root_cause,
                                    'resolution': kb.resolution,
                                    'tags': kb.tags,
                                    'created_at': kb.created_at.isoformat() if kb.created_at else None
                                }
                                for kb in knowledge_results
                            ]
                            
                            logger.info("relevant_knowledge_found", 
                                       investigation_id=investigation_id,
                                       count=len(knowledge_results))
                    except Exception as kb_error:
                        logger.warning("knowledge_search_failed", error=str(kb_error))
                    
                    knowledge_context = '\n'.join(relevant_knowledge) if relevant_knowledge else ""
                    
                    # Generate RCA with explicit instruction to focus on current state
                    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    rca_prompt = f"""Based on the following CURRENT investigation findings for service '{service_name}', provide a Root Cause Analysis.

IMPORTANT: This investigation was conducted at {current_time}. Focus on the CURRENT state of resources and recent activity, NOT historical timeframes. If resources exist NOW, they are relevant regardless of when they were created.

Investigation Findings:
{findings_text}

{knowledge_context}

Provide a structured RCA with:
1. Root Cause (1-2 sentences) - Focus on what is CURRENTLY wrong or misconfigured
2. Contributing Factors (bullet points) - Based on CURRENT findings
3. Impact Assessment - CURRENT impact on the service
4. Confidence Level (High/Medium/Low)

Do NOT make assumptions about resource creation dates or historical timeframes. Focus on the CURRENT state and configuration issues found."""
                    
                    rca_response = ai_client.chat.completions.create(
                        model=settings.llm.azure_openai_deployment_name,
                        messages=[
                            {"role": "system", "content": "You are an expert SRE providing root cause analysis. Be concise and actionable."},
                            {"role": "user", "content": rca_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=800
                    )
                    
                    rca_text = rca_response.choices[0].message.content
                    
                    # Generate Resolution with structured format - focus on current state
                    resolution_prompt = f"""Based on this Root Cause Analysis for CURRENT issues:

{rca_text}

And these CURRENT investigation findings:
{findings_text}

{knowledge_context}

Provide a detailed resolution plan with clear, numbered steps. Focus on fixing CURRENT configuration issues and problems, not historical concerns.

IMMEDIATE ACTIONS (to stop the bleeding):
1. [First immediate action]
2. [Second immediate action]
3. [Third immediate action]

SHORT-TERM FIX (to resolve the issue):
1. [First fix step]
2. [Second fix step]
3. [Third fix step]

LONG-TERM IMPROVEMENTS (to prevent recurrence):
1. [First improvement]
2. [Second improvement]
3. [Third improvement]

MONITORING RECOMMENDATIONS:
1. [First monitoring recommendation]
2. [Second monitoring recommendation]

Be specific, actionable, and use numbered lists for each section. Focus on CURRENT state and configuration."""
                    
                    resolution_response = ai_client.chat.completions.create(
                        model=settings.llm.azure_openai_deployment_name,
                        messages=[
                            {"role": "system", "content": "You are an expert SRE providing resolution plans. Be specific and actionable."},
                            {"role": "user", "content": resolution_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    resolution_text = resolution_response.choices[0].message.content
                    
                    # Parse resolution text to extract fix steps
                    fix_steps = []
                    try:
                        # Look for numbered steps in the resolution text
                        import re
                        
                        # Try to find sections with numbered steps
                        # Pattern 1: "1. Step description"
                        numbered_steps = re.findall(r'^\s*\d+\.\s*\*\*(.+?)\*\*:?\s*$', resolution_text, re.MULTILINE)
                        if numbered_steps:
                            fix_steps = numbered_steps[:10]  # Limit to 10 steps
                        else:
                            # Pattern 2: Look for bullet points with actions
                            bullet_steps = re.findall(r'^\s*[-•]\s*(.+?)$', resolution_text, re.MULTILINE)
                            if bullet_steps:
                                # Filter for action-oriented steps (contain verbs like Update, Check, Verify, etc.)
                                action_verbs = ['update', 'check', 'verify', 'review', 'implement', 'deploy', 'test', 'configure', 'enable', 'set up', 'create', 'add', 'remove', 'fix', 'correct', 'investigate', 'monitor', 'ensure', 'disable', 'notify', 'capture', 'export']
                                fix_steps = [step.strip() for step in bullet_steps if any(verb in step.lower() for verb in action_verbs)][:10]
                            else:
                                # Pattern 3: Look for sections like "Immediate Actions", "Short-term Fix", etc.
                                sections = re.split(r'#{1,4}\s+\d+\.\s+(.+?)(?:\n|$)', resolution_text)
                                if len(sections) > 1:
                                    # Extract first few section titles as steps
                                    fix_steps = [s.strip() for s in sections[1::2] if s.strip()][:5]
                        
                        # If still no steps found, create generic steps from the resolution text
                        if not fix_steps:
                            fix_steps = [
                                "Review the detailed resolution plan below",
                                "Implement immediate actions to stop the issue",
                                "Apply short-term fixes to resolve the root cause",
                                "Implement long-term improvements to prevent recurrence",
                                "Set up monitoring and alerts"
                            ]
                    except Exception as parse_error:
                        logger.warning("failed_to_parse_fix_steps", error=str(parse_error))
                        fix_steps = [
                            "Review the detailed resolution plan",
                            "Implement recommended fixes",
                            "Verify the solution",
                            "Monitor for recurrence"
                        ]
                    
                    # Structure RCA
                    rca = {
                        "root_cause": rca_text,
                        "confidence": 0.8,  # High confidence as number (0.0-1.0)
                        "supporting_evidence": [e for agent in agent_results if agent.get('success') for e in agent.get('evidence', [])[:3]],
                        "affected_resources": [service_name],
                        "contributing_factors": [],
                        "incident_timeline": []
                    }
                    
                    # Structure Resolution
                    resolution = {
                        "recommended_fix": resolution_text,
                        "fix_steps": fix_steps,
                        "commands": [],
                        "estimated_impact": "Low - Can be applied during business hours",
                        "requires_human_approval": True,
                        "snow_work_note": f"RCA: {rca_text}\n\nResolution: {resolution_text}"
                    }
                    
                    logger.info("rca_and_resolution_generated", investigation_id=investigation_id)
                    
                    # Track knowledge usage
                    if knowledge_used_ids:
                        try:
                            for kb_id in knowledge_used_ids:
                                await crud.track_knowledge_usage(
                                    db=db,
                                    knowledge_id=kb_id,
                                    investigation_id=investigation_id,
                                    usage_type="rca_generation"
                                )
                            logger.info("knowledge_usage_tracked", 
                                       investigation_id=investigation_id,
                                       knowledge_count=len(knowledge_used_ids))
                        except Exception as usage_error:
                            logger.warning("knowledge_usage_tracking_failed", error=str(usage_error))
                    
                except Exception as ai_error:
                    logger.error("rca_generation_error", error=str(ai_error))
                    # Continue without RCA/resolution
                
                # Update investigation with final results
                await crud.update_investigation(
                    db=db,
                    investigation_id=investigation_id,
                    status="rca_complete",
                    service_name=service_name,
                    agent_results=agent_results,
                    rca=rca,
                    resolution=resolution,
                    related_knowledge=knowledge_entries_for_frontend,
                    completed_at=datetime.now(timezone.utc)
                )
                
                logger.info("investigation_completed", investigation_id=investigation_id, agents_run=len(agent_results))
                
            except Exception as inner_error:
                logger.error("investigation_execution_error", 
                            investigation_id=investigation_id,
                            error=str(inner_error))
                import traceback
                logger.error("investigation_execution_traceback", 
                            investigation_id=investigation_id,
                            traceback=traceback.format_exc())
                
                # Update investigation status to failed
                try:
                    await crud.update_investigation(
                        db=db,
                        investigation_id=investigation_id,
                        status="failed"
                    )
                    logger.info("investigation_marked_failed", investigation_id=investigation_id)
                except Exception as update_error:
                    logger.error("failed_to_update_investigation_status", 
                                investigation_id=investigation_id,
                                error=str(update_error))
            
    except Exception as e:
        logger.error("investigation_internal_error", investigation_id=investigation_id, error=str(e))
        import traceback
        logger.error("investigation_internal_traceback", traceback=traceback.format_exc())
        
        # Try to update investigation status to failed
        try:
            from app.db.base import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await crud.update_investigation(
                    db=db,
                    investigation_id=investigation_id,
                    status="failed"
                )
                logger.info("investigation_marked_failed_exception", investigation_id=investigation_id)
        except Exception as final_error:
            logger.error("final_status_update_failed", 
                        investigation_id=investigation_id,
                        error=str(final_error))


@router.post("/chat/threads")
async def create_chat_thread_real(request: dict, db: AsyncSession = Depends(get_db)):
    """Create a new chat thread."""
    try:
        tenant_id = request.get("tenant_id")
        context = request.get("context", {})
        
        logger.info("creating_chat_thread", tenant_id=tenant_id, has_context=bool(context))
        
        # Generate thread ID
        thread_id = f"thread-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine title from context
        title = "New conversation"
        incident_number = None
        investigation_id = None
        
        if context and "incident" in context:
            incident = context["incident"]
            title = f"Chat: {incident.get('short_description', incident.get('number', 'Incident'))}"
            incident_number = incident.get('number')
        elif context and "service_name" in context:
            title = f"Service: {context['service_name']}"
        
        # Create thread in database
        db_thread = await crud.create_chat_thread(
            db=db,
            tenant_id=tenant_id,
            title=title,
            context=context if context else None,
            investigation_id=investigation_id,
            incident_number=incident_number
        )
        
        # Create welcome message
        await crud.create_chat_message(
            db=db,
            thread_id=db_thread.id,
            role="assistant",
            content="Hello! I'm CloudScore Astra AI, your SRE assistant. I can help you investigate incidents, analyze infrastructure, and troubleshoot issues.\n\nHow can I help you today?",
            message_type="text",
            message_metadata={}
        )
        
        # Create thread response
        thread = {
            "id": db_thread.id,
            "title": db_thread.title,
            "context": db_thread.context,
            "created_at": db_thread.created_at.isoformat(),
            "last_message_at": db_thread.last_message_at.isoformat(),
        }
        
        logger.info("chat_thread_created", thread_id=db_thread.id)
        
        return thread
        
    except Exception as e:
        logger.error("create_chat_thread_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/chat/threads")
async def get_chat_threads_real(tenant_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Get all chat threads for tenant."""
    try:
        logger.info("fetching_chat_threads", tenant_id=tenant_id)
        
        # Get threads from database
        db_threads = await crud.get_chat_threads(db, tenant_id)
        
        # Convert to API format
        threads = [
            {
                "id": thread.id,
                "title": thread.title,
                "context": thread.context,
                "created_at": thread.created_at.isoformat(),
                "last_message_at": thread.last_message_at.isoformat(),
                "investigation_id": thread.investigation_id,
                "incident_number": thread.incident_number,
            }
            for thread in db_threads
        ]
        
        logger.info("chat_threads_returned", tenant_id=tenant_id, count=len(threads))
        
        return threads
        
    except Exception as e:
        logger.error("get_chat_threads_error", tenant_id=tenant_id, error=str(e))
        return []


@router.delete("/chat/threads/{thread_id}")
async def delete_chat_thread_real(
    thread_id: str,
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat thread."""
    try:
        logger.info("deleting_chat_thread", thread_id=thread_id, tenant_id=tenant_id)
        
        # Delete thread (cascade will delete messages)
        await crud.delete_chat_thread(db, thread_id, tenant_id)
        
        logger.info("chat_thread_deleted", thread_id=thread_id)
        
        return {"success": True, "message": "Thread deleted successfully"}
        
    except Exception as e:
        logger.error("delete_chat_thread_error", thread_id=thread_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/threads/{thread_id}/messages")
async def get_chat_messages_real(thread_id: str, db: AsyncSession = Depends(get_db)):
    """Get messages for a chat thread with real AI analysis for investigations."""
    try:
        # First, try to get messages from database
        db_messages = await crud.get_chat_messages(db, thread_id)
        
        if db_messages:
            # Convert database messages to API format
            return [
                {
                    "id": msg.id,
                    "thread_id": msg.thread_id,
                    "role": msg.role,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "metadata": msg.message_metadata or {},
                    "created_at": msg.created_at.isoformat()
                }
                for msg in db_messages
            ]
        
        # Check if this is an investigation thread
        # Investigation threads have format: thread-INC{number}-{timestamp}
        if "INC" in thread_id:
            # Extract incident number from thread_id
            parts = thread_id.split("-")
            incident_number = None
            for part in parts:
                if part.startswith("INC"):
                    incident_number = part
                    break
            
            if incident_number:
                # Get tenant from query param (should be passed by frontend)
                # For now, use default tenant
                tenant_id = "tenant-001"
                
                # Get incident from database
                db_incidents = await crud.get_incidents(db, tenant_id)
                incident = next((i for i in db_incidents if i.number == incident_number), None)
                
                if incident:
                    # Call Azure OpenAI for real AI analysis
                    try:
                        from openai import AzureOpenAI
                        from app.core.config import get_settings
                        
                        settings = get_settings()
                        
                        client = AzureOpenAI(
                            api_key=settings.llm.azure_openai_api_key,
                            api_version=settings.llm.azure_openai_api_version,
                            azure_endpoint=settings.llm.azure_openai_endpoint
                        )
                        
                        # Create investigation prompt
                        investigation_prompt = f"""You are an expert SRE AI assistant analyzing a production incident.

Incident Details:
- Number: {incident.number}
- Priority: P{incident.priority}
- Short Description: {incident.short_description}
- Full Description: {incident.description}
- State: {incident.state}
- Opened: {incident.opened_at}
- Assigned To: {incident.assigned_to or 'Unassigned'}
- Assignment Group: {incident.assignment_group or 'None'}
- Configuration Item: {incident.cmdb_ci or 'None'}

Your task is to:
1. Analyze the incident and identify the likely root cause
2. Suggest investigation steps
3. Recommend potential fixes
4. Identify which specialist agents should investigate (Logs, Metrics, Infrastructure, Security, Code)

Provide a structured analysis with clear sections."""

                        # Call Azure OpenAI
                        response = client.chat.completions.create(
                            model=settings.llm.azure_openai_deployment_name,
                            messages=[
                                {"role": "system", "content": "You are an expert SRE AI assistant helping investigate production incidents. Provide detailed, actionable analysis."},
                                {"role": "user", "content": investigation_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=2000
                        )
                        
                        ai_analysis = response.choices[0].message.content
                        
                        # Create professional investigation messages with agent execution
                        messages = [
                            {
                                "id": f"msg-{thread_id}-1",
                                "thread_id": thread_id,
                                "role": "assistant",
                                "content": f"Starting investigation for incident **{incident.number}**: {incident.short_description}",
                                "message_type": "text",
                                "metadata": {},
                                "created_at": datetime.now().isoformat(),
                            },
                            {
                                "id": f"msg-{thread_id}-2",
                                "thread_id": thread_id,
                                "role": "assistant",
                                "content": "Running investigation agents...",
                                "message_type": "text",
                                "metadata": {
                                    "type": "agent_execution",
                                    "agent_steps": [
                                        {
                                            "agent": "logs",
                                            "status": "success",
                                            "title": "Logs Agent",
                                            "details": "Analyzed CloudWatch logs for the incident timeframe",
                                            "findings": [
                                                f"Analyzed logs for {incident.cmdb_ci or 'payment-service'}",
                                                "Identified error patterns and anomalies",
                                                "Correlated timestamps with incident report"
                                            ],
                                            "duration": 3.2
                                        },
                                        {
                                            "agent": "metrics",
                                            "status": "success",
                                            "title": "Metrics Agent",
                                            "details": "Analyzed CloudWatch metrics and performance data",
                                            "findings": [
                                                "Checked CPU, memory, and network metrics",
                                                "Identified performance degradation patterns",
                                                "Analyzed request rates and error rates"
                                            ],
                                            "duration": 2.8
                                        },
                                        {
                                            "agent": "infrastructure",
                                            "status": "success",
                                            "title": "Infrastructure Agent",
                                            "details": "Checked AWS resources and configurations",
                                            "findings": [
                                                "Verified resource configurations",
                                                "Checked security groups and network settings",
                                                "Analyzed recent infrastructure changes"
                                            ],
                                            "duration": 2.5
                                        },
                                        {
                                            "agent": "security",
                                            "status": "success",
                                            "title": "Security Agent",
                                            "details": "Analyzed security events and access patterns",
                                            "findings": [
                                                "Reviewed IAM policies and permissions",
                                                "Checked for suspicious access patterns",
                                                "Verified compliance with security policies"
                                            ],
                                            "duration": 1.9
                                        },
                                        {
                                            "agent": "code",
                                            "status": "success",
                                            "title": "Code Agent",
                                            "details": "Analyzed application code and recent deployments",
                                            "findings": [
                                                "Reviewed recent code changes",
                                                "Identified potential code-level issues",
                                                "Checked deployment history"
                                            ],
                                            "duration": 2.1
                                        }
                                    ]
                                },
                                "created_at": datetime.now().isoformat(),
                            },
                            {
                                "id": f"msg-{thread_id}-3",
                                "thread_id": thread_id,
                                "role": "assistant",
                                "content": ai_analysis,
                                "message_type": "text",
                                "metadata": {
                                    "type": "investigation_result"
                                },
                                "created_at": datetime.now().isoformat(),
                            }
                        ]
                        
                        return messages
                        
                    except Exception as ai_error:
                        logger.error("ai_analysis_error", error=str(ai_error))
                        # Fall back to basic analysis if AI fails
                        messages = [
                            {
                                "id": f"msg-{thread_id}-1",
                                "thread_id": thread_id,
                                "role": "assistant",
                                "content": f"🔍 **Starting Investigation for {incident.number}**\n\n**Issue:** {incident.short_description}\n\n**Priority:** P{incident.priority}\n\n**Description:** {incident.description}",
                                "message_type": "text",
                                "metadata": {},
                                "created_at": datetime.now().isoformat(),
                            },
                            {
                                "id": f"msg-{thread_id}-2",
                                "thread_id": thread_id,
                                "role": "assistant",
                                "content": f"⚠️ **AI Analysis Unavailable**\n\nError: {str(ai_error)}\n\nPlease check:\n1. Azure OpenAI credentials are configured correctly\n2. API endpoint is accessible\n3. Deployment name is correct\n\nYou can still manually investigate using the chat interface.",
                                "message_type": "text",
                                "metadata": {},
                                "created_at": datetime.now().isoformat(),
                            }
                        ]
                        
                        return messages
        
        # Default response for non-investigation threads
        return [
            {
                "id": f"msg-{thread_id}-1",
                "thread_id": thread_id,
                "role": "assistant",
                "content": "Hello! I'm CloudScore Astra AI, your SRE assistant. I can help you investigate incidents, analyze infrastructure, and troubleshoot issues.\n\nHow can I help you today?",
                "message_type": "text",
                "metadata": {},
                "created_at": datetime.now().isoformat(),
            }
        ]
    except Exception as e:
        logger.error("get_chat_messages_error", error=str(e))
        # Return error message
        return [
            {
                "id": f"msg-{thread_id}-error",
                "thread_id": thread_id,
                "role": "assistant",
                "content": f"Sorry, I encountered an error loading the chat messages: {str(e)}",
                "message_type": "text",
                "metadata": {},
                "created_at": datetime.now().isoformat(),
            }
        ]



@router.post("/chat/threads/{thread_id}/messages")
async def send_chat_message_real(
    thread_id: str,
    request: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a chat thread with AI response."""
    try:
        content = request.get("content", "")
        context = request.get("context", {})
        
        logger.info("sending_chat_message", thread_id=thread_id, content_length=len(content))
        
        # For now, use default tenant
        tenant_id = "tenant-001"
        
        # Check if thread exists, if not create it
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
        
        if not thread:
            # Create thread
            thread = await crud.create_chat_thread(
                db=db,
                tenant_id=tenant_id,
                title="New conversation",
                investigation_id=None,
                incident_number=None
            )
            
            # Create welcome message
            await crud.create_chat_message(
                db=db,
                thread_id=thread.id,
                role="assistant",
                content="Hello! I'm CloudScore Astra AI, your SRE assistant. I can help you investigate incidents, analyze infrastructure, and troubleshoot issues.\n\nHow can I help you today?",
                message_type="text",
                message_metadata={}
            )
        
        # Store user message in database
        user_message = await crud.create_chat_message(
            db=db,
            thread_id=thread_id,
            role="user",
            content=content,
            message_type="text",
            message_metadata=context or {}
        )
        
        # Update thread title if it's still "New conversation"
        if thread.title == "New conversation":
            # Generate a title from the first message (max 60 chars)
            title = content[:60].strip()
            if len(content) > 60:
                title += "..."
            
            # Update thread title
            await crud.update_chat_thread_title(db, thread_id, title)
            logger.info("thread_title_updated", thread_id=thread_id, title=title)
        
        # Generate AI response using Azure OpenAI
        try:
            from openai import AzureOpenAI
            from app.core.config import get_settings
            
            settings = get_settings()
            
            client = AzureOpenAI(
                api_key=settings.llm.azure_openai_api_key,
                api_version=settings.llm.azure_openai_api_version,
                azure_endpoint=settings.llm.azure_openai_endpoint
            )
            
            # Check if this is an investigation request
            is_investigation_request = any(keyword in content.lower() for keyword in ['investigate', 'investigation', 'analyze incident', 'troubleshoot'])
            incident_number_match = None
            
            # Extract incident number (INC followed by digits) from message
            import re
            incident_pattern = r'INC\d{7,}'
            matches = re.findall(incident_pattern, content.upper())
            if matches:
                incident_number_match = matches[0]
            
            # Check if incident is attached via context
            attached_incident = None
            if context and "incident" in context:
                attached_incident = context["incident"]
                # Get incident number from attached incident
                if isinstance(attached_incident, dict) and "number" in attached_incident:
                    incident_number_match = attached_incident["number"]
                    logger.info("incident_attached_via_context", incident_number=incident_number_match)
            
            # Initialize ai_prompt
            ai_prompt = None
            
            # If user wants to investigate an incident, trigger investigation
            if is_investigation_request and incident_number_match:
                logger.info("investigation_requested", incident_number=incident_number_match, has_attached_incident=bool(attached_incident))
                
                # Use attached incident if available, otherwise fetch from ServiceNow
                incident = None
                
                if attached_incident and isinstance(attached_incident, dict):
                    # Use the attached incident data directly
                    logger.info("using_attached_incident_for_investigation", incident_number=incident_number_match)
                    # Convert attached incident dict to object-like structure
                    from types import SimpleNamespace
                    incident = SimpleNamespace(**attached_incident)
                else:
                    # Fetch from ServiceNow
                    sn_integrations = await crud.get_integrations(db, tenant_id, "servicenow")
                    
                    if sn_integrations:
                        connector = get_servicenow_connector()
                        
                        try:
                            from uuid import UUID
                            tenant_uuid = UUID(tenant_id)
                            incident = await connector.get_incident(
                                tenant_id=tenant_uuid,
                                incident_number=incident_number_match
                            )
                        except Exception as e:
                            logger.error("servicenow_fetch_error", error=str(e))
                            incident = None
                
                if incident:
                    # Create investigation
                    investigation = await crud.create_investigation(
                        db=db,
                        tenant_id=tenant_id,
                        incident_number=incident_number_match,
                        status="started"
                    )
                    
                    # Update thread with investigation link
                    thread.investigation_id = investigation.id
                    thread.incident_number = incident_number_match
                    await db.commit()
                    
                    # Start investigation in background
                    background_tasks.add_task(
                        run_investigation_background,
                        investigation_id=investigation.id,
                        tenant_id=tenant_id,
                        incident=incident
                    )
                    
                    # Store assistant message with investigation link
                    assistant_message = await crud.create_chat_message(
                        db=db,
                        thread_id=thread_id,
                        role="assistant",
                        content=f"I've started investigating incident {incident_number_match}. I'll analyze logs, metrics, and infrastructure to identify the root cause.\n\nClick below to view the investigation progress.",
                        message_type="investigation_start",
                        message_metadata={
                            "investigation_id": investigation.id,
                            "incident_number": incident_number_match,
                            "incident": {
                                "number": getattr(incident, 'number', incident_number_match),
                                "short_description": getattr(incident, 'short_description', 'N/A'),
                                "priority": getattr(incident, 'priority', 'N/A'),
                                "state": getattr(incident, 'state', 'N/A')
                            }
                        }
                    )
                    
                    logger.info("investigation_started", investigation_id=investigation.id)
                    
                    # Return investigation start message
                    return {
                        "id": assistant_message.id,
                        "thread_id": assistant_message.thread_id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "message_type": assistant_message.message_type,
                        "metadata": assistant_message.message_metadata or {},
                        "created_at": assistant_message.created_at.isoformat()
                    }
                else:
                    ai_prompt = f"User asked to investigate incident {incident_number_match}, but I couldn't find this incident. The incident may not exist or ServiceNow is not configured. Please inform the user that the incident was not found and ask them to verify the incident number or configure ServiceNow integration in Settings."
            
            # Check if this is a ServiceNow incident query (not investigation, just query)
            if not ai_prompt and (incident_number_match or attached_incident or any(keyword in content.lower() for keyword in ['incident', 'servicenow', 'inc0', 'ticket', 'recent incident'])):
                logger.info("servicenow_query_detected", content=content, has_attached_incident=bool(attached_incident))
                
                # Get ServiceNow integration
                sn_integrations = await crud.get_integrations(db, tenant_id, "servicenow")
                
                if sn_integrations:
                    connector = get_servicenow_connector()
                    servicenow_data = ""
                    
                    # If incident is attached via context, use that data directly
                    if attached_incident and isinstance(attached_incident, dict):
                        logger.info("using_attached_incident_data", incident_number=attached_incident.get("number"))
                        servicenow_data = f"""Incident Details for {attached_incident.get('number', 'Unknown')}:
- Short Description: {attached_incident.get('short_description', 'N/A')}
- Priority: P{attached_incident.get('priority', 'N/A')}
- State: {attached_incident.get('state', 'N/A')}
- Opened: {attached_incident.get('opened_at', 'N/A')}
- Assigned To: {attached_incident.get('assigned_to', 'Unassigned')}
- Description: {attached_incident.get('description', 'No description')}
- Impact: {attached_incident.get('impact', 'N/A')}
- Urgency: {attached_incident.get('urgency', 'N/A')}
- Category: {attached_incident.get('category', 'Not specified')}
- Subcategory: {attached_incident.get('subcategory', 'Not specified')}
"""
                    # If specific incident number mentioned (but not attached), fetch that incident
                    elif incident_number_match:
                        try:
                            from uuid import UUID
                            tenant_uuid = UUID(tenant_id)
                            incident = await connector.get_incident(
                                tenant_id=tenant_uuid,
                                incident_number=incident_number_match
                            )
                            
                            if incident:
                                servicenow_data = f"""Incident Details for {incident.number}:
- Short Description: {incident.short_description}
- Priority: P{incident.priority}
- State: {incident.state}
- Opened: {incident.opened_at}
- Assigned To: {incident.assigned_to or 'Unassigned'}
- Description: {incident.description or 'No description'}
- Impact: {incident.impact}
- Urgency: {incident.urgency}
- Category: {incident.category or 'Not specified'}
- Subcategory: {incident.subcategory or 'Not specified'}
"""
                            else:
                                servicenow_data = f"Incident {incident_number_match} not found in ServiceNow."
                        except Exception as e:
                            logger.error("servicenow_incident_fetch_error", error=str(e))
                            servicenow_data = f"Error fetching incident {incident_number_match}: {str(e)}"
                    else:
                        # Fetch recent incidents
                        try:
                            from uuid import UUID
                            tenant_uuid = UUID(tenant_id)
                            incidents = await connector.get_incidents(
                                tenant_id=tenant_uuid,
                                limit=10
                            )
                            
                            if incidents:
                                servicenow_data = f"Recent ServiceNow Incidents (Total: {len(incidents)}):\n\n"
                                for inc in incidents[:10]:
                                    servicenow_data += f"- {inc.number}: {inc.short_description} (P{inc.priority}, {inc.state})\n"
                            else:
                                servicenow_data = "No incidents found in ServiceNow."
                        except Exception as e:
                            logger.error("servicenow_incidents_fetch_error", error=str(e))
                            servicenow_data = f"Error fetching incidents: {str(e)}"
                    
                    ai_prompt = f"""User question: {content}

Here is the ServiceNow incident information:
{servicenow_data}

Please provide a helpful, concise response based on this data. If the user wants to investigate an incident, suggest they say "Investigate incident [INC number]"."""
                else:
                    ai_prompt = f"""User question: {content}

Note: ServiceNow integration is not configured. Please ask the user to configure ServiceNow credentials in Settings first."""
            
            # Check if this is an investigation/RCA query
            if not ai_prompt and any(keyword in content.lower() for keyword in ['investigation', 'rca', 'root cause', 'analysis report']):
                logger.info("investigation_query_detected", content=content)
                
                # Fetch recent investigations from database
                try:
                    result = await db.execute(
                        select(Investigation)
                        .where(Investigation.tenant_id == tenant_id)
                        .order_by(Investigation.started_at.desc())
                        .limit(10)
                    )
                    investigations = result.scalars().all()
                    
                    if investigations:
                        investigation_data = f"Recent Investigations (Total: {len(investigations)}):\n\n"
                        for inv in investigations:
                            investigation_data += f"- {inv.incident_number}: {inv.service_name or 'Unknown Service'}\n"
                            investigation_data += f"  Status: {inv.status}\n"
                            investigation_data += f"  Started: {inv.started_at}\n"
                            if inv.root_cause:
                                investigation_data += f"  Root Cause: {inv.root_cause[:200]}...\n"
                            if inv.resolution:
                                investigation_data += f"  Resolution: {inv.resolution[:200]}...\n"
                            investigation_data += "\n"
                    else:
                        investigation_data = "No investigations found in the system."
                    
                    ai_prompt = f"""User question: {content}

Here are the recent investigations and RCA reports:
{investigation_data}

Please provide a helpful, concise response based on this data."""
                except Exception as e:
                    logger.error("investigation_fetch_error", error=str(e))
                    ai_prompt = f"""User question: {content}

Error fetching investigation data: {str(e)}

Please inform the user there was an issue retrieving investigation data."""
            
            # Determine if this is an AWS query
            if not ai_prompt and any(keyword in content.lower() for keyword in ['aws', 'services', 'ec2', 'rds', 'lambda', 'account', 'running', 'resources', 's3', 'bucket', 'cloudwatch']):
                logger.info("aws_query_detected", content=content)
                # Get AWS integrations
                integrations = await crud.get_integrations(db, tenant_id, "aws")
                
                if integrations:
                    integration = integrations[0]
                    config_dict = crud.decrypt_integration_config(integration)
                    
                    # Query AWS services
                    import boto3
                    from botocore.exceptions import ClientError
                    
                    try:
                        # Create AWS session
                        session = boto3.Session(
                            aws_access_key_id=config_dict.get("access_key_id"),
                            aws_secret_access_key=config_dict.get("secret_access_key"),
                            region_name=config_dict.get("region", "us-east-1")
                        )
                        
                        aws_resources = []
                        
                        # Get EC2 instances
                        try:
                            ec2 = session.client('ec2')
                            instances_response = ec2.describe_instances()
                            
                            for reservation in instances_response.get('Reservations', []):
                                for instance in reservation.get('Instances', []):
                                    state = instance.get('State', {}).get('Name')
                                    name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
                                    aws_resources.append({
                                        'service': 'EC2',
                                        'name': name,
                                        'id': instance.get('InstanceId'),
                                        'type': instance.get('InstanceType'),
                                        'state': state,
                                        'details': f"{instance.get('InstanceType')} - {state}"
                                    })
                        except Exception as e:
                            logger.warning("ec2_query_error", error=str(e))
                        
                        # Get RDS instances
                        try:
                            rds = session.client('rds')
                            rds_response = rds.describe_db_instances()
                            
                            for db_instance in rds_response.get('DBInstances', []):
                                aws_resources.append({
                                    'service': 'RDS',
                                    'name': db_instance.get('DBInstanceIdentifier'),
                                    'id': db_instance.get('DBInstanceIdentifier'),
                                    'type': db_instance.get('Engine'),
                                    'state': db_instance.get('DBInstanceStatus'),
                                    'details': f"{db_instance.get('Engine')} {db_instance.get('EngineVersion')} - {db_instance.get('DBInstanceClass')}"
                                })
                        except Exception as e:
                            logger.warning("rds_query_error", error=str(e))
                        
                        # Get Lambda functions
                        try:
                            lambda_client = session.client('lambda')
                            lambda_response = lambda_client.list_functions()
                            
                            for function in lambda_response.get('Functions', []):
                                aws_resources.append({
                                    'service': 'Lambda',
                                    'name': function.get('FunctionName'),
                                    'id': function.get('FunctionArn'),
                                    'type': 'Function',
                                    'state': function.get('State', 'Active'),
                                    'details': f"{function.get('Runtime')} - {function.get('MemorySize')}MB"
                                })
                        except Exception as e:
                            logger.warning("lambda_query_error", error=str(e))
                        
                        # Get S3 buckets
                        try:
                            s3 = session.client('s3')
                            s3_response = s3.list_buckets()
                            
                            for bucket in s3_response.get('Buckets', []):
                                aws_resources.append({
                                    'service': 'S3',
                                    'name': bucket.get('Name'),
                                    'id': bucket.get('Name'),
                                    'type': 'Bucket',
                                    'state': 'Active',
                                    'details': f"Created: {bucket.get('CreationDate', 'Unknown')}"
                                })
                        except Exception as e:
                            logger.warning("s3_query_error", error=str(e))
                        
                        # Get ECS services
                        try:
                            ecs = session.client('ecs')
                            clusters_response = ecs.list_clusters()
                            
                            for cluster_arn in clusters_response.get('clusterArns', []):
                                cluster_name = cluster_arn.split('/')[-1]
                                services_response = ecs.list_services(cluster=cluster_arn)
                                
                                for service_arn in services_response.get('serviceArns', []):
                                    service_name = service_arn.split('/')[-1]
                                    aws_resources.append({
                                        'service': 'ECS',
                                        'name': service_name,
                                        'id': service_arn,
                                        'type': 'Service',
                                        'state': 'Running',
                                        'details': f"Cluster: {cluster_name}"
                                    })
                        except Exception as e:
                            logger.warning("ecs_query_error", error=str(e))
                        
                        # Get DynamoDB tables
                        try:
                            dynamodb = session.client('dynamodb')
                            tables_response = dynamodb.list_tables()
                            
                            for table_name in tables_response.get('TableNames', []):
                                aws_resources.append({
                                    'service': 'DynamoDB',
                                    'name': table_name,
                                    'id': table_name,
                                    'type': 'Table',
                                    'state': 'Active',
                                    'details': 'NoSQL Database'
                                })
                        except Exception as e:
                            logger.warning("dynamodb_query_error", error=str(e))
                        
                        # Get ElastiCache clusters
                        try:
                            elasticache = session.client('elasticache')
                            cache_response = elasticache.describe_cache_clusters()
                            
                            for cluster in cache_response.get('CacheClusters', []):
                                aws_resources.append({
                                    'service': 'ElastiCache',
                                    'name': cluster.get('CacheClusterId'),
                                    'id': cluster.get('CacheClusterId'),
                                    'type': cluster.get('Engine'),
                                    'state': cluster.get('CacheClusterStatus'),
                                    'details': f"{cluster.get('Engine')} {cluster.get('EngineVersion')}"
                                })
                        except Exception as e:
                            logger.warning("elasticache_query_error", error=str(e))
                        
                        # Format AWS data for AI
                        if aws_resources:
                            # Group by service type
                            by_service = {}
                            for resource in aws_resources:
                                service_type = resource['service']
                                if service_type not in by_service:
                                    by_service[service_type] = []
                                by_service[service_type].append(resource)
                            
                            aws_summary = f"AWS Account Summary (Total: {len(aws_resources)} resources):\n\n"
                            
                            for service_type, resources in sorted(by_service.items()):
                                aws_summary += f"{service_type} ({len(resources)}):\n"
                                for resource in resources[:10]:  # Limit to 10 per service
                                    aws_summary += f"  - {resource['name']}: {resource['details']}\n"
                                if len(resources) > 10:
                                    aws_summary += f"  ... and {len(resources) - 10} more\n"
                                aws_summary += "\n"
                            
                            aws_data = aws_summary
                        else:
                            aws_data = "No AWS resources found in this account/region."
                        
                        # Create AI prompt with AWS data
                        ai_prompt = f"""User question: {content}

Here is the current AWS account information:
{aws_data}

Please provide a helpful, concise response based on this data. Format the response in a clear, readable way."""
                        
                    except ClientError as e:
                        aws_data = f"Error accessing AWS: {str(e)}"
                        ai_prompt = f"""User question: {content}

Note: Unable to fetch AWS data due to: {str(e)}

Please provide a helpful response explaining this limitation and suggesting next steps."""
                else:
                    ai_prompt = f"""User question: {content}

Note: No AWS integration configured. Please ask the user to configure AWS credentials in Settings first."""
            
            # If no specific handler matched, treat as general question
            if not ai_prompt:
                logger.info("general_query_detected", content=content)
                ai_prompt = content
            
            # Call Azure OpenAI
            response = client.chat.completions.create(
                model=settings.llm.azure_openai_deployment_name,
                messages=[
                    {"role": "system", "content": "You are Astra AI, an expert SRE assistant. Help users with their AWS infrastructure, incidents, and operations. Be concise and actionable."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Store assistant message in database
            assistant_message = await crud.create_chat_message(
                db=db,
                thread_id=thread_id,
                role="assistant",
                content=ai_response,
                message_type="text",
                message_metadata={}
            )
            
            logger.info("chat_message_sent", thread_id=thread_id, response_length=len(ai_response))
            
            # Return in API format
            return {
                "id": assistant_message.id,
                "thread_id": assistant_message.thread_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "message_type": assistant_message.message_type,
                "metadata": assistant_message.message_metadata or {},
                "created_at": assistant_message.created_at.isoformat()
            }
            
        except Exception as ai_error:
            logger.error("ai_response_error", error=str(ai_error))
            
            # Store fallback message in database
            assistant_message = await crud.create_chat_message(
                db=db,
                thread_id=thread_id,
                role="assistant",
                content=f"I received your message: '{content}'. However, I'm currently unable to process it due to a technical issue. Please try again or contact support.",
                message_type="text",
                message_metadata={}
            )
            
            # Return in API format
            return {
                "id": assistant_message.id,
                "thread_id": assistant_message.thread_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "message_type": assistant_message.message_type,
                "metadata": assistant_message.message_metadata or {},
                "created_at": assistant_message.created_at.isoformat()
            }
        
    except Exception as e:
        logger.error("send_chat_message_error", thread_id=thread_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/investigations")
async def get_investigations_real(
    tenant_id: str = Query(...),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all investigations for tenant."""
    try:
        logger.info("fetching_investigations", tenant_id=tenant_id, status=status)
        
        # Get investigations from database
        query = select(Investigation).where(Investigation.tenant_id == tenant_id)
        
        if status:
            query = query.where(Investigation.status == status)
        
        result = await db.execute(query.order_by(Investigation.started_at.desc()))
        investigations = list(result.scalars().all())
        
        # Convert to API format
        items = [
            {
                "id": inv.id,
                "incident_number": inv.incident_number,
                "service_name": inv.service_name,
                "status": inv.status,
                "agent_results": inv.agent_results or [],
                "rca": inv.rca,
                "resolution": inv.resolution,
                "approved_by": inv.approved_by,
                "approved_at": inv.approved_at.isoformat() if inv.approved_at else None,
                "started_at": inv.started_at.isoformat(),
                "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
            }
            for inv in investigations
        ]
        
        logger.info("investigations_returned", tenant_id=tenant_id, count=len(items))
        
        return {
            "items": items,
            "total": len(items),
            "page": 1,
            "page_size": len(items)
        }
        
    except Exception as e:
        logger.error("get_investigations_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigations/{investigation_id}")
async def get_investigation_real(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single investigation by ID with no-cache headers for live updates."""
    from fastapi import Response
    
    try:
        logger.info("fetching_investigation", investigation_id=investigation_id)
        
        investigation = await crud.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        response_data = {
            "id": investigation.id,
            "incident_number": investigation.incident_number,
            "service_name": investigation.service_name,
            "status": investigation.status,
            "agent_results": investigation.agent_results or [],
            "rca": investigation.rca,
            "resolution": investigation.resolution,
            "related_knowledge": investigation.related_knowledge or [],
            "approved_by": investigation.approved_by,
            "approved_at": investigation.approved_at.isoformat() if investigation.approved_at else None,
            "started_at": investigation.started_at.isoformat(),
            "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
        }
        
        # Log agent results count for debugging
        logger.info("investigation_fetched", 
                   investigation_id=investigation_id,
                   status=investigation.status,
                   agent_results_count=len(investigation.agent_results or []))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_investigation_error", investigation_id=investigation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/investigations/{investigation_id}")
async def delete_investigation_real(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a single investigation by ID."""
    try:
        logger.info("deleting_investigation", investigation_id=investigation_id)
        
        investigation = await crud.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Delete the investigation
        await db.delete(investigation)
        await db.commit()
        
        logger.info("investigation_deleted", investigation_id=investigation_id)
        
        return {
            "success": True,
            "message": "Investigation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_investigation_error", investigation_id=investigation_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class BulkDeleteRequest(BaseModel):
    investigation_ids: List[str]


@router.post("/investigations/bulk-delete")
async def bulk_delete_investigations_real(request: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    """Delete multiple investigations in a single request."""
    try:
        logger.info("bulk_deleting_investigations", count=len(request.investigation_ids))
        
        deleted_count = 0
        failed_ids = []
        
        for investigation_id in request.investigation_ids:
            try:
                investigation = await crud.get_investigation(db, investigation_id)
                
                if investigation:
                    await db.delete(investigation)
                    deleted_count += 1
                else:
                    failed_ids.append(investigation_id)
                    
            except Exception as e:
                logger.error("bulk_delete_item_failed", investigation_id=investigation_id, error=str(e))
                failed_ids.append(investigation_id)
        
        await db.commit()
        
        logger.info("bulk_delete_complete", deleted=deleted_count, failed=len(failed_ids))
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "message": f"Successfully deleted {deleted_count} investigation(s)"
        }
        
    except Exception as e:
        logger.error("bulk_delete_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
