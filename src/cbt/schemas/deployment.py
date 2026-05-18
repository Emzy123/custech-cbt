"""
Production deployment and operational handover schemas.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DeploymentType(str, Enum):
    """Deployment types."""
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    BIG_BANG = "big_bang"


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster_recovery"


class DeploymentStatus(str, Enum):
    """Deployment status."""
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class HandoverStatus(str, Enum):
    """Handover status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DeploymentPlanCreate(BaseModel):
    """Deployment plan creation request."""
    title: str
    description: str
    environment: Environment
    deployment_type: DeploymentType = DeploymentType.BLUE_GREEN
    target_date: str
    stakeholders: List[str] = []
    rollback_plan: Dict[str, Any] = {}
    success_criteria: Dict[str, Any] = {}
    risk_assessment: Dict[str, Any] = {}
    
    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(
                "Target date must be in ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        return v


class DeploymentPlanResponse(BaseModel):
    """Deployment plan response."""
    deployment_id: str
    title: str
    description: str
    environment: Environment
    deployment_type: DeploymentType
    target_date: str
    stakeholders: List[str]
    rollback_plan: Dict[str, Any]
    success_criteria: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    created_at: datetime
    status: DeploymentStatus
    phases: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentExecutionResponse(BaseModel):
    """Deployment execution response."""
    deployment_id: str
    status: str
    success: Optional[bool] = None
    execution_duration: Optional[float] = None
    execution_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentRollbackResponse(BaseModel):
    """Deployment rollback response."""
    deployment_id: str
    rollback_reason: str
    rollback_duration: Optional[float] = None
    rollback_results: Optional[Dict[str, Any]] = None
    status: str
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OperationalHandoverCreate(BaseModel):
    """Operational handover creation request."""
    handover_team: List[str] = []
    contact_information: Dict[str, Any] = {}
    training_requirements: Dict[str, Any] = {}
    documentation_requirements: List[str] = []
    support_level_agreement: Dict[str, Any] = {}


class OperationalHandoverResponse(BaseModel):
    """Operational handover response."""
    handover_id: str
    deployment_id: str
    title: str
    created_at: datetime
    handover_team: List[str]
    documentation: Dict[str, Any]
    training_materials: Dict[str, Any]
    support_procedures: Dict[str, Any]
    monitoring_setup: Dict[str, Any]
    emergency_procedures: Dict[str, Any]
    contact_information: Dict[str, Any]
    checklists: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class HandoverExecutionResponse(BaseModel):
    """Handover execution response."""
    handover_id: str
    status: str
    success: Optional[bool] = None
    handover_duration: Optional[float] = None
    handover_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectClosureResponse(BaseModel):
    """Project closure report response."""
    report_id: str
    deployment_id: str
    project_title: str
    generated_at: datetime
    executive_summary: Dict[str, Any]
    project_overview: Dict[str, Any]
    deployment_summary: Dict[str, Any]
    technical_achievements: List[str]
    business_outcomes: Dict[str, Any]
    lessons_learned: List[str]
    recommendations: List[Dict[str, Any]]
    appendices: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentStatusResponse(BaseModel):
    """Deployment status response."""
    deployment_id: str
    title: str
    status: DeploymentStatus
    environment: Environment
    created_at: datetime
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    execution_duration: Optional[float] = None
    deployment_success: Optional[bool] = None
    current_phase: Optional[str] = None
    progress_percentage: float
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentEvent(BaseModel):
    """Deployment event log."""
    deployment_id: str
    event_type: str
    details: Dict[str, Any]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentPhase(BaseModel):
    """Deployment phase."""
    phase_id: str
    name: str
    description: str
    duration_minutes: int
    status: str
    dependencies: List[str]
    tasks: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_duration: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentMetrics(BaseModel):
    """Deployment metrics."""
    deployment_id: str
    metric_type: Optional[str] = None
    time_range: str
    metrics: Dict[str, Any]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentHealth(BaseModel):
    """Deployment health metrics."""
    deployment_id: str
    health_score: float
    overall_status: str
    health_metrics: Dict[str, Any]
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentBackup(BaseModel):
    """Deployment backup information."""
    backup_id: str
    deployment_id: str
    backup_type: str
    created_at: datetime
    status: str
    backup_size: str
    backup_location: str
    checksum: str
    
    model_config = ConfigDict(from_attributes=True)


class InfrastructureComponent(BaseModel):
    """Infrastructure component."""
    component_id: str
    name: str
    type: str
    status: str
    configuration: Dict[str, Any]
    health_status: str
    metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ServiceConfiguration(BaseModel):
    """Service configuration."""
    service_id: str
    name: str
    version: str
    environment: str
    configuration: Dict[str, Any]
    dependencies: List[str]
    health_check_url: str
    resource_requirements: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class DatabaseConfiguration(BaseModel):
    """Database configuration."""
    database_id: str
    name: str
    type: str
    version: str
    connection_string: str  # Encrypted
    configuration: Dict[str, Any]
    backup_strategy: Dict[str, Any]
    migration_status: str
    schema_version: str
    
    model_config = ConfigDict(from_attributes=True)


class SecurityConfiguration(BaseModel):
    """Security configuration."""
    security_id: str
    name: str
    type: str
    configuration: Dict[str, Any]
    compliance_standards: List[str]
    audit_status: str
    last_audit_date: datetime
    vulnerabilities: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


class MonitoringConfiguration(BaseModel):
    """Monitoring configuration."""
    monitoring_id: str
    name: str
    type: str
    dashboards: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    log_aggregation: Dict[str, Any]
    metrics_collection: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentTemplate(BaseModel):
    """Deployment template."""
    template_id: str
    name: str
    description: str
    deployment_type: DeploymentType
    environment: Environment
    template_configuration: Dict[str, Any]
    phases: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    rollback_procedures: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentEnvironment(BaseModel):
    """Deployment environment."""
    environment_id: str
    name: str
    type: Environment
    configuration: Dict[str, Any]
    infrastructure: List[InfrastructureComponent]
    services: List[ServiceConfiguration]
    databases: List[DatabaseConfiguration]
    security: SecurityConfiguration
    monitoring: MonitoringConfiguration
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentPipeline(BaseModel):
    """Deployment pipeline."""
    pipeline_id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    rollback_strategy: Dict[str, Any]
    created_at: datetime
    last_execution: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentApproval(BaseModel):
    """Deployment approval."""
    approval_id: str
    deployment_id: str
    approver_id: str
    approver_name: str
    status: str  # pending, approved, rejected
    comments: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentNotification(BaseModel):
    """Deployment notification."""
    notification_id: str
    deployment_id: str
    type: str
    recipients: List[str]
    message: str
    sent_at: datetime
    delivery_status: str
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentRisk(BaseModel):
    """Deployment risk assessment."""
    risk_id: str
    deployment_id: str
    category: str
    description: str
    probability: str  # low, medium, high
    impact: str  # low, medium, high
    mitigation_strategy: str
    owner: str
    status: str  # open, mitigated, accepted
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentChecklist(BaseModel):
    """Deployment checklist."""
    checklist_id: str
    deployment_id: str
    category: str
    items: List[Dict[str, Any]]
    completed_items: List[str]
    completion_percentage: float
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentTest(BaseModel):
    """Deployment test."""
    test_id: str
    deployment_id: str
    name: str
    type: str  # unit, integration, performance, security
    status: str  # pending, running, passed, failed
    results: Dict[str, Any]
    execution_time: Optional[float] = None
    executed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentArtifact(BaseModel):
    """Deployment artifact."""
    artifact_id: str
    deployment_id: str
    name: str
    type: str  # code, configuration, documentation, backup
    version: str
    checksum: str
    location: str
    created_at: datetime
    size: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentSchedule(BaseModel):
    """Deployment schedule."""
    schedule_id: str
    deployment_id: str
    scheduled_time: datetime
    duration_minutes: int
    timezone: str
    dependencies: List[str]
    notifications: List[Dict[str, Any]]
    created_at: datetime
    created_by: str
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentLog(BaseModel):
    """Deployment log."""
    log_id: str
    deployment_id: str
    level: str  # info, warning, error, debug
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    source: str
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentRollback(BaseModel):
    """Deployment rollback."""
    rollback_id: str
    deployment_id: str
    reason: str
    strategy: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str  # in_progress, completed, failed
    results: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentVerification(BaseModel):
    """Deployment verification."""
    verification_id: str
    deployment_id: str
    type: str  # health, functionality, performance, security
    status: str  # pending, running, passed, failed
    tests: List[Dict[str, Any]]
    results: Dict[str, Any]
    executed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentDashboard(BaseModel):
    """Deployment dashboard data."""
    active_deployments: List[DeploymentStatusResponse]
    scheduled_deployments: List[DeploymentStatusResponse]
    recent_deployments: List[DeploymentStatusResponse]
    system_health: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentComparison(BaseModel):
    """Deployment comparison."""
    comparison_id: str
    deployment_ids: List[str]
    comparison_metrics: List[str]
    results: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentStatistics(BaseModel):
    """Deployment statistics."""
    period: str
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    cancelled_deployments: int
    average_deployment_time: float
    average_rollback_time: float
    success_rate: float
    failure_rate: float
    deployment_frequency: Dict[str, int]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentRecommendation(BaseModel):
    """Deployment recommendation."""
    recommendation_id: str
    deployment_id: str
    category: str
    priority: str
    title: str
    description: str
    impact_assessment: str
    effort_estimate: str
    timeline: str
    dependencies: List[str]
    status: str  # pending, in_progress, completed, rejected
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentLesson(BaseModel):
    """Deployment lesson learned."""
    lesson_id: str
    deployment_id: str
    category: str
    lesson: str
    context: str
    impact: str  # positive, negative, neutral
    applicability: str  # specific, general, strategic
    recommendations: List[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
