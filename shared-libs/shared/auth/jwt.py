"""JWT token utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.config import JWTSettings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: dict,
    settings: JWTSettings,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token.
    
    Args:
        data: Token payload data
        settings: JWT settings
        expires_delta: Optional expiration delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, settings: JWTSettings) -> Optional[dict]:
    """Verify JWT token.
    
    Args:
        token: JWT token to verify
        settings: JWT settings
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """Hash password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
