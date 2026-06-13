"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
from loguru import logger

from .services.auth_service import auth_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = auth_service.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_auth = auth_service.get_user_auth(user_id)
    if not user_auth or not user_auth.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "email": payload.get("email"),
        "role": payload.get("role", "user")
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user (alias for get_current_user with explicit naming)
    """
    return current_user


def require_role(required_role: str) -> Callable:
    """
    Dependency factory for role-based access control
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "user")
        
        if user_role == "admin":
            return current_user
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_roles(*allowed_roles: str) -> Callable:
    """
    Dependency factory for multiple role-based access control
    """
    async def roles_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "user")
        
        if user_role == "admin":
            return current_user
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return roles_checker


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None
    Useful for endpoints that work both with and without authentication
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token, token_type="access")
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user_auth = auth_service.get_user_auth(user_id)
        if not user_auth or not user_auth.get("is_active", True):
            return None
        
        return {
            "user_id": user_id,
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
    except Exception as e:
        logger.warning(f"Error getting optional user: {str(e)}")
        return None
