"""Eraser Service - Architecture diagram generation."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

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
    logger.info("eraser_service_startup", port=8010)
    init_db(settings.database)
    yield
    logger.info("eraser_service_shutdown")


app = FastAPI(
    title="Eraser Service",
    description="Architecture diagram generation via Eraser.io",
    version="0.1.0",
    lifespan=lifespan,
)


class DiagramRequest(BaseModel):
    tenant_id: str
    diagram_type: str
    services: list[str]


@app.post("/api/v1/architecture/generate")
async def generate_diagram(request: DiagramRequest):
    """Generate architecture diagram."""
    logger.info("generate_diagram", tenant_id=request.tenant_id, type=request.diagram_type)
    
    return {
        "diagram_url": "https://eraser.io/diagram/example",
        "diagram_type": request.diagram_type,
        "services": request.services
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "eraser-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
