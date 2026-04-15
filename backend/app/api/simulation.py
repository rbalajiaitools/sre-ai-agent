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
    duration_seconds: int,
    db: AsyncSession
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
        
        # Simulate metrics
        requests_per_second = int(100 * multiplier)
        error_rate = 0.05 * multiplier if scenario_type == 'error' else 0.01
        
        total_requests = requests_per_second * duration_seconds
        total_errors = int(total_requests * error_rate)
        avg_latency = 50 * multiplier if scenario_type == 'latency' else 50
        
        # Update metrics
        _active_simulations[simulation_id]['metrics'] = {
            'requests_sent': total_requests,
            'errors_generated': total_errors,
            'avg_latency_ms': int(avg_latency)
        }
        
        # Create incident if severity is high or critical
        incident_number = None
        if severity in ['high', 'critical']:
            # Create incident in database
            incident_data = {
                'sys_id': str(uuid.uuid4()),
                'number': f'INC{str(uuid.uuid4())[:8].upper()}',
                'short_description': f'{scenario_type.title()} issue on {service_id}',
                'description': f'Simulated {scenario_type} with {severity} severity on {service_id}. Error rate: {error_rate*100:.1f}%',
                'priority': 1 if severity == 'critical' else 2,
                'state': '1',  # New
                'category': 'Performance',
                'subcategory': scenario_type.title(),
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
                    'severity': severity
                },
                'synced_at': start_time
            }
            
            await crud.create_incident(db, tenant_id, incident_data)
            incident_number = incident_data['number']
            
            _active_simulations[simulation_id]['incident_number'] = incident_number
            
            logger.info("simulation_incident_created", simulation_id=simulation_id, incident_number=incident_number)
        
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
            request.duration_seconds,
            db
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
