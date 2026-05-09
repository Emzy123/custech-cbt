"""
Pilot examination schemas for testing and iterative refinement.
"""

from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PilotType(str, Enum):
    """Pilot examination types."""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    INTEGRATION = "integration"


class PilotStatus(str, Enum):
    """Pilot examination status."""
    PLANNED = "planned"
    PARTICIPANTS_ENROLLED = "participants_enrolled"
    ENVIRONMENT_READY = "environment_ready"
    ENVIRONMENT_ISSUES = "environment_issues"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    IMPROVEMENTS_IMPLEMENTED = "improvements_implemented"
    REPORT_GENERATED = "report_generated"


class MonitoringLevel(str, Enum):
    """Monitoring levels for pilot."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    INTENSIVE = "intensive"


class PilotExaminationCreate(BaseModel):
    """Pilot examination creation request."""
    title: str
    description: str
    course_code: str
    target_participants: int
    scheduled_date: str
    duration_minutes: int = 120
    pilot_type: PilotType = PilotType.FUNCTIONAL
    test_objectives: List[str] = []
    success_criteria: Dict[str, Any] = {}
    monitoring_level: MonitoringLevel = MonitoringLevel.COMPREHENSIVE
    
    @validator('target_participants')
    def validate_target_participants(cls, v):
        if v < 5 or v > 500:
            raise ValueError('Target participants must be between 5 and 500')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v < 30 or v > 480:
            raise ValueError('Duration must be between 30 and 480 minutes')
        return v


class PilotExaminationResponse(BaseModel):
    """Pilot examination response."""
    pilot_id: str
    title: str
    description: str
    course_code: str
    target_participants: int
    scheduled_date: str
    duration_minutes: int
    pilot_type: PilotType
    test_objectives: List[str]
    success_criteria: Dict[str, Any]
    monitoring_level: MonitoringLevel
    created_at: datetime
    status: PilotStatus
    configuration: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ParticipantCriteria(BaseModel):
    """Participant selection criteria."""
    departments: List[str] = []
    levels: List[str] = []
    min_gpa: Optional[float] = None
    max_gpa: Optional[float] = None
    technical_proficiency: List[str] = []
    previous_participation: Optional[bool] = None
    random_selection: bool = True
    selection_ratio: float = 1.0


class PilotEnrollmentRequest(BaseModel):
    """Pilot enrollment request."""
    participant_criteria: ParticipantCriteria


class PilotEnrollmentResponse(BaseModel):
    """Pilot enrollment response."""
    pilot_id: str
    total_enrolled: int
    enrollments: List[Dict[str, Any]]
    selection_criteria: Dict[str, Any]
    
    class Config:
        from_attributes = True


class PilotEnvironmentResponse(BaseModel):
    """Pilot environment preparation response."""
    pilot_id: str
    readiness_score: float
    ready: bool
    preparation_results: Dict[str, Any]
    
    class Config:
        from_attributes = True


class PilotExecutionResponse(BaseModel):
    """Pilot execution response."""
    pilot_id: str
    status: str
    execution_duration: Optional[float] = None
    execution_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ParticipantSurvey(BaseModel):
    """Participant survey data."""
    participant_id: str
    overall_satisfaction: int  # 1-5
    ease_of_use: int  # 1-5
    system_reliability: int  # 1-5
    interface_design: int  # 1-5
    feature_completeness: int  # 1-5
    comments: Optional[str] = None
    issues_encountered: List[str] = []
    suggestions: List[str] = []


class InvigilatorFeedback(BaseModel):
    """Invigilator feedback data."""
    invigilator_id: str
    dashboard_usability: int  # 1-5
    alert_effectiveness: int  # 1-5
    monitoring_completeness: int  # 1-5
    intervention_tools: int  # 1-5
    overall_effectiveness: int  # 1-5
    comments: Optional[str] = None
    suggestions: List[str] = []
    issues_observed: List[str] = []


class TechnicalFeedback(BaseModel):
    """Technical feedback data."""
    system_stability: int  # 1-5
    performance_adequacy: int  # 1-5
    scalability_readiness: int  # 1-5
    security_effectiveness: int  # 1-5
    monitoring_effectiveness: int  # 1-5
    issues_identified: List[str] = []
    optimization_opportunities: List[str] = []


class PilotFeedbackResponse(BaseModel):
    """Pilot feedback collection response."""
    pilot_id: str
    feedback_results: Dict[str, Any]
    feedback_analysis: Dict[str, Any]
    
    class Config:
        from_attributes = True


class SuccessCriteriaAnalysis(BaseModel):
    """Success criteria analysis."""
    criteria_name: str
    target_value: float
    achieved_value: float
    met: bool
    variance: float


class PerformanceAnalysis(BaseModel):
    """Performance analysis results."""
    response_time_analysis: Dict[str, Any]
    throughput_analysis: Dict[str, Any]
    error_rate_analysis: Dict[str, Any]
    resource_utilization: Dict[str, Any]


class UserExperienceAnalysis(BaseModel):
    """User experience analysis results."""
    task_completion_rate: float
    time_on_task: float
    error_rate: float
    satisfaction_score: float
    usability_score: float
    accessibility_score: float


class PilotAnalysisResponse(BaseModel):
    """Pilot analysis response."""
    pilot_id: str
    success_score: float
    analysis_results: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    improvement_plan: Dict[str, Any]
    
    class Config:
        from_attributes = True


class Improvement(BaseModel):
    """Improvement item."""
    id: str
    priority: str  # high, medium, low
    category: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    timeline: str
    dependencies: List[str] = []


class ImprovementPlan(BaseModel):
    """Improvement implementation plan."""
    plan_id: str
    created_at: datetime
    target_completion: datetime
    improvements: List[Improvement]
    phases: List[Dict[str, Any]]
    success_metrics: List[str]
    budget_estimate: Optional[float] = None
    resource_requirements: Dict[str, Any] = {}


class PilotImprovementRequest(BaseModel):
    """Pilot improvement implementation request."""
    improvement_plan: ImprovementPlan


class PilotImprovementResponse(BaseModel):
    """Pilot improvement implementation response."""
    pilot_id: str
    status: str
    implementation_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExecutiveSummary(BaseModel):
    """Executive summary section."""
    pilot_overview: Dict[str, Any]
    key_findings: List[str]
    success_indicators: Dict[str, Any]
    recommendations_summary: List[str]
    next_steps: List[Dict[str, Any]]


class MethodologySection(BaseModel):
    """Methodology section."""
    pilot_design: Dict[str, Any]
    data_collection: Dict[str, Any]
    analysis_methods: List[str]


class ResultsOverview(BaseModel):
    """Results overview section."""
    participation_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    satisfaction_metrics: Dict[str, Any]
    technical_metrics: Dict[str, Any]


class DetailedFindings(BaseModel):
    """Detailed findings section."""
    system_performance: Dict[str, Any]
    user_experience: Dict[str, Any]
    security_assessment: Dict[str, Any]


class PilotReportResponse(BaseModel):
    """Pilot report response."""
    metadata: Dict[str, Any]
    executive_summary: ExecutiveSummary
    methodology: MethodologySection
    results_overview: ResultsOverview
    detailed_findings: DetailedFindings
    recommendations: List[Dict[str, Any]]
    implementation_plan: Dict[str, Any]
    lessons_learned: List[str]
    next_steps: List[Dict[str, Any]]
    appendices: Dict[str, Any]
    
    class Config:
        from_attributes = True


class PilotSummaryResponse(BaseModel):
    """Pilot summary response."""
    pilot_id: str
    title: str
    status: PilotStatus
    target_participants: int
    enrolled_count: int
    success_score: float
    created_at: datetime
    execution_start: Optional[datetime] = None
    execution_duration: Optional[float] = None
    readiness_score: Optional[float] = None
    recommendations_count: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class PilotEvent(BaseModel):
    """Pilot event log."""
    pilot_id: str
    event_type: str
    details: Dict[str, Any]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class PilotMetrics(BaseModel):
    """Pilot metrics data."""
    pilot_id: str
    metrics: Dict[str, Any]
    metric_type: Optional[str] = None
    generated_at: datetime
    
    class Config:
        from_attributes = True


class PilotParticipant(BaseModel):
    """Pilot participant information."""
    enrollment_id: str
    pilot_id: str
    student_id: str
    enrollment_date: datetime
    status: str  # enrolled, active, completed, withdrawn
    communication_sent: bool
    test_account_created: bool
    participation_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PilotCommunication(BaseModel):
    """Pilot communication record."""
    communication_id: str
    pilot_id: str
    enrollment_id: str
    communication_type: str  # email, sms, notification
    message: str
    sent_at: datetime
    sent_by: str
    delivery_status: str  # sent, delivered, failed
    
    class Config:
        from_attributes = True


class PilotConfiguration(BaseModel):
    """Pilot configuration template."""
    template_name: str
    pilot_type: PilotType
    default_settings: Dict[str, Any]
    success_criteria_templates: Dict[str, Any]
    monitoring_configurations: Dict[str, Any]
    communication_templates: Dict[str, Any]


class PilotTemplate(BaseModel):
    """Pilot examination template."""
    template_id: str
    name: str
    description: str
    pilot_type: PilotType
    configuration: PilotConfiguration
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class PilotDashboard(BaseModel):
    """Pilot examination dashboard data."""
    active_pilots: List[PilotSummaryResponse]
    upcoming_pilots: List[PilotSummaryResponse]
    completed_pilots: List[PilotSummaryResponse]
    overall_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class PilotComparison(BaseModel):
    """Pilot examination comparison."""
    comparison_id: str
    pilot_ids: List[str]
    comparison_metrics: List[str]
    results: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class PilotRecommendation(BaseModel):
    """Pilot examination recommendation."""
    recommendation_id: str
    pilot_id: str
    category: str
    priority: str
    title: str
    description: str
    impact_assessment: str
    effort_estimate: str
    dependencies: List[str]
    implementation_steps: List[str]
    success_metrics: List[str]
    created_at: datetime
    status: str  # pending, in_progress, completed, rejected
    
    class Config:
        from_attributes = True


class PilotLessonLearned(BaseModel):
    """Lesson learned from pilot examination."""
    lesson_id: str
    pilot_id: str
    category: str
    lesson: str
    context: str
    impact: str  # positive, negative, neutral
    applicability: str  # specific, general, strategic
    related_recommendations: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PilotSuccessCriteria(BaseModel):
    """Pilot success criteria definition."""
    criteria_id: str
    name: str
    description: str
    category: str  # technical, user_experience, business, security
    measurement_method: str
    target_value: float
    unit: str
    weight: float  # For overall success calculation
    threshold_type: str  # minimum, maximum, exact
    
    class Config:
        from_attributes = True
