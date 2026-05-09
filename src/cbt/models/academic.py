"""
Academic structure models: sessions, semesters, departments, and courses using Beanie (MongoDB).
"""

from typing import Optional
import enum
from datetime import datetime
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class SemesterType(str, enum.Enum):
    """Semester types."""
    FIRST = "FIRST"
    SECOND = "SECOND"


class AcademicSession(BaseDocument):
    """Academic session (e.g., 2026/2027)."""
    session_code: str
    start_date: datetime
    end_date: datetime
    is_current: bool = False

    @property
    def display_name(self) -> str:
        return self.session_code

    class Settings:
        name = "academic_sessions"


class Semester(BaseDocument):
    """Semester within an academic session."""
    academic_session_id: str
    semester_type: SemesterType
    start_date: datetime
    end_date: datetime
    is_current: bool = False

    class Settings:
        name = "semesters"


class Department(BaseDocument):
    """Academic department."""
    code: str
    name: str
    faculty_code: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.code} - {self.name}"

    class Settings:
        name = "departments"


class CourseLevel(int, enum.Enum):
    """Course levels."""
    LEVEL_100 = 100
    LEVEL_200 = 200
    LEVEL_300 = 300
    LEVEL_400 = 400
    LEVEL_500 = 500
    LEVEL_600 = 600
    LEVEL_700 = 700
    LEVEL_800 = 800
    LEVEL_900 = 900


class Course(BaseDocument):
    """Course information."""
    code: str
    title: str
    description: Optional[str] = None
    credit_units: int
    level: CourseLevel
    semester_type: SemesterType
    created_by: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.code} - {self.title}"

    @property
    def level_name(self) -> str:
        return str(self.level.value)

    class Settings:
        name = "courses"


class CourseDepartment(BaseDocument):
    """Course-Department many-to-many relationship."""
    course_id: str
    department_id: str
    is_mandatory: bool = False

    class Settings:
        name = "course_departments"
