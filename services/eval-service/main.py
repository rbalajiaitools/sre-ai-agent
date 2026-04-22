"""Eval Service - RCA quality scoring and analytics."""

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
    logger.info("eval_service_startup", port=8008)
    init_db(settings.database)
    yield
    logger.info("eval_service_shutdown")


app = FastAPI(
    title="Eval Service",
    description="RCA quality scoring and analytics",
    version="0.1.0",
    lifespan=lifespan,
)


class EvaluationRequest(BaseModel):
    investigation_id: str
    tenant_id: str


@app.post("/api/v1/evaluations")
async def evaluate_investigation(request: EvaluationRequest):
    """Evaluate investigation quality."""
    logger.info("evaluate_investigation", investigation_id=request.investigation_id)
    
    return {
        "investigation_id": request.investigation_id,
        "quality_score": 0.85,
        "metrics": {
            "accuracy": 0.9,
            "completeness": 0.8,
            "timeliness": 0.85
        }
    }


@app.get("/api/v1/analytics")
async def get_analytics(tenant_id: str):
    """Get analytics dashboard."""
    logger.info("get_analytics", tenant_id=tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "total_investigations": 100,
        "avg_resolution_time": 15.5,
        "success_rate": 0.92
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "eval-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
