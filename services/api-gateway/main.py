"""API Gateway - Main entry point."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.logging import setup_logging, get_logger, bind_context, clear_context
from shared.database import init_db

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)

# Service registry
SERVICE_REGISTRY = {
    "/api/v1/auth": "http://localhost:8009",
    "/api/v1/users": "http://localhost:8009",
    "/api/v1/tenants": "http://localhost:8009",
    "/api/v1/bootstrap": "http://localhost:8009",
    "/api/v1/alerts": "http://localhost:8001",
    "/api/v1/incidents": "http://localhost:8001",
    "/api/v1/webhooks": "http://localhost:8001",
    "/api/v1/investigations": "http://localhost:8002",
    "/api/v1/postmortems": "http://localhost:8002",
    "/api/v1/ai": "http://localhost:8003",
    "/api/v1/services": "http://localhost:8004",
    "/api/v1/topology": "http://localhost:8004",
    "/api/v1/graph": "http://localhost:8004",
    "/api/v1/actions": "http://localhost:8005",
    "/api/v1/policies": "http://localhost:8006",
    "/api/v1/connectors": "http://localhost:8006",
    "/api/v1/audit": "http://localhost:8006",
    "/api/v1/admin": "http://localhost:8006",
    "/api/v1/notifications": "http://localhost:8007",
    "/api/v1/analytics": "http://localhost:8008",
    "/api/v1/evaluations": "http://localhost:8008",
    "/api/v1/feedback": "http://localhost:8008",
    "/api/v1/architecture": "http://localhost:8010",
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("api_gateway_startup", port=8000)
    
    # Initialize database for audit logs
    init_db(settings.database)
    
    yield
    
    logger.info("api_gateway_shutdown")


app = FastAPI(
    title="CloudScore ASTRA AI - API Gateway",
    description="API Gateway with routing and audit logging",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID and logging context."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    bind_context(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_context()


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Audit logging for mutations."""
    response = await call_next(request)
    
    # Log mutations (POST, PUT, PATCH, DELETE)
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        # Extract user info from request state (set by auth service)
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        if user_id and tenant_id:
            logger.info(
                "audit_log",
                user_id=user_id,
                tenant_id=tenant_id,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
            )
    
    return response


def get_upstream_service(path: str) -> str | None:
    """Get upstream service URL for path."""
    for prefix, service_url in SERVICE_REGISTRY.items():
        if path.startswith(prefix):
            return service_url
    return None


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(request: Request, path: str):
    """Proxy requests to upstream services."""
    full_path = f"/{path}"
    
    # Get upstream service
    upstream_url = get_upstream_service(full_path)
    
    if not upstream_url:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Service not found",
                "path": full_path,
                "request_id": request.state.request_id,
            }
        )
    
    # Build target URL
    target_url = f"{upstream_url}{full_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Forward headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers["X-Request-ID"] = request.state.request_id
    headers["X-Forwarded-For"] = request.client.host
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Forward request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
            
    except httpx.ConnectError:
        logger.error("upstream_connection_error", upstream_url=upstream_url)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service unavailable",
                "service": upstream_url,
                "request_id": request.state.request_id,
            }
        )
    except Exception as e:
        logger.error("proxy_error", error=str(e), upstream_url=upstream_url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": request.state.request_id,
            }
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
