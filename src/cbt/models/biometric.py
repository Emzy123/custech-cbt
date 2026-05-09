"""
Biometric models for secure template handling using Beanie (MongoDB).
"""

from typing import Optional, List, Dict, Any
import enum
from datetime import datetime, timezone
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class BiometricTemplate(BaseDocument):
    """Biometric template model for storing encrypted biometric data."""
    user_id: str
    biometric_type: str  # fingerprint, facial_recognition, iris, voice, palm
    template_data: str   # Encrypted biometric template
    template_hash: str   # SHA-256 hash
    device_id: Optional[str] = None
    quality_score: float = 0.0
    enrollment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deactivated_at: Optional[datetime] = None
    deactivation_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_templates"


class BiometricVerification(BaseDocument):
    """Biometric verification model for tracking verification attempts."""
    user_id: str
    template_id: Optional[str] = None
    biometric_type: str
    verification_data: str   # Encrypted verification data
    verification_hash: str   # SHA-256 hash
    match_score: float
    confidence: str           # high, medium, low
    verification_method: str  # minutiae_matching, feature_matching, etc.
    passed: bool
    verification_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_verifications"


class BiometricDevice(BaseDocument):
    """Biometric device model for managing biometric hardware."""
    device_name: str
    device_identifier: str  # Serial number or unique ID
    device_type: str        # fingerprint_scanner, camera, iris_scanner, microphone
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    supported_biometric_types: List[str] = Field(default_factory=list)
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_devices"


class BiometricSession(BaseDocument):
    """Biometric session model for tracking exam session biometrics."""
    user_id: str
    exam_instance_id: Optional[str] = None
    session_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_end: Optional[datetime] = None
    initial_verification: bool = False
    re_verifications: int = 0
    verification_intervals: List[str] = Field(default_factory=list)
    anomaly_detected: bool = False
    anomaly_details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_sessions"


class BiometricAnomaly(BaseDocument):
    """Biometric anomaly model for tracking suspicious biometric events."""
    session_id: str
    user_id: str
    anomaly_type: str    # identity_mismatch, timeout, device_error, etc.
    severity: str        # low, medium, high, critical
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_anomalies"


class BiometricConfiguration(BaseDocument):
    """Biometric configuration model for system settings."""
    biometric_type: str
    configuration_name: str
    verification_threshold: float = 0.7
    quality_threshold: float = 0.6
    max_verification_attempts: int = 3
    re_verification_interval: int = 300  # seconds
    template_retention_days: int = 365
    encryption_algorithm: str = "AES-256"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_configurations"


class BiometricAuditLog(BaseDocument):
    """Biometric audit log model for compliance tracking."""
    user_id: Optional[str] = None
    action: str  # register, verify, update, deactivate
    biometric_type: Optional[str] = None
    template_id: Optional[str] = None
    verification_id: Optional[str] = None
    device_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "biometric_audit_logs"
