"""Base Pydantic models for the application."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {}
        }
    }


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantMixin(BaseModel):
    """Mixin for tenant-scoped resources."""

    tenant_id: UUID = Field(..., description="Tenant identifier")


class BaseEntity(BaseSchema, TimestampMixin):
    """Base entity with ID and timestamps."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")


class TenantEntity(BaseEntity, TenantMixin):
    """Base entity for tenant-scoped resources."""

    pass


class ErrorResponse(BaseSchema):
    """Standard error response model."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class SuccessResponse(BaseSchema):
    """Standard success response model."""

    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(default=None, description="Response data")
