"""
FastAPI dependencies for authentication, database, and services.
"""

from typing import AsyncGenerator, Any, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.database import get_db, db_manager
from ..core.redis import redis_manager, cache_manager, session_manager
from ..core.config import settings
from ..core.security import security
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.authorization_service import AuthorizationService

# HTTP Bearer for token authentication
security_bearer = HTTPBearer()


async def get_redis():
    """Get Redis connection."""
    if not redis_manager.redis_client:
        await redis_manager.connect()
    return redis_manager.redis_client


async def get_cache():
    """Get cache manager."""
    return cache_manager


async def get_sessions():
    """Get session manager."""
    return session_manager


async def get_auth_service(
    db: Any = Depends(get_db),
    cache = Depends(get_cache),
    sessions = Depends(get_sessions)
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db, cache, sessions)


async def get_authorization_service(
    cache = Depends(get_cache)
) -> AuthorizationService:
    """Get authorization service instance."""
    return AuthorizationService(cache)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        auth_service: Authentication service
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user = await auth_service.get_user_from_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current verified user
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


def require_permission(permission: str):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        authz_service: AuthorizationService = Depends(get_authorization_service)
    ) -> User:
        """Check if user has required permission."""
        # Extract resource information from request
        resource_type = request.url.path.split("/")[1] if len(request.url.path.split("/")) > 1 else "unknown"
        resource_id = request.path_params.get("id")
        
        has_permission = await authz_service.check_permission(
            user_id=current_user.id,
            permission=permission,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return permission_dependency


def require_role(role: str):
    """
    Decorator to require specific role.
    
    Args:
        role: Required role
        
    Returns:
        Dependency function
    """
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        """Check if user has required role."""
        has_role = await auth_service.user_has_role(current_user.id, role)
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        
        return current_user
    
    return role_dependency


async def get_student_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user if they are a student."""
    is_student = await auth_service.user_has_role(current_user.id, "STUDENT")
    if not is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user


async def get_lecturer_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user if they are a lecturer."""
    is_lecturer = await auth_service.user_has_role(current_user.id, "LECTURER")
    if not is_lecturer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lecturer access required"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user if they are an administrator."""
    is_admin = await auth_service.user_has_role(current_user.id, "ADMINISTRATOR")
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


async def get_exam_officer_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user if they are an examination officer."""
    is_exam_officer = await auth_service.user_has_role(current_user.id, "EXAM_OFFICER")
    if not is_exam_officer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Examination officer access required"
        )
    return current_user


async def validate_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    sessions = Depends(get_sessions)
) -> User:
    """
    Validate user session for security.
    
    Args:
        request: FastAPI request
        current_user: Current authenticated user
        sessions: Session manager
        
    Returns:
        User: Validated user
        
    Raises:
        HTTPException: If session is invalid
    """
    # Get session token from request
    session_token = request.headers.get("X-Session-Token")
    if not session_token:
        session_token = request.cookies.get(settings.session_cookie_name)
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token provided"
        )
    
    # Validate session
    session_data = await sessions.get_session(session_token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Check session belongs to current user
    if session_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session validation failed"
        )
    
    # Check device fingerprint
    device_fingerprint = security.generate_device_fingerprint(
        request.headers.get("User-Agent", ""),
        request.client.host if request.client else "unknown"
    )
    
    if session_data.get("device_fingerprint") != device_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device fingerprint mismatch"
        )
    
    return current_user
