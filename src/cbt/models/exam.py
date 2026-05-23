"""
Examination, ExamInstance (Session), and Result models using Beanie (MongoDB).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from beanie import Document
from pydantic import Field, field_validator

from .base import BaseDocument
import enum


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
    TERMINATED = "TERMINATED"



class Examination(BaseDocument):
    """Simplified Examination definition."""

    title: str
    course_code: str = "CSC131"
    duration_minutes: int
    total_questions: int = 0
    passing_score: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    start_time: str = "09:00"  # e.g. "09:00"
    end_time: str = "17:00"    # e.g. "17:00"
    is_active: bool = True
    status: ExamStatus = ExamStatus.DRAFT
    created_by: str

    @field_validator("start_time", mode="before")
    @classmethod
    def coerce_start_time(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%H:%M")
        return str(v) if v else "09:00"

    @field_validator("end_time", mode="before")
    @classmethod
    def coerce_end_time(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%H:%M")
        return str(v) if v else "17:00"

    class Settings:
        name = "examinations"


class ExamInstance(BaseDocument):
    """Simplified Student Exam Session."""

    student_id: str
    exam_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime
    answers: List[Dict[str, str]] = []  # list of {"question_id": "...", "selected_option": "A/B/C/D"}
    status: str = "in_progress"         # "in_progress", "submitted", "expired"

    class Settings:
        name = "exam_instances"


class Result(BaseDocument):
    """Simplified Student Exam Result."""

    student_id: str
    exam_id: str
    score: float
    total_questions: int
    percentage: float
    grade: str  # "A", "B", "C", "D", "F"
    date_taken: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "results"
