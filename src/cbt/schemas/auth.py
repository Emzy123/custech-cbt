"""
Authentication and user management schemas.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)
from typing import Optional, List, Self
from datetime import datetime, date

from ..models.user import Gender, UserRole


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str
    require_biometric: bool = False
    biometric_data: Optional[dict] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    return v


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

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith("+234") and len(v) == 13 and v[4:].isdigit()):
            raise ValueError("Phone number must be in format +234XXXXXXXXXX")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        return self


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

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)

    @model_validator(mode="after")
    def confirm_matches_new(self) -> Self:
        if self.confirm_password != self.new_password:
            raise ValueError("Passwords do not match")
        return self


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
    model_config = ConfigDict(from_attributes=True)

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


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ProfileResponse


class UserRoleResponse(BaseModel):
    """User role response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    role: UserRole
    department_id: Optional[str]
    department_name: Optional[str]
    granted_at: datetime
    granted_by: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool


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
    model_config = ConfigDict(from_attributes=True)

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


class UserSessionsResponse(BaseModel):
    """User sessions response schema."""
    sessions: List[SessionInfo]
    total_sessions: int
    active_sessions: int


class SecurityEventResponse(BaseModel):
    """Security event response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    severity: str
    description: str
    user_id: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]


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
