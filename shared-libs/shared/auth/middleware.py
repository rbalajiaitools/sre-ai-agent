"""Authentication middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from shared.auth.jwt import verify_token
from shared.config import JWTSettings

security = HTTPBearer()


class JWTAuthMiddleware:
    """JWT authentication middleware."""
    
    def __init__(self, settings: JWTSettings):
        """Initialize middleware.
        
        Args:
            settings: JWT settings
        """
        self.settings = settings
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Verify JWT token from request.
        
        Args:
            request: FastAPI request
            credentials: HTTP authorization credentials
            
        Returns:
            Token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        payload = verify_token(token, self.settings)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user info to request state
        request.state.user_id = payload.get("sub")
        request.state.tenant_id = payload.get("tenant_id")
        request.state.user_email = payload.get("email")
        request.state.user_role = payload.get("role")
        
        return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: JWTSettings = Depends()
) -> dict:
    """Get current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        settings: JWT settings
        
    Returns:
        User payload from token
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = verify_token(token, settings)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_role(required_role: str):
    """Dependency to require specific role.
    
    Args:
        required_role: Required role
        
    Returns:
        Dependency function
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role")
        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user
    
    return role_checker
