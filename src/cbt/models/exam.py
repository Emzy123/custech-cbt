"""
Examination and exam instance models using Beanie (MongoDB).
"""

from typing import Optional, Dict, Any
import enum
from datetime import datetime, timedelta
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class ExamStatus(str, enum.Enum):
    """Examination status."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ExamInstanceStatus(str, enum.Enum):
    """Exam instance status."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    TIMED_OUT = "TIMED_OUT"
    ABANDONED = "ABANDONED"


class Examination(BaseDocument):
    """Examination definition and configuration."""

    title: str
    description: Optional[str] = None
    exam_date: datetime
    start_time: datetime
    duration_minutes: int
    total_points: int
    pass_points: Optional[int] = None
    status: ExamStatus = ExamStatus.DRAFT
    randomize_questions: bool = False
    randomize_options: bool = False
    allow_review: bool = False
    show_results_immediately: bool = False
    max_attempts: int = 1
    settings: Optional[Dict[str, Any]] = None
    course_id: str
    academic_session_id: str
    semester_id: str
    created_by: str
    updated_by: Optional[str] = None

    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def is_active_exam(self) -> bool:
        return self.status == ExamStatus.ACTIVE

    class Settings:
        name = "examinations"


class ExamQuestion(BaseDocument):
    """Questions included in an examination."""
    examination_id: str
    question_id: str
    question_order: int
    points_override: Optional[int] = None

    class Settings:
        name = "exam_questions"


class ExamInstance(BaseDocument):
    """Individual student exam instance."""
    examination_id: str
    student_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_extension_minutes: int = 0
    status: ExamInstanceStatus = ExamInstanceStatus.NOT_STARTED
    total_points_earned: int = 0
    total_points_possible: int = 0
    percentage_score: Optional[float] = None
    grade: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    biometric_verified: bool = False
    biometric_verification_time: Optional[datetime] = None

    @property
    def duration_taken(self) -> int:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0

    @property
    def is_completed(self) -> bool:
        return self.status == ExamInstanceStatus.SUBMITTED

    class Settings:
        name = "exam_instances"


class ExamAnswer(BaseDocument):
    """Student's answer to a specific question in an exam."""
    exam_instance_id: str
    question_id: str
    exam_question_id: Optional[str] = None
    selected_option_id: Optional[str] = None
    answer_text: Optional[str] = None
    is_marked_for_review: bool = False
    time_spent_seconds: int = 0
    points_earned: int = 0
    is_correct: Optional[bool] = None

    @property
    def has_answer(self) -> bool:
        return self.selected_option_id is not None or self.answer_text is not None

    class Settings:
        name = "exam_answers"
