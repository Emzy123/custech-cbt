"""
Course and academic management schemas.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.academic import CourseLevel, SemesterType


class CourseBase(BaseModel):
    """Base course schema."""
    code: str
    title: str
    description: Optional[str] = None
    credit_units: int
    level: CourseLevel
    semester_type: SemesterType


class CourseCreate(CourseBase):
    """Schema for creating a course."""
    department_ids: Optional[List[str]] = []


class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    title: Optional[str] = None
    description: Optional[str] = None
    credit_units: Optional[int] = None
    level: Optional[CourseLevel] = None
    semester_type: Optional[SemesterType] = None
    is_active: Optional[bool] = None
    department_ids: Optional[List[str]] = None


class CourseResponse(CourseBase):
    """Schema for course response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CourseSearch(BaseModel):
    """Schema for course search parameters."""
    department_id: Optional[str] = None
    level: Optional[CourseLevel] = None
    semester_type: Optional[SemesterType] = None
    is_active: Optional[bool] = None
    query: Optional[str] = None
    limit: int = 50
    cursor: Optional[str] = None


class AcademicSessionBase(BaseModel):
    """Base academic session schema."""
    session_code: str
    start_date: datetime
    end_date: datetime


class AcademicSessionCreate(AcademicSessionBase):
    """Schema for creating academic session."""
    pass


class AcademicSessionUpdate(BaseModel):
    """Schema for updating academic session."""
    session_code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: Optional[bool] = None


class AcademicSessionResponse(AcademicSessionBase):
    """Schema for academic session response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_current: bool
    created_at: datetime
    updated_at: datetime


class SemesterBase(BaseModel):
    """Base semester schema."""
    academic_session_id: str
    semester_type: SemesterType
    start_date: datetime
    end_date: datetime


class SemesterCreate(SemesterBase):
    """Schema for creating semester."""
    pass


class SemesterResponse(SemesterBase):
    """Schema for semester response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_current: bool
    created_at: datetime
    updated_at: datetime


class CourseDepartmentAssignment(BaseModel):
    """Schema for course-department assignment."""
    course_id: str
    department_id: str
    is_mandatory: bool = False


class CurriculumPlan(BaseModel):
    """Schema for curriculum planning."""
    department_id: str
    level: CourseLevel
    semester_type: SemesterType
    courses: List[str]  # Course IDs


class StudentCourseRegistration(BaseModel):
    """Schema for student course registration."""
    student_id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    registration_date: datetime
