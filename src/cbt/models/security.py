"""
Security and audit models for user sessions, audit logs, and logging using Beanie (MongoDB).
"""

from typing import Optional, Dict, Any
import enum
from datetime import datetime, timezone
from pydantic import Field

from .base import BaseDocument


class UserSession(BaseDocument):
    """User session tracking and management."""
    user_id: str
    session_token: str
    refresh_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    biometric_verified: bool = False
    expires_at: datetime
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def session_age(self) -> int:
        age = datetime.now(timezone.utc) - self.created_at
        return int(age.total_seconds() / 60)

    class Settings:
        name = "user_sessions"


class AuditAction(str, enum.Enum):
    """Audit log action types."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXAM_START = "EXAM_START"
    EXAM_SUBMIT = "EXAM_SUBMIT"
    ROLE_CHANGE = "ROLE_CHANGE"
    SYSTEM_CHANGE = "SYSTEM_CHANGE"
    SECURITY_EVENT = "SECURITY_EVENT"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"


class AuditLog(BaseDocument):
    """Comprehensive audit logging for security and compliance."""
    user_id: Optional[str] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    class Settings:
        name = "audit_logs"


class SecurityEvent(BaseDocument):
    """Security events that require immediate attention."""
    event_type: str
    severity: str  # HIGH, MEDIUM, LOW
    description: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    class Settings:
        name = "security_events"


class SecurityScan(BaseDocument):
    """Recorded security scan or hardening run (SAST, DAST, WAF, audits, etc.)."""

    scan_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    vulnerabilities_found: int = 0
    configuration: Dict[str, Any] = Field(default_factory=dict)
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Settings:
        name = "security_scans"


class Vulnerability(BaseDocument):
    """Individual vulnerability finding linked to a security scan."""

    scan_id: str
    severity: str
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    url: Optional[str] = None
    parameter: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: float = 0.0
    remediation: Optional[str] = None
    status: str = "open"
    exploit_available: bool = False
    remediated_by: Optional[str] = None
    remediated_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    remediation_notes: Optional[str] = None
    acknowledgment_notes: Optional[str] = None

    class Settings:
        name = "vulnerabilities"
