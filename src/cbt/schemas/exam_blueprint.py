"""
Exam blueprint and configuration schemas.
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from ..models.question import QuestionDifficulty, CognitiveLevel, QuestionType


class BlueprintRequirement(BaseModel):
    """Single blueprint requirement for question selection."""
    topic: str
    difficulty: QuestionDifficulty
    cognitive_level: CognitiveLevel
    question_count: int
    question_type: Optional[QuestionType] = None
    
    @validator('question_count')
    def validate_question_count(cls, v):
        if v <= 0 or v > 20:
            raise ValueError('Question count must be between 1 and 20')
        return v


class ExamBlueprintCreate(BaseModel):
    """Exam blueprint creation schema."""
    examination_id: str
    total_questions: int
    total_points: int
    requirements: List[BlueprintRequirement]
    randomization_enabled: bool = True
    option_shuffle_enabled: bool = True
    question_order_randomization: bool = True
    
    @validator('total_questions')
    def validate_total_questions(cls, v):
        if v <= 0 or v > 200:
            raise ValueError('Total questions must be between 1 and 200')
        return v
    
    @validator('total_points')
    def validate_total_points(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError('Total points must be between 1 and 1000')
        return v
    
    @validator('requirements')
    def validate_requirements(cls, v, values):
        if 'total_questions' in values:
            total_required = sum(req.question_count for req in v)
            if total_required != values['total_questions']:
                raise ValueError(f'Sum of requirement questions ({total_required}) must equal total questions ({values["total_questions"]})')
        return v


class ExamBlueprintUpdate(BaseModel):
    """Exam blueprint update schema."""
    total_questions: Optional[int] = None
    total_points: Optional[int] = None
    requirements: Optional[List[BlueprintRequirement]] = None
    randomization_enabled: Optional[bool] = None
    option_shuffle_enabled: Optional[bool] = None
    question_order_randomization: Optional[bool] = None


class ExamBlueprintResponse(BaseModel):
    """Exam blueprint response schema."""
    id: str
    examination_id: str
    total_questions: int
    total_points: int
    requirements: List[BlueprintRequirement]
    randomization_enabled: bool
    option_shuffle_enabled: bool
    question_order_randomization: bool
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_validated(self) -> bool:
        """Check if blueprint is validated."""
        return self.status == "validated"
    
    class Config:
        from_attributes = True


class BlueprintValidationRequest(BaseModel):
    """Blueprint validation request schema."""
    blueprint_id: str
    validate_question_availability: bool = True
    validate_distribution: bool = True
    check_conflicts: bool = True


class BlueprintValidationResponse(BaseModel):
    """Blueprint validation response schema."""
    is_valid: bool
    validation_errors: List[str]
    validation_warnings: List[str]
    availability_report: Dict[str, Any]
    distribution_analysis: Dict[str, Any]
    conflict_report: List[Dict[str, Any]]
    validated_at: datetime
    validated_by: str


class ExamScheduleCreate(BaseModel):
    """Exam schedule creation schema."""
    examination_id: str
    exam_date: date
    start_time: datetime
    duration_minutes: int
    venue_assignments: List[Dict[str, Any]]
    special_accommodations: Optional[List[Dict[str, Any]]] = None
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v < 30 or v > 480:
            raise ValueError('Duration must be between 30 and 480 minutes')
        return v
    
    @validator('venue_assignments')
    def validate_venue_assignments(cls, v):
        if not v:
            raise ValueError('At least one venue assignment is required')
        return v


class ExamScheduleResponse(BaseModel):
    """Exam schedule response schema."""
    id: str
    examination_id: str
    exam_date: date
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: str
    venue_assignments: List[Dict[str, Any]]
    special_accommodations: List[Dict[str, Any]]
    total_students: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_confirmed(self) -> bool:
        """Check if schedule is confirmed."""
        return self.status == "confirmed"
    
    class Config:
        from_attributes = True


class VenueAssignment(BaseModel):
    """Venue assignment schema."""
    venue_id: str
    venue_name: str
    capacity: int
    assigned_students: List[str]
    invigilators: List[str]
    special_instructions: Optional[str] = None


class ConflictDetectionRequest(BaseModel):
    """Conflict detection request schema."""
    examination_id: str
    check_student_conflicts: bool = True
    check_venue_conflicts: bool = True
    check_invigilator_conflicts: bool = True


class ConflictDetectionResponse(BaseModel):
    """Conflict detection response schema."""
    has_conflicts: bool
    student_conflicts: List[Dict[str, Any]]
    venue_conflicts: List[Dict[str, Any]]
    invigilator_conflicts: List[Dict[str, Any]]
    suggestions: List[str]
    detected_at: datetime


class ExamSlipRequest(BaseModel):
    """Exam slip generation request schema."""
    examination_id: str
    student_ids: Optional[List[str]] = None
    include_photo: bool = True
    include_barcode: bool = True
    format: str = "pdf"  # "pdf", "html"


class ExamSlipResponse(BaseModel):
    """Exam slip response schema."""
    slip_id: str
    examination_id: str
    student_id: str
    file_url: str
    file_name: str
    generated_at: datetime
    expires_at: datetime


class QuestionSelectionRequest(BaseModel):
    """Question selection request schema."""
    blueprint_id: str
    seed: Optional[str] = None  # For reproducible randomization
    exclude_questions: Optional[List[str]] = None
    force_include_questions: Optional[List[str]] = None


class QuestionSelectionResponse(BaseModel):
    """Question selection response schema."""
    selection_id: str
    blueprint_id: str
    selected_questions: List[str]
    selection_seed: str
    randomization_applied: bool
    selected_at: datetime
    selected_by: str


class ExamConfigurationSummary(BaseModel):
    """Exam configuration summary schema."""
    examination_id: str
    blueprint_validated: bool
    schedule_confirmed: bool
    questions_selected: bool
    venues_assigned: bool
    invigilators_assigned: bool
    ready_for_exam: bool
    completion_percentage: float
    missing_components: List[str]
    last_updated: datetime


class BlueprintTemplate(BaseModel):
    """Blueprint template for reuse."""
    id: str
    name: str
    description: str
    course_id: str
    total_questions: int
    total_points: int
    requirements: List[BlueprintRequirement]
    settings: Dict[str, Any]
    usage_count: int
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BlueprintTemplateCreate(BaseModel):
    """Blueprint template creation schema."""
    name: str
    description: str
    course_id: str
    requirements: List[BlueprintRequirement]
    settings: Dict[str, Any]
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Template name must be at least 3 characters long')
        return v.strip()


class BlueprintStatistics(BaseModel):
    """Blueprint statistics schema."""
    total_blueprints: int
    validated_blueprints: int
    pending_validation: int
    failed_validation: int
    
    by_course: Dict[str, int]
    by_difficulty_distribution: Dict[str, Dict[str, int]]
    by_cognitive_level_distribution: Dict[str, Dict[str, int]]
    average_questions_per_blueprint: float
    average_points_per_blueprint: float


class VenueAvailability(BaseModel):
    """Venue availability schema."""
    venue_id: str
    venue_name: str
    capacity: int
    available_slots: List[Dict[str, Any]]
    booking_conflicts: List[Dict[str, Any]]
    special_features: List[str]


class ExamConfigurationRequest(BaseModel):
    """Complete exam configuration request."""
    examination_id: str
    blueprint: ExamBlueprintCreate
    schedule: ExamScheduleCreate
    question_selection: QuestionSelectionRequest
    auto_validate: bool = True
    auto_detect_conflicts: bool = True


class ExamConfigurationResponse(BaseModel):
    """Complete exam configuration response."""
    success: bool
    examination_id: str
    blueprint: Optional[ExamBlueprintResponse] = None
    schedule: Optional[ExamScheduleResponse] = None
    question_selection: Optional[QuestionSelectionResponse] = None
    validation_results: Optional[BlueprintValidationResponse] = None
    conflict_results: Optional[ConflictDetectionResponse] = None
    errors: List[str]
    warnings: List[str]
    configured_at: datetime
    configured_by: str
