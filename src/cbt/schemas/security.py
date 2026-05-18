"""
Security hardening and penetration testing schemas.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ScanType(str, Enum):
    """Security scan types."""
    SAST = "SAST"
    DAST = "DAST"
    PENETRATION_TEST = "PENETRATION_TEST"
    SERVER_HARDENING = "SERVER_HARDENING"
    WAF_CONFIGURATION = "WAF_CONFIGURATION"
    SECRETS_AUDIT = "SECRETS_AUDIT"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityStatus(str, Enum):
    """Vulnerability status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACKNOWLEDGED = "acknowledged"
    FALSE_POSITIVE = "false_positive"


class SASTScanRequest(BaseModel):
    """SAST scan request."""
    scan_type: str = "comprehensive"  # quick, comprehensive, deep
    
    @field_validator("scan_type")
    @classmethod
    def validate_scan_type(cls, v: str) -> str:
        allowed_types = ["quick", "comprehensive", "deep"]
        if v not in allowed_types:
            raise ValueError(f"Scan type must be one of: {allowed_types}")
        return v


class SASTScanResponse(BaseModel):
    """SAST scan response."""
    scan_id: str
    scan_type: str
    status: str
    vulnerabilities_found: Optional[int] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None
    scan_duration: Optional[float] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DASTScanRequest(BaseModel):
    """DAST scan request."""
    target_url: str
    scan_type: str = "comprehensive"  # quick, comprehensive, deep
    
    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("Target URL must start with http:// or https://")
        return v

    @field_validator("scan_type")
    @classmethod
    def validate_dast_scan_type(cls, v: str) -> str:
        allowed_types = ["quick", "comprehensive", "deep"]
        if v not in allowed_types:
            raise ValueError(f"Scan type must be one of: {allowed_types}")
        return v


class DASTScanResponse(BaseModel):
    """DAST scan response."""
    scan_id: str
    scan_type: str
    target_url: str
    status: str
    vulnerabilities_found: Optional[int] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None
    scan_duration: Optional[float] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PenetrationTestRequest(BaseModel):
    """Penetration test request."""
    test_scope: Dict[str, Any]
    
    @field_validator("test_scope")
    @classmethod
    def validate_test_scope(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["target_url", "test_types"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Test scope must include: {required_fields}")
        return v


class PenetrationTestResponse(BaseModel):
    """Penetration test response."""
    test_id: str
    scan_type: str
    status: str
    vulnerabilities_found: Optional[int] = None
    risk_score: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    test_duration: Optional[float] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ServerHardeningRequest(BaseModel):
    """Server hardening request."""
    server_config: Dict[str, Any]
    
    @field_validator("server_config")
    @classmethod
    def validate_server_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("Server configuration cannot be empty")
        return v


class ServerHardeningResponse(BaseModel):
    """Server hardening response."""
    hardening_id: str
    scan_type: str
    status: str
    hardening_score: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    hardening_duration: Optional[float] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class WAFConfigurationRequest(BaseModel):
    """WAF configuration request."""
    waf_config: Dict[str, Any]
    
    @field_validator("waf_config")
    @classmethod
    def validate_waf_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("WAF configuration cannot be empty")
        return v


class WAFConfigurationResponse(BaseModel):
    """WAF configuration response."""
    config_id: str
    scan_type: str
    status: str
    results: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    configuration_duration: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class SecretsAuditResponse(BaseModel):
    """Secrets audit response."""
    audit_id: str
    scan_type: str
    status: str
    security_score: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    audit_duration: Optional[float] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class Vulnerability(BaseModel):
    """Vulnerability model."""
    id: str
    scan_id: str
    severity: SeverityLevel
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    url: Optional[str] = None
    parameter: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    status: VulnerabilityStatus
    exploit_available: Optional[bool] = False
    remediated_by: Optional[str] = None
    remediated_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    remediation_notes: Optional[str] = None
    acknowledgment_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class VulnerabilityReport(BaseModel):
    """Vulnerability report model."""
    scan_id: Optional[str] = None
    total_vulnerabilities: int
    severity_distribution: Dict[str, int]
    vulnerabilities: Dict[str, List[Dict[str, Any]]]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VulnerabilityRemediation(BaseModel):
    """Vulnerability remediation request."""
    notes: Optional[str] = None
    evidence: Optional[str] = None


class SecurityScan(BaseModel):
    """Security scan model."""
    id: str
    scan_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    vulnerabilities_found: Optional[int] = None
    configuration: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SecurityDashboard(BaseModel):
    """Security dashboard model."""
    overview: Dict[str, Any]
    recent_scans: List[Dict[str, Any]]
    risk_level: str
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ComplianceCheck(BaseModel):
    """Compliance check model."""
    standard: str
    compliance_score: float
    compliant_categories: int
    total_categories: int
    results: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    checked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RemediationSprint(BaseModel):
    """Remediation sprint model."""
    id: str
    name: str
    description: Optional[str] = None
    vulnerability_ids: List[str]
    created_by: str
    created_at: datetime
    target_completion: Optional[datetime] = None
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class SecurityMetric(BaseModel):
    """Security metric model."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    trend: Optional[str] = None  # up, down, stable


class SecurityAlert(BaseModel):
    """Security alert model."""
    id: str
    alert_type: str
    severity: SeverityLevel
    title: str
    description: str
    source: str
    affected_resources: List[str]
    first_seen: datetime
    last_seen: datetime
    status: str  # active, acknowledged, resolved
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SecurityPolicy(BaseModel):
    """Security policy model."""
    id: str
    name: str
    description: str
    category: str
    requirements: List[str]
    compliance_standards: List[str]
    implementation_status: str
    last_reviewed: datetime
    next_review: datetime
    owner: str
    
    model_config = ConfigDict(from_attributes=True)


class SecurityIncident(BaseModel):
    """Security incident model."""
    id: str
    incident_type: str
    severity: SeverityLevel
    title: str
    description: str
    detected_at: datetime
    reported_by: str
    assigned_to: Optional[str] = None
    status: str  # open, investigating, resolved
    impact_assessment: Optional[str] = None
    containment_actions: List[str] = []
    resolution_actions: List[str] = []
    lessons_learned: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ThreatIntelligence(BaseModel):
    """Threat intelligence model."""
    id: str
    threat_type: str
    severity: SeverityLevel
    title: str
    description: str
    source: str
    indicators: List[Dict[str, Any]]
    affected_systems: List[str]
    mitigation_recommendations: List[str]
    first_seen: datetime
    last_seen: datetime
    confidence_score: float
    
    model_config = ConfigDict(from_attributes=True)


class SecurityConfiguration(BaseModel):
    """Security configuration model."""
    component: str
    configuration_type: str
    settings: Dict[str, Any]
    compliance_status: str
    last_updated: datetime
    updated_by: str
    
    model_config = ConfigDict(from_attributes=True)


class SecurityAuditLog(BaseModel):
    """Security audit log model."""
    id: str
    action: str
    resource_type: str
    resource_id: str
    user_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class RiskAssessment(BaseModel):
    """Risk assessment model."""
    id: str
    asset: str
    threat: str
    vulnerability: str
    likelihood: int  # 1-5 scale
    impact: int  # 1-5 scale
    risk_score: float  # likelihood * impact
    risk_level: SeverityLevel
    mitigation_measures: List[str]
    residual_risk: float
    assessment_date: datetime
    next_review: datetime
    assessor: str
    
    model_config = ConfigDict(from_attributes=True)
