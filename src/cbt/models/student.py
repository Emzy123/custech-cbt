"""
Student and student course registration models using Beanie (MongoDB).
"""

from typing import Optional
import enum
from datetime import datetime
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class StudentStatus(str, enum.Enum):
    """Student status options."""
    PROSPECTIVE = "PROSPECTIVE"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    GRADUATED = "GRADUATED"
    ALUMNI = "ALUMNI"
    ARCHIVED = "ARCHIVED"


class Student(BaseDocument):
    """Student information and academic record."""

    user_id: str
    department_id: str
    academic_session_id: str
    matric_number: str
    admission_year: int
    current_level: int
    graduation_year: Optional[int] = None
    graduated: bool = False

    @property
    def status(self) -> StudentStatus:
        if self.graduated:
            return StudentStatus.GRADUATED
        elif not self.is_active:
            return StudentStatus.INACTIVE
        return StudentStatus.ACTIVE

    class Settings:
        name = "students"


class StudentCourse(BaseDocument):
    """Student course registration."""

    student_id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    registration_date: datetime
    status: str = "REGISTERED"  # REGISTERED, WITHDRAWN, COMPLETED, FAILED

    @property
    def is_active_registration(self) -> bool:
        return self.status == "REGISTERED"

    class Settings:
        name = "student_courses"
