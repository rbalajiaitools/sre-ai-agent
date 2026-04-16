"""Simulation API endpoints for triggering load/errors on services."""

import uuid
from datetime import datetime, timedelta
from typing import List
import asyncio

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db import crud
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["simulation"])

# In-memory storage for simulations (in production, use database)
_active_simulations = {}
_simulation_history = []


class Service(BaseModel):
    id: str
    name: str
    type: str
    status: str
    current_load: float
    error_rate: float


class SimulationScenario(BaseModel):
    id: str
    name: str
    description: str
    service_id: str
    type: str
    severity: str
    duration_seconds: int
    parameters: dict


class SimulationRun(BaseModel):
    id: str
    scenario_id: str
    service_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    incident_created: str | None = None
    metrics: dict


class TriggerSimulationRequest(BaseModel):
    tenant_id: str
    service_id: str
    scenario_type: str  # load, error, latency, crash
    severity: str  # low, medium, high, critical
    duration_seconds: int
    parameters: dict | None = None


class TriggerSimulationResponse(BaseModel):
    simulation_id: str
    message: str
    incident_number: str | None = None


class StopSimulationRequest(BaseModel):
    tenant_id: str
    simulation_id: str


@router.get("/simulation/services")
async def get_services(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> List[Service]:
    """Get list of services that can be simulated."""
    try:
        logger.info("fetching_simulation_services", tenant_id=tenant_id)
        
        # Return known services from topology
        services = [
            Service(
                id="s3-demo-dashboard",
                name="S3 Demo Dashboard",
                type="static-website",
                status="healthy",
                current_load=15.0,
                error_rate=0.0
            ),
            Service(
                id="api-gateway",
                name="API Gateway",
                type="api",
                status="healthy",
                current_load=45.0,
                error_rate=0.1
            ),
            Service(
                id="payment-service",
                name="Payment Service",
                type="api",
                status="healthy",
                current_load=62.0,
                error_rate=0.3
            ),
            Service(
                id="auth-service",
                name="Auth Service",
                type="api",
                status="healthy",
                current_load=38.0,
                error_rate=0.05
            ),
            Service(
                id="postgres-primary",
                name="PostgreSQL Primary",
                type="database",
                status="healthy",
                current_load=55.0,
                error_rate=0.0
            ),
            Service(
                id="redis-cache",
                name="Redis Cache",
                type="cache",
                status="healthy",
                current_load=28.0,
                error_rate=0.0
            ),
        ]
        
        return services
        
    except Exception as e:
        logger.error("get_services_error", tenant_id=tenant_id, error=str(e))
        raise


@router.get("/simulation/runs")
async def get_simulation_runs(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> List[SimulationRun]:
    """Get simulation run history."""
    try:
        logger.info("fetching_simulation_runs", tenant_id=tenant_id)
        
        # Return simulation history
        runs = []
        for run_data in _simulation_history:
            if run_data.get('tenant_id') == tenant_id:
                runs.append(SimulationRun(
                    id=run_data['id'],
                    scenario_id=run_data['scenario_id'],
                    service_id=run_data['service_id'],
                    status=run_data['status'],
                    started_at=run_data['started_at'],
                    completed_at=run_data.get('completed_at'),
                    incident_created=run_data.get('incident_number'),
                    metrics=run_data.get('metrics', {
                        'requests_sent': 0,
                        'errors_generated': 0,
                        'avg_latency_ms': 0
                    })
                ))
        
        # Add active simulations
        for sim_id, sim_data in _active_simulations.items():
            if sim_data.get('tenant_id') == tenant_id:
                runs.append(SimulationRun(
                    id=sim_id,
                    scenario_id=sim_data['scenario_id'],
                    service_id=sim_data['service_id'],
                    status='running',
                    started_at=sim_data['started_at'],
                    incident_created=sim_data.get('incident_number'),
                    metrics=sim_data.get('metrics', {
                        'requests_sent': 0,
                        'errors_generated': 0,
                        'avg_latency_ms': 0
                    })
                ))
        
        # Sort by started_at descending
        runs.sort(key=lambda x: x.started_at, reverse=True)
        return runs[:20]  # Return last 20 runs
        
    except Exception as e:
        logger.error("get_simulation_runs_error", tenant_id=tenant_id, error=str(e))
        raise


async def run_simulation(
    simulation_id: str,
    tenant_id: str,
    service_id: str,
    scenario_type: str,
    severity: str,
    duration_seconds: int
):
    """Background task to run simulation."""
    try:
        logger.info("simulation_started", simulation_id=simulation_id, service_id=service_id, scenario_type=scenario_type)
        
        # Simulate for the duration
        start_time = datetime.utcnow()
        
        # Calculate metrics based on severity
        severity_multipliers = {
            'low': 1.0,
            'medium': 2.0,
            'high': 3.0,
            'critical': 5.0
        }
        multiplier = severity_multipliers.get(severity, 1.0)
        
        # For S3 Demo Dashboard, actually check if the website is accessible
        actual_error_detected = False
        actual_error_details = ""
        
        if service_id == 's3-demo-dashboard':
            try:
                import httpx
                website_url = "http://cloudscore-demo-dashboard-181080507119.s3-website-us-east-1.amazonaws.com"
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    try:
                        response = await client.get(website_url)
                        if response.status_code >= 400:
                            actual_error_detected = True
                            actual_error_details = f"Website returned {response.status_code} error"
                            logger.warning("s3_website_error_detected", 
                                         simulation_id=simulation_id,
                                         status_code=response.status_code)
                        else:
                            logger.info("s3_website_accessible", 
                                      simulation_id=simulation_id,
                                      status_code=response.status_code)
                    except Exception as http_error:
                        actual_error_detected = True
                        actual_error_details = f"Website unreachable: {str(http_error)}"
                        logger.warning("s3_website_unreachable", 
                                     simulation_id=simulation_id,
                                     error=str(http_error))
            except Exception as check_error:
                logger.warning("s3_website_check_failed", 
                             simulation_id=simulation_id,
                             error=str(check_error))
        
        # Simulate metrics based on actual error or fake scenario
        if actual_error_detected:
            # Real error detected - use realistic metrics
            requests_per_second = int(50 * multiplier)  # Lower traffic due to errors
            error_rate = 0.95  # 95% error rate for real outage
            total_requests = requests_per_second * duration_seconds
            total_errors = int(total_requests * error_rate)
            avg_latency = 200  # Higher latency due to errors
        else:
            # Fake scenario - use simulated metrics
            requests_per_second = int(100 * multiplier)
            error_rate = 0.05 * multiplier if scenario_type == 'error' else 0.01
            total_requests = requests_per_second * duration_seconds
            total_errors = int(total_requests * error_rate)
            avg_latency = 50 * multiplier if scenario_type == 'latency' else 50
        
        # Update metrics
        _active_simulations[simulation_id]['metrics'] = {
            'requests_sent': total_requests,
            'errors_generated': total_errors,
            'avg_latency_ms': int(avg_latency),
            'actual_error_detected': actual_error_detected,
            'error_details': actual_error_details
        }
        
        # Create incident if severity is high or critical
        incident_number = None
        if severity in ['high', 'critical']:
            # Create a new database session for the background task
            from app.db.base import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Get ServiceNow integration for this tenant
                integrations = await crud.get_integrations(db, tenant_id, "servicenow")
                if not integrations:
                    logger.warning("no_servicenow_integration_for_simulation", tenant_id=tenant_id)
                    # Continue without creating incident
                else:
                    integration_id = integrations[0].id
                    
                    # Create incident description based on service type and actual error
                    if service_id == 's3-demo-dashboard':
                        if actual_error_detected:
                            # Real error detected - create detailed incident
                            short_desc = f'S3 Website CRITICAL - Demo Dashboard Completely Inaccessible'
                            description = f'''REAL OUTAGE DETECTED on S3 static website (Demo Dashboard).

Severity: {severity.upper()}
Service: S3 Demo Dashboard
Issue Type: {scenario_type.title()}
Error Rate: {error_rate*100:.1f}%

ACTUAL ERROR DETECTED:
{actual_error_details}

Website URL: http://cloudscore-demo-dashboard-181080507119.s3-website-us-east-1.amazonaws.com

Symptoms:
- Website returning errors or completely unreachable
- Users unable to access dashboard
- High 4xx/5xx error rates detected
- Possible S3 configuration issue (public access, bucket policy, or website hosting)

Impact:
- Dashboard COMPLETELY UNAVAILABLE to all users
- Monitoring visibility lost
- Critical business impact

Recommended Immediate Actions:
1. Check S3 bucket public access block settings
2. Verify bucket policy allows public read access
3. Confirm website hosting is enabled
4. Review recent S3 configuration changes
5. Check CloudWatch alarms and metrics'''
                        else:
                            # Simulated scenario
                            short_desc = f'S3 Website {scenario_type.title()} - Demo Dashboard Performance Issue'
                            description = f'''Simulated {scenario_type} issue on S3 static website (Demo Dashboard).

Severity: {severity.upper()}
Service: S3 Demo Dashboard
Issue Type: {scenario_type.title()}
Error Rate: {error_rate*100:.1f}%

Note: This is a SIMULATED incident for testing. Website appears accessible.

Symptoms:
- Potential performance degradation
- Simulated error rate increase
- Testing incident response workflow

Recommended Actions:
1. Verify S3 bucket configuration
2. Check CloudWatch logs and metrics
3. Review website hosting settings'''
                    else:
                        short_desc = f'{scenario_type.title()} issue on {service_id}'
                        description = f'Simulated {scenario_type} with {severity} severity on {service_id}. Error rate: {error_rate*100:.1f}%'
                    
                    try:
                        # Get ServiceNow config
                        sn_integration = integrations[0]
                        config_dict = crud.decrypt_integration_config(sn_integration)
                        
                        # Create incident in ServiceNow first
                        import httpx
                        
                        snow_incident_data = {
                            "short_description": short_desc,
                            "description": description,
                            "urgency": "1" if severity == 'critical' else "2",
                            "impact": "1" if severity == 'critical' else "2",
                            "category": "Infrastructure",
                            "subcategory": "S3" if service_id == 's3-demo-dashboard' else scenario_type.title(),
                            "cmdb_ci": service_id,
                            "assignment_group": "SRE Team",
                        }
                        
                        # Call ServiceNow API to create incident
                        url = f"https://{config_dict['instance']}.service-now.com/api/now/table/incident"
                        auth = (config_dict['username'], config_dict['password'])
                        headers = {
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.post(url, json=snow_incident_data, auth=auth, headers=headers, timeout=30.0)
                            
                            if response.status_code == 201:
                                snow_response = response.json()
                                snow_incident_number = snow_response['result']['number']
                                snow_sys_id = snow_response['result']['sys_id']
                                
                                # Now create in local database with ServiceNow details
                                incident_data = {
                                    'sys_id': snow_sys_id,
                                    'number': snow_incident_number,
                                    'short_description': short_desc,
                                    'description': description,
                                    'priority': 1 if severity == 'critical' else 2,
                                    'state': '1',  # New
                                    'category': snow_incident_data['category'],
                                    'subcategory': snow_incident_data['subcategory'],
                                    'cmdb_ci': service_id,
                                    'assignment_group': 'SRE Team',
                                    'assigned_to': None,
                                    'opened_at': start_time,
                                    'updated_at': start_time,
                                    'resolved_at': None,
                                    'investigation_status': None,
                                    'investigation_id': None,
                                    'raw_data': {
                                        'simulation_id': simulation_id,
                                        'scenario_type': scenario_type,
                                        'severity': severity,
                                        'service_type': 'static-website',
                                        'actual_error_detected': actual_error_detected,
                                        'error_details': actual_error_details
                                    },
                                    'synced_at': start_time
                                }
                                
                                # Create incident in local database
                                await crud.upsert_incident(
                                    db=db,
                                    tenant_id=tenant_id,
                                    integration_id=integration_id,
                                    incident_data=incident_data
                                )
                                
                                incident_number = snow_incident_number
                                _active_simulations[simulation_id]['incident_number'] = snow_incident_number
                                
                                logger.info("simulation_incident_created_in_servicenow", 
                                          simulation_id=simulation_id, 
                                          snow_incident_number=snow_incident_number,
                                          actual_error=actual_error_detected)
                            else:
                                logger.warning("failed_to_create_servicenow_incident", 
                                             status=response.status_code,
                                             response=response.text)
                        
                    except Exception as snow_error:
                        logger.error("servicenow_incident_creation_failed", error=str(snow_error))
                        import traceback
                        logger.error("incident_creation_traceback", traceback=traceback.format_exc())
        
        # Wait for duration
        await asyncio.sleep(duration_seconds)
        
        # Mark as completed
        completed_at = datetime.utcnow()
        
        # Move to history
        sim_data = _active_simulations.pop(simulation_id)
        sim_data['status'] = 'completed'
        sim_data['completed_at'] = completed_at
        _simulation_history.append(sim_data)
        
        logger.info("simulation_completed", simulation_id=simulation_id, duration=duration_seconds)
        
    except Exception as e:
        logger.error("simulation_error", simulation_id=simulation_id, error=str(e))
        import traceback
        logger.error("simulation_error_traceback", traceback=traceback.format_exc())
        # Mark as failed
        if simulation_id in _active_simulations:
            sim_data = _active_simulations.pop(simulation_id)
            sim_data['status'] = 'failed'
            sim_data['completed_at'] = datetime.utcnow()
            _simulation_history.append(sim_data)


@router.post("/simulation/trigger")
async def trigger_simulation(
    request: TriggerSimulationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> TriggerSimulationResponse:
    """Trigger a simulation scenario."""
    try:
        logger.info("triggering_simulation", 
                   tenant_id=request.tenant_id,
                   service_id=request.service_id,
                   scenario_type=request.scenario_type,
                   severity=request.severity)
        
        # Generate IDs
        simulation_id = str(uuid.uuid4())
        scenario_id = f"{request.scenario_type}-{request.severity}"
        
        # Store simulation data
        sim_data = {
            'id': simulation_id,
            'tenant_id': request.tenant_id,
            'scenario_id': scenario_id,
            'service_id': request.service_id,
            'scenario_type': request.scenario_type,
            'severity': request.severity,
            'duration_seconds': request.duration_seconds,
            'started_at': datetime.utcnow(),
            'status': 'running',
            'metrics': {
                'requests_sent': 0,
                'errors_generated': 0,
                'avg_latency_ms': 0
            }
        }
        
        _active_simulations[simulation_id] = sim_data
        
        # Start simulation in background
        background_tasks.add_task(
            run_simulation,
            simulation_id,
            request.tenant_id,
            request.service_id,
            request.scenario_type,
            request.severity,
            request.duration_seconds
        )
        
        return TriggerSimulationResponse(
            simulation_id=simulation_id,
            message=f"Simulation started for {request.service_id}",
            incident_number=None
        )
        
    except Exception as e:
        logger.error("trigger_simulation_error", error=str(e))
        raise


@router.post("/simulation/stop")
async def stop_simulation(
    request: StopSimulationRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Stop a running simulation."""
    try:
        logger.info("stopping_simulation", simulation_id=request.simulation_id)
        
        if request.simulation_id in _active_simulations:
            sim_data = _active_simulations.pop(request.simulation_id)
            sim_data['status'] = 'completed'
            sim_data['completed_at'] = datetime.utcnow()
            _simulation_history.append(sim_data)
            
            return {"message": "Simulation stopped successfully"}
        else:
            return {"message": "Simulation not found or already completed"}
        
    except Exception as e:
        logger.error("stop_simulation_error", error=str(e))
        raise
