"""FastAPI dependency injection functions."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_tenant_id(
    x_tenant_id: Annotated[str, Header(description="Tenant ID")]
) -> UUID:
    """Extract and validate tenant ID from request headers.

    Args:
        x_tenant_id: Tenant ID from X-Tenant-ID header

    Returns:
        Validated tenant UUID

    Raises:
        HTTPException: If tenant ID is invalid
    """
    try:
        tenant_id = UUID(x_tenant_id)
        logger.debug("tenant_id_extracted", tenant_id=str(tenant_id))
        return tenant_id
    except ValueError as e:
        logger.error("invalid_tenant_id", tenant_id=x_tenant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format",
        )


async def get_current_settings() -> Settings:
    """Get current application settings.

    Returns:
        Application settings instance
    """
    return get_settings()


def get_llm():
    """Get LLM instance.
    
    Returns:
        LLM instance
    """
    from app.core.llm import LLMFactory
    settings = get_settings()
    return LLMFactory.create_llm(settings.llm)


def get_provider_registry():
    """Get provider registry.
    
    Returns:
        Provider registry instance
    """
    from app.adapters.registry import ProviderRegistry
    return ProviderRegistry()


def get_knowledge_graph():
    """Get knowledge graph instance.
    
    Returns:
        Knowledge graph instance (stub)
    """
    # Stub implementation - would connect to Neo4j in production
    return None


def get_incident_memory():
    """Get incident memory instance.
    
    Returns:
        Incident memory instance (stub)
    """
    # Stub implementation - would connect to vector DB in production
    return None


def get_servicenow_connector():
    """Get ServiceNow connector instance.
    
    Returns:
        ServiceNow connector instance (stub)
    """
    # Stub implementation - would be properly configured in production
    return None


# Type aliases for dependency injection
TenantIdDep = Annotated[UUID, Depends(get_tenant_id)]
SettingsDep = Annotated[Settings, Depends(get_current_settings)]
