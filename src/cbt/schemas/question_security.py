"""
Question bank encryption and security control schemas.
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EncryptionStatus(str, Enum):
    """Encryption status."""
    ENCRYPTED = "encrypted"
    DECRYPTED = "decrypted"
    PARTIAL = "partial"
    NONE = "none"


class SecurityLevel(str, Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EncryptionMethod(str, Enum):
    """Encryption methods."""
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"


class QuestionEncryptionRequest(BaseModel):
    """Question encryption request."""
    question_data: Dict[str, Any]
    encryption_method: Optional[EncryptionMethod] = EncryptionMethod.AES_256_GCM
    encrypt_all_fields: bool = True
    
    @field_validator("question_data")
    @classmethod
    def validate_question_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v or not isinstance(v, dict):
            raise ValueError("Question data must be a non-empty dictionary")
        return v


class QuestionEncryptionResponse(BaseModel):
    """Question encryption response."""
    success: bool
    encrypted_data: Dict[str, Any]
    metadata: Dict[str, Any]
    encryption_time: Optional[float] = None


class QuestionDecryptionRequest(BaseModel):
    """Question decryption request."""
    encrypted_data: Dict[str, Any]
    key_id: Optional[str] = None
    
    @field_validator("encrypted_data")
    @classmethod
    def validate_encrypted_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v or not isinstance(v, dict):
            raise ValueError("Encrypted data must be a non-empty dictionary")
        return v


class QuestionDecryptionResponse(BaseModel):
    """Question decryption response."""
    success: bool
    decrypted_data: Dict[str, Any]
    metadata: Dict[str, Any]
    decryption_time: Optional[float] = None


class KeyRotationRequest(BaseModel):
    """Key rotation request."""
    force_rotation: bool = False
    backup_old_keys: bool = True
    rotation_reason: Optional[str] = None


class KeyRotationResponse(BaseModel):
    """Key rotation response."""
    rotation_completed: bool
    new_key_id: str
    reencrypted_count: int
    failed_count: int
    rotation_date: datetime
    rotation_duration: Optional[float] = None


class QuestionIntegrityResponse(BaseModel):
    """Question integrity validation response."""
    question_id: str
    validation_date: datetime
    integrity_score: float
    passed: bool
    checks: Dict[str, Any]


class EncryptionStatusResponse(BaseModel):
    """Encryption status response."""
    total_questions: int
    encrypted_questions_text: int
    encrypted_questions_options: int
    encryption_coverage: Dict[str, float]
    key_management: Dict[str, Any]
    security_status: str


class SecurityAuditRequest(BaseModel):
    """Security audit request."""
    user_id: str
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SecurityPolicy(BaseModel):
    """Security policy configuration."""
    encryption_required: bool = True
    key_rotation_frequency: str = "90_days"
    integrity_validation: bool = True
    audit_logging: bool = True
    access_control: str = "role_based"
    data_retention: str = "7_years"
    encryption_method: EncryptionMethod = EncryptionMethod.AES_256_GCM
    minimum_key_strength: int = 256
    backup_encryption_keys: bool = True


class QuestionSecurityInfo(BaseModel):
    """Question security information."""
    question_id: str
    encryption_status: Dict[str, Any]
    hash_status: Dict[str, Any]
    security_level: SecurityLevel
    last_accessed: Optional[datetime] = None
    access_count: int = 0


class EncryptionMetadata(BaseModel):
    """Encryption metadata."""
    encrypted_fields: List[str]
    encryption_method: EncryptionMethod
    key_id: str
    encrypted_at: datetime
    iv: Optional[str] = None
    tag: Optional[str] = None
    algorithm: str


class SecurityEvent(BaseModel):
    """Security event model."""
    event_id: str
    event_type: str
    user_id: Optional[str] = None
    question_id: Optional[str] = None
    details: Dict[str, Any]
    timestamp: datetime
    severity: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class EncryptionAuditLog(BaseModel):
    """Encryption audit log."""
    audit_id: str
    user_id: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class KeyManagement(BaseModel):
    """Key management information."""
    key_id: str
    algorithm: str
    key_size: int
    created_at: datetime
    expires_at: datetime
    status: str
    last_used: Optional[datetime] = None
    usage_count: int = 0


class BatchEncryptionResult(BaseModel):
    """Batch encryption result."""
    batch_id: str
    total_questions: int
    processed: int
    success: int
    failed: int
    errors: List[str]
    processing_time: Optional[float] = None


class BatchIntegrityResult(BaseModel):
    """Batch integrity validation result."""
    batch_id: str
    total_questions: int
    processed: int
    passed: int
    failed: int
    average_integrity_score: float
    validation_results: List[QuestionIntegrityResponse]


class SecurityComplianceReport(BaseModel):
    """Security compliance report."""
    report_id: str
    report_date: datetime
    compliance_score: float
    encryption_compliance: Dict[str, Any]
    key_management_compliance: Dict[str, Any]
    audit_compliance: Dict[str, Any]
    recommendations: List[str]
    passed_checks: int
    failed_checks: int


class SecurityMetrics(BaseModel):
    """Security metrics."""
    period: str
    total_encryptions: int
    total_decryptions: int
    key_rotations: int
    integrity_validations: int
    security_events: int
    average_processing_time: float
    success_rate: float


class QuestionSecuritySummary(BaseModel):
    """Question security summary."""
    total_questions: int
    encrypted_questions: int
    encryption_coverage: float
    average_integrity_score: float
    security_events_count: int
    last_key_rotation: Optional[datetime] = None
    security_level_distribution: Dict[str, int]


class EncryptionPerformance(BaseModel):
    """Encryption performance metrics."""
    operation_type: str
    data_size: int
    processing_time: float
    throughput: float  # bytes per second
    success: bool
    error_message: Optional[str] = None


class SecurityAlert(BaseModel):
    """Security alert."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    question_id: Optional[str] = None
    user_id: Optional[str] = None
    detected_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class SecurityConfiguration(BaseModel):
    """Security configuration."""
    encryption_enabled: bool = True
    encryption_method: EncryptionMethod = EncryptionMethod.AES_256_GCM
    key_rotation_enabled: bool = True
    key_rotation_interval: int = 90  # days
    integrity_validation_enabled: bool = True
    audit_logging_enabled: bool = True
    access_control_enabled: bool = True
    backup_encryption_keys: bool = True
    minimum_security_level: SecurityLevel = SecurityLevel.MEDIUM


