"""
Biometric integration schemas for secure template handling.
"""

from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BiometricType(str, Enum):
    """Biometric types."""
    FINGERPRINT = "fingerprint"
    FACIAL_RECOGNITION = "facial_recognition"
    IRIS = "iris"
    VOICE = "voice"
    PALM = "palm"
    VEIN = "vein"


class VerificationMethod(str, Enum):
    """Verification methods."""
    MINUTIAE_MATCHING = "minutiae_matching"
    FEATURE_MATCHING = "feature_matching"
    IRIS_CODE_MATCHING = "iris_code_matching"
    VOICE_PRINT_MATCHING = "voice_print_matching"
    PATTERN_MATCHING = "pattern_matching"


class ConfidenceLevel(str, Enum):
    """Confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BiometricTemplateRegister(BaseModel):
    """Biometric template registration request."""
    biometric_type: BiometricType
    template_data: str  # Base64 encoded biometric template
    device_id: Optional[str] = None
    quality_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('quality_score')
    def validate_quality_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Quality score must be between 0.0 and 1.0')
        return v
    
    @validator('biometric_type')
    def validate_biometric_type(cls, v):
        allowed_types = ['fingerprint', 'facial_recognition', 'iris', 'voice', 'palm', 'vein']
        if v.value not in allowed_types:
            raise ValueError(f'Biometric type must be one of: {allowed_types}')
        return v


class BiometricTemplateResponse(BaseModel):
    """Biometric template response."""
    template_id: str
    user_id: str
    biometric_type: BiometricType
    enrollment_date: datetime
    quality_score: float
    status: str
    
    class Config:
        from_attributes = True


class BiometricVerificationRequest(BaseModel):
    """Biometric verification request."""
    user_id: str
    biometric_type: BiometricType
    verification_data: str  # Base64 encoded biometric data
    device_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('biometric_type')
    def validate_biometric_type(cls, v):
        allowed_types = ['fingerprint', 'facial_recognition', 'iris', 'voice', 'palm', 'vein']
        if v.value not in allowed_types:
            raise ValueError(f'Biometric type must be one of: {allowed_types}')
        return v


class BiometricVerificationResponse(BaseModel):
    """Biometric verification response."""
    verification_id: str
    user_id: str
    biometric_type: BiometricType
    passed: bool
    match_score: float
    confidence: ConfidenceLevel
    verification_date: datetime
    threshold: float
    
    class Config:
        from_attributes = True


class BiometricTemplateUpdate(BaseModel):
    """Biometric template update request."""
    template_data: str  # Base64 encoded biometric template
    quality_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('quality_score')
    def validate_quality_score(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError('Quality score must be between 0.0 and 1.0')
        return v


class BiometricTemplateDeactivate(BaseModel):
    """Biometric template deactivation request."""
    reason: str


class BiometricDeviceRegister(BaseModel):
    """Biometric device registration request."""
    device_name: str
    device_identifier: str
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    supported_biometric_types: List[str] = []
    metadata: Optional[Dict[str, Any]] = {}


class BiometricDeviceResponse(BaseModel):
    """Biometric device response."""
    device_id: str
    device_name: str
    device_identifier: str
    device_type: str
    registration_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class BiometricStatisticsResponse(BaseModel):
    """Biometric statistics response."""
    template_statistics: Dict[str, Any]
    verification_statistics: Dict[str, Any]
    period: str
    generated_at: datetime
    
    class Config:
        from_attributes = True


class BiometricQualityCheck(BaseModel):
    """Biometric quality check result."""
    template_id: str
    quality_score: float
    quality_level: str
    recommendations: List[str]
    check_date: datetime
    passed: bool


class BiometricSession(BaseModel):
    """Biometric session model."""
    session_id: str
    user_id: str
    exam_instance_id: Optional[str] = None
    session_start: datetime
    session_end: Optional[datetime] = None
    initial_verification: bool
    re_verifications: int
    verification_intervals: List[datetime]
    anomaly_detected: bool
    anomaly_details: Dict[str, Any]
    
    class Config:
        from_attributes = True


class BiometricAnomaly(BaseModel):
    """Biometric anomaly model."""
    anomaly_id: str
    session_id: str
    user_id: str
    anomaly_type: str
    severity: str
    description: str
    detected_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    
    class Config:
        from_attributes = True


class BiometricConfiguration(BaseModel):
    """Biometric configuration model."""
    biometric_type: BiometricType
    verification_threshold: float
    quality_threshold: float
    max_verification_attempts: int
    re_verification_interval: int
    template_retention_days: int
    encryption_algorithm: str
    
    class Config:
        from_attributes = True


class BiometricAuditLog(BaseModel):
    """Biometric audit log model."""
    log_id: str
    user_id: Optional[str] = None
    action: str
    biometric_type: Optional[str] = None
    template_id: Optional[str] = None
    verification_id: Optional[str] = None
    device_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class BiometricComplianceReport(BaseModel):
    """Biometric compliance report model."""
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    compliance_score: float
    statistics: Dict[str, Any]
    compliance_details: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class BiometricKeyRotation(BaseModel):
    """Biometric key rotation model."""
    key_id: str
    key_version: int
    algorithm: str
    key_size: int
    created_at: datetime
    expires_at: datetime
    is_active: bool
    deprecated_at: Optional[datetime] = None
    rotation_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class BiometricEnrollmentResult(BaseModel):
    """Biometric enrollment result."""
    enrollment_id: str
    user_id: str
    biometric_type: BiometricType
    success: bool
    quality_score: float
    attempts: int
    enrollment_date: datetime
    device_id: Optional[str] = None
    recommendations: List[str] = []


class BiometricVerificationResult(BaseModel):
    """Biometric verification result."""
    verification_id: str
    user_id: str
    biometric_type: BiometricType
    success: bool
    match_score: float
    confidence: ConfidenceLevel
    verification_method: VerificationMethod
    verification_date: datetime
    device_id: Optional[str] = None
    template_id: Optional[str] = None
    processing_time: Optional[float] = None


class BiometricDeviceMaintenance(BaseModel):
    """Biometric device maintenance model."""
    device_id: str
    maintenance_type: str
    scheduled_date: datetime
    completed_date: Optional[datetime] = None
    technician: Optional[str] = None
    notes: Optional[str] = None
    status: str  # scheduled, in_progress, completed, cancelled


class BiometricTemplateBatch(BaseModel):
    """Biometric template batch processing."""
    batch_id: str
    templates: List[Dict[str, Any]]
    processing_status: str  # pending, processing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    errors: List[str] = []


class BiometricVerificationBatch(BaseModel):
    """Biometric verification batch processing."""
    batch_id: str
    verifications: List[Dict[str, Any]]
    processing_status: str  # pending, processing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    average_match_score: Optional[float] = None
    errors: List[str] = []


class BiometricSystemHealth(BaseModel):
    """Biometric system health status."""
    overall_status: str  # healthy, degraded, unhealthy
    device_status: Dict[str, str]
    service_status: Dict[str, str]
    performance_metrics: Dict[str, float]
    error_rates: Dict[str, float]
    last_check: datetime
    recommendations: List[str]


class BiometricAnalytics(BaseModel):
    """Biometric analytics data."""
    period: str
    total_verifications: int
    successful_verifications: int
    failed_verifications: int
    average_match_score: float
    match_score_distribution: Dict[str, int]
    verification_by_type: Dict[str, int]
    verification_by_device: Dict[str, int]
    peak_verification_times: List[datetime]
    anomaly_count: int


class BiometricUserSummary(BaseModel):
    """Biometric user summary."""
    user_id: str
    total_templates: int
    active_templates: int
    templates_by_type: Dict[str, int]
    total_verifications: int
    successful_verifications: int
    average_match_score: float
    last_verification: Optional[datetime] = None
    enrollment_date: Optional[datetime] = None


class BiometricDeviceSummary(BaseModel):
    """Biometric device summary."""
    device_id: str
    device_name: str
    device_type: str
    total_templates: int
    total_verifications: int
    success_rate: float
    average_match_score: float
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    status: str


class BiometricConfigurationTemplate(BaseModel):
    """Biometric configuration template."""
    template_id: str
    name: str
    description: str
    biometric_type: BiometricType
    default_settings: Dict[str, Any]
    recommended_thresholds: Dict[str, float]
    quality_requirements: Dict[str, Any]
    security_settings: Dict[str, Any]


class BiometricIntegration(BaseModel):
    """Biometric integration configuration."""
    integration_id: str
    name: str
    biometric_type: BiometricType
    sdk_version: str
    api_endpoint: Optional[str] = None
    configuration: Dict[str, Any]
    supported_features: List[str]
    limitations: List[str]
    integration_status: str


class BiometricBackup(BaseModel):
    """Biometric backup information."""
    backup_id: str
    backup_type: str  # full, incremental, differential
    created_at: datetime
    file_size: int
    file_count: int
    encryption_method: str
    checksum: str
    location: str
    restored_at: Optional[datetime] = None


class BiometricExport(BaseModel):
    """Biometric export configuration."""
    export_id: str
    export_type: str  # templates, verifications, audit_logs
    format: str  # json, csv, xml
    filters: Dict[str, Any]
    created_at: datetime
    file_size: int
    download_url: Optional[str] = None
    expires_at: datetime


class BiometricImport(BaseModel):
    """Biometric import configuration."""
    import_id: str
    import_type: str  # templates, devices, configurations
    source: str
    format: str
    validation_rules: Dict[str, Any]
    created_at: datetime
    status: str  # pending, processing, completed, failed
    records_processed: int = 0
    records_failed: int = 0
    errors: List[str] = []


class BiometricAlert(BaseModel):
    """Biometric system alert."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    source: str
    affected_resources: List[str]
    first_seen: datetime
    last_seen: datetime
    status: str  # active, acknowledged, resolved
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class BiometricPolicy(BaseModel):
    """Biometric policy configuration."""
    policy_id: str
    name: str
    description: str
    biometric_types: List[BiometricType]
    requirements: List[str]
    compliance_standards: List[str]
    implementation_status: str
    last_reviewed: datetime
    next_review: datetime
    owner: str


class BiometricTraining(BaseModel):
    """Biometric training data."""
    training_id: str
    biometric_type: BiometricType
    training_type: str  # enrollment, verification, quality_assessment
    dataset_size: int
    model_version: str
    accuracy_score: float
    false_positive_rate: float
    false_negative_rate: float
    trained_at: datetime
    is_active: bool


class BiometricTest(BaseModel):
    """Biometric test result."""
    test_id: str
    test_type: str  # enrollment, verification, performance, security
    biometric_type: BiometricType
    test_date: datetime
    test_results: Dict[str, Any]
    passed: bool
    score: Optional[float] = None
    recommendations: List[str] = []


class BiometricDashboard(BaseModel):
    """Biometric dashboard data."""
    overview: Dict[str, Any]
    recent_verifications: List[Dict[str, Any]]
    device_status: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    compliance_status: Dict[str, Any]
    last_updated: datetime
