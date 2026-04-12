"""FastAPI application entrypoint."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import SREAgentException
from app.core.logging import bind_context, clear_context, get_logger, setup_logging

settings = get_settings()

# Setup logging
setup_logging(log_level=settings.app.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app.app_name,
        environment=settings.app.app_env,
    )

    yield

    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="CloudScore Astra AI",
    description="Enterprise-grade multi-tenant SaaS platform for CloudScore Astra AI",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=f"{settings.app.api_v1_prefix}/docs",
    redoc_url=f"{settings.app.api_v1_prefix}/redoc",
    openapi_url=f"{settings.app.api_v1_prefix}/openapi.json",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to all requests and bind to logging context.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response with X-Request-ID header
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Bind request context to logger
    tenant_id = request.headers.get("x-tenant-id")
    bind_context(
        request_id=request_id,
        tenant_id=tenant_id,
        path=request.url.path,
        method=request.method,
    )

    logger.info("request_started")

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info("request_completed", status_code=response.status_code)

        return response
    finally:
        clear_context()


@app.exception_handler(SREAgentException)
async def sre_agent_exception_handler(
    request: Request, exc: SREAgentException
) -> JSONResponse:
    """Handle custom SRE Agent exceptions.

    Args:
        request: Incoming request
        exc: SRE Agent exception

    Returns:
        JSON response with error details
    """
    logger.error(
        "sre_agent_exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            **exc.to_dict(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors.

    Args:
        request: Incoming request
        exc: Validation error

    Returns:
        JSON response with validation error details
    """
    logger.error("validation_error", errors=exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()},
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: Incoming request
        exc: Exception

    Returns:
        JSON response with error details
    """
    logger.exception("unexpected_error", error=str(exc))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.app.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint redirect.

    Returns:
        Redirect message
    """
    return {
        "message": "SRE AI Agent API",
        "docs": f"{settings.app.api_v1_prefix}/docs",
    }
