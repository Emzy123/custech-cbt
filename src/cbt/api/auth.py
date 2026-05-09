"""
Authentication API endpoints for login, registration, and token management.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from ..models.user import User
from ..schemas.auth import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    RegisterRequest, RegisterResponse, ChangePasswordRequest, ChangePasswordResponse,
    LogoutRequest, LogoutResponse, ProfileResponse
)
from ..services.auth_service import AuthService
from ..services.authorization_service import AuthorizationService
from ..core.config import settings
from .deps import get_auth_service, get_authorization_service, get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """
    Authenticate user and return tokens.
    
    Args:
        request: HTTP request
        login_data: Login credentials
        
    Returns:
        LoginResponse: Authentication tokens and user info
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = auth_service.security.generate_device_fingerprint(user_agent, ip_address)
        
        # Authenticate user
        auth_result = await auth_service.authenticate(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            require_biometric=login_data.require_biometric
        )
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Authentication failed"
            )
        
        # Set session cookie
        response = LoginResponse(
            access_token=auth_result.token,
            refresh_token=auth_result.refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=ProfileResponse.from_orm(auth_result.user)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/login/form", response_model=LoginResponse)
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """
    OAuth2 compatible login endpoint.
    
    Args:
        request: HTTP request
        form_data: OAuth2 form data
        
    Returns:
        LoginResponse: Authentication tokens and user info
    """
    login_data = LoginRequest(
        username=form_data.username,
        password=form_data.password,
        require_biometric=False
    )
    
    return await login(request, login_data, auth_service)


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: Request,
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> RegisterResponse:
    """
    Register new user account.
    
    Args:
        request: HTTP request
        register_data: Registration data
        
    Returns:
        RegisterResponse: Registration result
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Register user
        user = await auth_service.register_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            phone_number=register_data.phone_number,
            date_of_birth=register_data.date_of_birth,
            gender=register_data.gender,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return RegisterResponse(
            success=True,
            message="User registered successfully",
            user_id=user.id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: HTTP request
        refresh_data: Refresh token request
        
    Returns:
        RefreshTokenResponse: New access token
        
    Raises:
        HTTPException: If refresh fails
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Refresh token
        token_result = await auth_service.refresh_token(
            refresh_token=refresh_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not token_result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_result.error_message or "Token refresh failed"
            )
        
        return RefreshTokenResponse(
            access_token=token_result.token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LogoutResponse:
    """
    Logout user and invalidate tokens.
    
    Args:
        request: HTTP request
        logout_data: Logout request
        
    Returns:
        LogoutResponse: Logout result
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Logout user
        success = await auth_service.logout_user(
            refresh_token=logout_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return LogoutResponse(
            success=success,
            message="Logged out successfully" if success else "Logout failed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ChangePasswordResponse:
    """
    Change user password.
    
    Args:
        password_data: Password change request
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        ChangePasswordResponse: Password change result
        
    Raises:
        HTTPException: If password change fails
    """
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
) -> ProfileResponse:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        ProfileResponse: User profile information
    """
    return ProfileResponse.from_orm(current_user)


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ProfileResponse:
    """
    Update current user profile.
    
    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        ProfileResponse: Updated user profile
        
    Raises:
        HTTPException: If profile update fails
    """
    try:
        updated_user = await auth_service.update_user_profile(
            user_id=current_user.id,
            profile_data=profile_data
        )
        
        return ProfileResponse.from_orm(updated_user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Verify user email address.
    
    Args:
        token: Email verification token
        auth_service: Authentication service
        
    Returns:
        dict: Verification result
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        success = await auth_service.verify_email(token)
        
        return {
            "success": success,
            "message": "Email verified successfully" if success else "Invalid or expired token"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Send password reset email.
    
    Args:
        email: User email address
        request: HTTP request
        auth_service: Authentication service
        
    Returns:
        dict: Password reset request result
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        
        success = await auth_service.send_password_reset_email(
            email=email,
            ip_address=ip_address
        )
        
        return {
            "success": success,
            "message": "Password reset email sent" if success else "Email not found"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Reset password using reset token.
    
    Args:
        token: Password reset token
        new_password: New password
        request: HTTP request
        auth_service: Authentication service
        
    Returns:
        dict: Password reset result
        
    Raises:
        HTTPException: If password reset fails
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else "unknown"
        
        success = await auth_service.reset_password(
            token=token,
            new_password=new_password,
            ip_address=ip_address
        )
        
        return {
            "success": success,
            "message": "Password reset successfully" if success else "Invalid or expired token"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(get_authorization_service)
) -> dict:
    """
    Get current user information with permissions.
    
    Args:
        current_user: Current authenticated user
        authz_service: Authorization service
        
    Returns:
        dict: User information with roles and permissions
    """
    # Get user roles and permissions
    user_roles = await authz_service.get_user_roles(current_user.id)
    user_permissions = await authz_service.get_user_permissions(current_user.id)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "last_login_at": current_user.last_login_at,
        "created_at": current_user.created_at,
        "roles": user_roles,
        "permissions": list(user_permissions)
    }
