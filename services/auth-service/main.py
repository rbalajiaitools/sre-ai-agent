"""Auth Service - Authentication and user management."""

import uuid
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import init_db, get_db_session
from shared.models import User, Tenant
from shared.auth import create_access_token, verify_password, get_password_hash
from shared.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    logger.info("auth_service_startup", port=8009)
    init_db(settings.database)
    yield
    logger.info("auth_service_shutdown")


app = FastAPI(
    title="Auth Service",
    description="Authentication and user management",
    version="0.1.0",
    lifespan=lifespan,
)


# Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    tenant_id: str
    role: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_id: str
    role: str = "user"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    tenant_id: str
    role: str
    is_active: bool
    created_at: datetime


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    created_at: datetime


# Auth endpoints
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """User login."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "role": user.role,
    }
    access_token = create_access_token(token_data, settings.jwt)
    
    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    
    logger.info("user_login", user_id=user.id, email=user.email)
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        role=user.role,
    )


@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    request: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Register new user."""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == request.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        role=request.role,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info("user_registered", user_id=user.id, email=user.email)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=user.tenant_id,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


# User endpoints
@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=user.tenant_id,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@app.get("/api/v1/users", response_model=list[UserResponse])
async def list_users(
    tenant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List users."""
    query = select(User)
    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tenant_id=user.tenant_id,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


# Tenant endpoints
@app.post("/api/v1/tenants", response_model=TenantResponse)
async def create_tenant(
    request: TenantCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new tenant."""
    # Check if slug exists
    result = await db.execute(
        select(Tenant).where(Tenant.slug == request.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already exists"
        )
    
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=request.name,
        slug=request.slug,
        is_active=True,
        settings={},
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    logger.info("tenant_created", tenant_id=tenant.id, slug=tenant.slug)
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
    )


@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get tenant by ID."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
    )


@app.post("/api/v1/bootstrap")
async def bootstrap(db: AsyncSession = Depends(get_db_session)):
    """Bootstrap initial tenant and admin user."""
    # Check if already bootstrapped
    result = await db.execute(select(Tenant))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System already bootstrapped"
        )
    
    # Create default tenant
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Default Organization",
        slug="default",
        is_active=True,
        settings={},
    )
    db.add(tenant)
    
    # Create admin user
    admin = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email="admin@astra.ai",
        password_hash=get_password_hash("admin123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    
    await db.commit()
    
    logger.info("system_bootstrapped", tenant_id=tenant.id, admin_id=admin.id)
    
    return {
        "message": "System bootstrapped successfully",
        "tenant_id": tenant.id,
        "admin_email": admin.email,
        "admin_password": "admin123",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "auth-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
