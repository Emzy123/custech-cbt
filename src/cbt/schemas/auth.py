"""
Authentication and user management schemas.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from ..models.user import Gender, UserRole


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str
    require_biometric: bool = False
    biometric_data: Optional[dict] = None


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "ProfileResponse"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    """User registration request schema."""
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not (v.startswith('+234') and len(v) == 13 and v[4:].isdigit()):
            raise ValueError('Phone number must be in format +234XXXXXXXXXX')
        return v


class RegisterResponse(BaseModel):
    """Registration response schema."""
    success: bool
    message: str
    user_id: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePasswordResponse(BaseModel):
    """Change password response schema."""
    success: bool
    message: str


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Logout response schema."""
    success: bool
    message: str


class ProfileResponse(BaseModel):
    """User profile response schema."""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[Gender]
    is_verified: bool
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """Create from ORM object."""
        return cls(
            id=obj.id,
            username=obj.username,
            email=obj.email,
            first_name=obj.first_name,
            last_name=obj.last_name,
            full_name=f"{obj.first_name} {obj.last_name}",
            phone_number=obj.phone_number,
            date_of_birth=obj.date_of_birth,
            gender=obj.gender,
            is_verified=obj.is_verified,
            is_active=obj.is_active,
            last_login_at=obj.last_login_at,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class UserRoleResponse(BaseModel):
    """User role response schema."""
    id: str
    user_id: str
    role: UserRole
    department_id: Optional[str]
    department_name: Optional[str]
    granted_at: datetime
    granted_by: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class BiometricEnrollmentRequest(BaseModel):
    """Biometric enrollment request schema."""
    biometric_type: str
    biometric_data: str  # Base64 encoded biometric template
    device_id: Optional[str] = None


class BiometricEnrollmentResponse(BaseModel):
    """Biometric enrollment response schema."""
    success: bool
    message: str
    template_id: Optional[str] = None


class BiometricVerificationRequest(BaseModel):
    """Biometric verification request schema."""
    biometric_type: str
    biometric_data: str  # Base64 encoded biometric template
    device_id: Optional[str] = None


class BiometricVerificationResponse(BaseModel):
    """Biometric verification response schema."""
    success: bool
    message: str
    match_score: Optional[float] = None
    verification_time: Optional[datetime] = None


class SessionInfo(BaseModel):
    """Session information schema."""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    device_fingerprint: str
    biometric_verified: bool
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserSessionsResponse(BaseModel):
    """User sessions response schema."""
    sessions: List[SessionInfo]
    total_sessions: int
    active_sessions: int


class SecurityEventResponse(BaseModel):
    """Security event response schema."""
    id: str
    event_type: str
    severity: str
    description: str
    user_id: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserSecuritySettings(BaseModel):
    """User security settings schema."""
    require_biometric: bool = False
    require_totp: bool = False
    session_timeout_minutes: int = 120
    max_concurrent_sessions: int = 3
    email_notifications: bool = True
    sms_notifications: bool = False


class UpdateSecuritySettingsRequest(BaseModel):
    """Update security settings request schema."""
    require_biometric: Optional[bool] = None
    require_totp: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_concurrent_sessions: Optional[int] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None


class PasswordPolicyResponse(BaseModel):
    """Password policy response schema."""
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_digits: bool
    require_special_chars: bool
    max_age_days: int
    history_count: int
    lockout_threshold: int
    lockout_duration_minutes: int


class UserActivityResponse(BaseModel):
    """User activity response schema."""
    login_count: int
    last_login: Optional[datetime]
    failed_login_attempts: int
    is_locked: bool
    locked_until: Optional[datetime]
    recent_logins: List[dict]
    security_events: List[SecurityEventResponse]


# Update forward references
LoginResponse.update_forward_refs()