class QuestionSecurityAudit(BaseModel):
    """Question security audit."""
    audit_id: str
    question_id: str
    audit_date: datetime
    auditor_id: str
    findings: List[Dict[str, Any]]
    compliance_score: float
    recommendations: List[str]
    passed: bool


class EncryptionKeyHistory(BaseModel):
    """Encryption key history."""
    key_id: str
    previous_key_id: Optional[str] = None
    rotation_date: datetime
    rotation_reason: str
    questions_reencrypted: int
    failed_reencryptions: int
    rotation_duration: float


class SecurityDashboard(BaseModel):
    """Security dashboard data."""
    overview: Dict[str, Any]
    encryption_status: Dict[str, Any]
    key_management: Dict[str, Any]
    recent_events: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class QuestionSecurityPolicy(BaseModel):
    """Question security policy."""
    policy_id: str
    name: str
    description: str
    version: str
    created_at: datetime
    updated_at: datetime
    configuration: SecurityConfiguration
    compliance_requirements: List[str]
    enforcement_level: str


class SecurityIncident(BaseModel):
    """Security incident."""
    incident_id: str
    incident_type: str
    severity: str
    description: str
    affected_questions: List[str]
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    impact_assessment: Dict[str, Any]
    lessons_learned: List[str]


class DataRetentionPolicy(BaseModel):
    """Data retention policy."""
    policy_id: str
    data_type: str
    retention_period: str
    encryption_required: bool
    access_restrictions: List[str]
    archival_procedure: str
    deletion_procedure: str
    compliance_requirements: List[str]


class SecurityTraining(BaseModel):
    """Security training record."""
    training_id: str
    user_id: str
    training_type: str
    completion_date: datetime
    score: Optional[float] = None
    certificate_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    topics_covered: List[str]


class SecurityAssessment(BaseModel):
    """Security assessment."""
    assessment_id: str
    assessment_type: str
    scope: str
    start_date: datetime
    end_date: datetime
    assessor_id: str
    findings: List[Dict[str, Any]]
    risk_score: float
    recommendations: List[str]
    next_assessment_date: datetime


class SecurityComplianceCheck(BaseModel):
    """Security compliance check."""
    check_id: str
    requirement_id: str
    description: str
    status: str
    last_checked: datetime
    result: Dict[str, Any]
    evidence: List[str]
    next_check_date: datetime


class EncryptionBenchmark(BaseModel):
    """Encryption benchmark."""
    benchmark_id: str
    algorithm: str
    key_size: int
    data_size: int
    encryption_time: float
    decryption_time: float
    throughput: float
    memory_usage: float
    cpu_usage: float
    test_date: datetime


class SecurityMonitoring(BaseModel):
    """Security monitoring data."""
    monitoring_id: str
    metric_type: str
    value: float
    threshold: float
    status: str
    timestamp: datetime
    details: Dict[str, Any]


class QuestionSecurityReport(BaseModel):
    """Question security report."""
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    detailed_findings: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_status: Dict[str, Any]
    generated_at: datetime
