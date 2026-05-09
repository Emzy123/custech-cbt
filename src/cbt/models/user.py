"""
User model for authentication and authorization using Beanie (MongoDB).
"""

from typing import Optional
import enum
from datetime import datetime, timezone
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class UserRole(str, enum.Enum):
    """User roles in the system."""
    STUDENT = "STUDENT"
    LECTURER = "LECTURER"
    EXAM_OFFICER = "EXAM_OFFICER"
    ADMINISTRATOR = "ADMINISTRATOR"
    SUPER_ADMIN = "SUPER_ADMIN"


class Gender(str, enum.Enum):
    """Gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class UserRoleAssignment(BaseDocument):
    """User role assignments with department context."""
    user_id: str
    role: UserRole
    department_id: Optional[str] = None
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Settings:
        name = "user_roles"


class User(BaseDocument):
    """User model for authentication and basic user information."""

    # Basic Information
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[Gender] = None

    # Security
    password_hash: str
    salt: str
    is_verified: bool = False
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    class Settings:
        name = "users"
