"""
User model for authentication and authorization using Beanie (MongoDB).
"""

from typing import Optional
from datetime import datetime, timezone
import enum
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class Gender(str, enum.Enum):
    """User gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class UserRole(str, enum.Enum):
    """User role options."""
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"
    # Legacy roles mapped for schema compatibility
    ADMINISTRATOR = "admin"
    SUPER_ADMIN = "admin"
    EXAM_OFFICER = "admin"



class User(BaseDocument):
    """User model for authentication and basic user information."""

    username: str
    email: str
    password_hash: str
    salt: str
    full_name: str
    matric_number: Optional[str] = None
    role: str = "student"  # "student", "lecturer", "admin"
    department: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[Gender] = None
    is_verified: bool = True
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    @property
    def first_name(self) -> str:
        """Derive first name from full name."""
        parts = self.full_name.split(" ", 1)
        return parts[0] if parts else ""

    @property
    def last_name(self) -> str:
        """Derive last name from full name."""
        parts = self.full_name.split(" ", 1)
        return parts[1] if len(parts) > 1 else ""

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    class Settings:
        name = "users"
