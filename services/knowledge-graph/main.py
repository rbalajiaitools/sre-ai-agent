"""Knowledge Graph - Service topology and dependencies."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from shared.config import get_settings
from shared.database import init_db
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("knowledge_graph_startup", port=8004)
    init_db(settings.database)
    yield
    logger.info("knowledge_graph_shutdown")


app = FastAPI(
    title="Knowledge Graph",
    description="Service topology, dependencies, and blast radius analysis",
    version="0.1.0",
    lifespan=lifespan,
)


class ServiceNode(BaseModel):
    id: str
    name: str
    type: str
    health_score: float


class DependencyEdge(BaseModel):
    from_service: str
    to_service: str
    dependency_type: str


class TopologyResponse(BaseModel):
    services: list[ServiceNode]
    dependencies: list[DependencyEdge]


class BlastRadiusRequest(BaseModel):
    service_id: str
    tenant_id: str


class ChangeRiskRequest(BaseModel):
    service_id: str
    change_type: str
    tenant_id: str


class ServiceCreate(BaseModel):
    tenant_id: str
    name: str
    service_type: str
    description: Optional[str] = None
    metadata: dict = {}


class ServiceResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    service_type: str
    health_score: float
    status: str


class DependencyCreate(BaseModel):
    tenant_id: str
    from_service_id: str
    to_service_id: str
    dependency_type: str


# In-memory storage for demo (replace with database in production)
services_db = {}
dependencies_db = []


@app.post("/api/v1/services", response_model=ServiceResponse)
async def register_service(request: ServiceCreate):
    """Register a new service."""
    import uuid
    
    service_id = str(uuid.uuid4())
    service = {
        "id": service_id,
        "tenant_id": request.tenant_id,
        "name": request.name,
        "service_type": request.service_type,
        "description": request.description,
        "metadata": request.metadata,
        "health_score": 1.0,
        "status": "healthy",
    }
    
    services_db[service_id] = service
    logger.info("service_registered", service_id=service_id, name=request.name)
    
    return ServiceResponse(**service)


@app.get("/api/v1/services", response_model=list[ServiceResponse])
async def list_services(tenant_id: Optional[str] = None):
    """List all services."""
    services = list(services_db.values())
    
    if tenant_id:
        services = [s for s in services if s["tenant_id"] == tenant_id]
    
    return [ServiceResponse(**s) for s in services]


@app.get("/api/v1/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str):
    """Get service by ID."""
    service = services_db.get(service_id)
    
    if not service:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return ServiceResponse(**service)


@app.post("/api/v1/dependencies")
async def create_dependency(request: DependencyCreate):
    """Create service dependency."""
    dependency = {
        "tenant_id": request.tenant_id,
        "from_service_id": request.from_service_id,
        "to_service_id": request.to_service_id,
        "dependency_type": request.dependency_type,
    }
    
    dependencies_db.append(dependency)
    logger.info("dependency_created", from_service=request.from_service_id, to_service=request.to_service_id)
    
    return {"message": "Dependency created successfully", "dependency": dependency}


@app.get("/api/v1/dependencies")
async def list_dependencies(tenant_id: Optional[str] = None):
    """List all dependencies."""
    deps = dependencies_db
    
    if tenant_id:
        deps = [d for d in deps if d["tenant_id"] == tenant_id]
    
    return deps


@app.get("/api/v1/graph/topology", response_model=TopologyResponse)
async def get_topology(tenant_id: Optional[str] = None):
    """Get service topology."""
    logger.info("get_topology", tenant_id=tenant_id)
    
    # Simulated topology
    services = [
        ServiceNode(id="svc-1", name="user-service", type="api", health_score=0.95),
        ServiceNode(id="svc-2", name="auth-service", type="api", health_score=0.98),
        ServiceNode(id="svc-3", name="database", type="database", health_score=0.92),
    ]
    
    dependencies = [
        DependencyEdge(from_service="svc-1", to_service="svc-2", dependency_type="sync"),
        DependencyEdge(from_service="svc-1", to_service="svc-3", dependency_type="sync"),
    ]
    
    return TopologyResponse(services=services, dependencies=dependencies)


@app.post("/api/v1/graph/blast-radius")
async def calculate_blast_radius(request: BlastRadiusRequest):
    """Calculate blast radius for service."""
    logger.info("blast_radius", service_id=request.service_id)
    
    return {
        "service_id": request.service_id,
        "affected_services": ["svc-1", "svc-2"],
        "impact_score": 0.75,
        "estimated_users_affected": 1000
    }


@app.post("/api/v1/graph/change-risk")
async def assess_change_risk(request: ChangeRiskRequest):
    """Assess risk of change to service."""
    logger.info("change_risk", service_id=request.service_id, change_type=request.change_type)
    
    return {
        "service_id": request.service_id,
        "change_type": request.change_type,
        "risk_score": 0.65,
        "risk_level": "medium",
        "recommendations": ["Deploy during low-traffic window", "Enable feature flag"]
    }


@app.get("/api/v1/graph/health-dashboard")
async def health_dashboard(tenant_id: Optional[str] = None):
    """Get service health dashboard."""
    logger.info("health_dashboard", tenant_id=tenant_id)
    
    return {
        "services": [
            {"name": "user-service", "health_score": 0.95, "status": "healthy"},
            {"name": "auth-service", "health_score": 0.98, "status": "healthy"},
            {"name": "database", "health_score": 0.92, "status": "degraded"},
        ],
        "overall_health": 0.95
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "knowledge-graph"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
