"""
Examination schemas.
"""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Self
from datetime import datetime, date

from ..models.exam import ExamStatus, ExamInstanceStatus


class ExaminationBase(BaseModel):
    """Base examination schema."""
    title: str
    description: Optional[str] = None
    exam_date: date
    start_time: datetime
    duration_minutes: int
    total_points: int
    pass_points: Optional[int] = None
    randomize_questions: bool = False
    randomize_options: bool = False
    allow_review: bool = False
    show_results_immediately: bool = False
    max_attempts: int = 1

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 5 or v > 480:  # 5 minutes to 8 hours
            raise ValueError("Duration must be between 5 and 480 minutes")
        return v

    @field_validator("total_points")
    @classmethod
    def validate_total_points(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Total points must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_pass_points_vs_total(self) -> Self:
        if (
            self.pass_points is not None
            and self.pass_points > self.total_points
        ):
            raise ValueError("Pass points cannot exceed total points")
        return self


class ExaminationCreate(ExaminationBase):
    """Examination creation schema."""
    course_id: str
    academic_session_id: str
    semester_id: str
    question_ids: List[str]  # List of question IDs to include
    question_order: Optional[List[str]] = None  # Optional specific order


class ExaminationUpdate(BaseModel):
    """Examination update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    total_points: Optional[int] = None
    pass_points: Optional[int] = None
    status: Optional[ExamStatus] = None
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    allow_review: Optional[bool] = None
    show_results_immediately: Optional[bool] = None
    max_attempts: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None
    release_mode: Optional[str] = None
    release_at: Optional[datetime] = None
    embargo_active: Optional[bool] = None


class ExaminationResponse(ExaminationBase):
    """Examination response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    status: ExamStatus
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @property
    def end_time(self) -> datetime:
        """Calculate exam end time."""
        from datetime import timedelta
        return self.start_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_active(self) -> bool:
        """Check if exam is currently active."""
        return self.status == ExamStatus.ACTIVE


class ExamInstanceBase(BaseModel):
    """Base exam instance schema."""
    examination_id: str
    student_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_extension_minutes: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    biometric_verified: bool = False
    biometric_verification_time: Optional[datetime] = None


class ExamInstanceResponse(ExamInstanceBase):
    """Exam instance response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ExamInstanceStatus
    total_points_earned: int
    total_points_possible: int
    percentage_score: Optional[float]
    grade: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @property
    def duration_taken(self) -> int:
        """Calculate actual duration taken in minutes."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0
    
    @property
    def is_completed(self) -> bool:
        """Check if exam instance is completed."""
        return self.status == ExamInstanceStatus.SUBMITTED
    
    @property
    def is_passed(self) -> bool:
        """Check if student passed the exam."""
        if self.percentage_score is None:
            return False
        return self.percentage_score >= 50.0  # Simplified pass threshold


class ExamSubmissionRequest(BaseModel):
    """Exam submission request schema."""
    answers: List[Dict[str, Any]] = []
    submission_time: Optional[datetime] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class ExamSubmissionResponse(BaseModel):
    """Exam submission response schema."""
    success: bool
    message: str
    instance_id: str
    submission_time: datetime
    total_answers: int
    points_earned: int
    percentage_score: Optional[float]
    grade: Optional[str]


class ExamStartRequest(BaseModel):
    """Exam start request schema."""
    student_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    biometric_verified: bool = False
    biometric_data: Optional[str] = None
    rules_accepted: bool = False


class AnswerSaveRequest(BaseModel):
    """Answer save request."""
    question_id: str
    selected_option_id: Optional[str] = None
    answer_text: Optional[str] = None
    is_flagged: bool = False
    idempotency_key: str

class ProctoringEventRequest(BaseModel):
    """Proctoring event request."""
    event_type: str
    payload: Optional[Dict[str, Any]] = None


class ExamStartResponse(BaseModel):
    """Exam start response schema."""
    success: bool
    message: str
    instance_id: str
    attempt_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    question_count: int
    total_points: int
    biometric_required: bool

    @model_validator(mode="after")
    def sync_attempt_id(self) -> Self:
        if not self.attempt_id:
            self.attempt_id = self.instance_id
        return self


class ExamReviewResponse(BaseModel):
    """Exam review response schema."""
    instance_id: str
    exam_title: str
    student_name: str
    start_time: datetime
    end_time: datetime
    duration_taken: int
    total_points: int
    points_earned: int
    percentage_score: float
    grade: str
    passed: bool
    answers: List[Dict[str, Any]]
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    time_per_question: List[Dict[str, Any]]


class ExamStatisticsResponse(BaseModel):
    """Exam statistics response schema."""
    exam_id: str
    exam_title: str
    total_instances: int
    completed_instances: int
    in_progress_instances: int
    not_started_instances: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    average_duration: float
    completion_rate: float
    score_distribution: Dict[str, int]
    time_distribution: Dict[str, int]


class ExamResultSummary(BaseModel):
    """Exam result summary for student."""
    instance_id: str
    exam_title: str
    exam_date: date
    score: float
    grade: str
    passed: bool
    rank: Optional[int]
    percentile: Optional[float]
    class_average: float
    time_taken: int


class ExamResultDetail(BaseModel):
    """Detailed exam result for student."""
    instance_id: str
    exam_title: str
    course_code: str
    course_title: str
    exam_date: date
    start_time: datetime
    end_time: datetime
    duration_taken: int
    total_points: int
    points_earned: int
    percentage_score: float
    grade: str
    passed: bool
    rank: Optional[int]
    percentile: Optional[float]
    class_average: float
    class_size: int
    answers: List[Dict[str, Any]]
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    time_per_question: List[Dict[str, Any]]


class ExamGradingRequest(BaseModel):
    """Exam grading request schema."""
    auto_grade: bool = True
    publish_results: bool = False
    grading_criteria: Optional[Dict[str, Any]] = None


class ExamGradingResponse(BaseModel):
    """Exam grading response schema."""
    success: bool
    message: str
    total_graded: int
    grading_errors: List[str]
    average_score: float
    pass_rate: float
    grade_distribution: Dict[str, int]


class ExamScheduleRequest(BaseModel):
    """Exam scheduling request schema."""
    exam_date: date
    start_time: datetime
    duration_minutes: int
    venue: Optional[str] = None
    invigilators: Optional[List[str]] = None
    special_instructions: Optional[str] = None


class ExamPublishRequest(BaseModel):
    """Exam publishing request schema."""
    publish_to_students: bool = True
    publish_results: bool = False
    notification_message: Optional[str] = None
    publish_date: Optional[datetime] = None


class ExamCancelRequest(BaseModel):
    """Exam cancellation request schema."""
    reason: str
    notify_students: bool = True
    reschedule_date: Optional[date] = None
    alternative_arrangements: Optional[str] = None


class ExamExtensionRequest(BaseModel):
    """Exam time extension request schema."""
    instance_id: str
    extension_minutes: int
    reason: str
    approved_by: Optional[str] = None


class ExamMonitoringResponse(BaseModel):
    """Real-time exam monitoring response."""
    exam_id: str
    exam_title: str
    total_students: int
    started_students: int
    in_progress_students: int
    completed_students: int
    average_progress: float
    average_time_remaining: int
    technical_issues: List[Dict[str, Any]]
    suspicious_activities: List[Dict[str, Any]]
    last_updated: datetime


class ExamRegisteredStudentResponse(BaseModel):
    """Schema for a student registered for an examination."""
    id: str
    first_name: str
    last_name: str
    email: str
    matric_number: str
    department_id: str
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    is_active: bool

