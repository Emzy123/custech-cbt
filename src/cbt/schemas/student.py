"""
Student management schemas.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from ..models.student import StudentStatus


class StudentBase(BaseModel):
    """Base student schema."""
    matric_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    admission_year: int
    current_level: int
    department_id: str
    academic_session_id: str
    
    @validator('matric_number')
    def validate_matric_number(cls, v):
        import re
        if not re.match(r'^20\d{2}/\d{6}$', v):
            raise ValueError('Matric number must follow format: 20XX/XXXXXX')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not (v.startswith('+234') and len(v) == 13 and v[4:].isdigit()):
            raise ValueError('Phone number must be in format +234XXXXXXXXXX')
        return v
    
    @validator('current_level')
    def validate_level(cls, v):
        if not 100 <= v <= 900 or v % 100 != 0:
            raise ValueError('Level must be one of 100, 200, 300, 400, 500, 600, 700, 800, 900')
        return v


class StudentCreate(StudentBase):
    """Student creation schema."""
    user_id: str


class StudentUpdate(BaseModel):
    """Student update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    current_level: Optional[int] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    """Student response schema."""
    id: str
    user_id: str
    is_active: bool
    graduated: bool
    graduation_year: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentSearch(BaseModel):
    """Student search parameters."""
    query: Optional[str] = None
    department_id: Optional[str] = None
    level: Optional[int] = None
    status: Optional[StudentStatus] = None
    academic_session: Optional[str] = None
    limit: int = 50
    cursor: Optional[str] = None


class BulkImportRequest(BaseModel):
    """Bulk import request schema."""
    students: List[StudentCreate]
    validate_only: bool = False
    continue_on_error: bool = False


class BulkImportResponse(BaseModel):
    """Bulk import response schema."""
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]]
    import_id: str


class StudentCourseRegistration(BaseModel):
    """Student course registration schema."""
    student_id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    registration_date: date


class StudentStatusUpdate(BaseModel):
    """Student status update schema."""
    status: StudentStatus
    reason: Optional[str] = None
    effective_date: date


class StudentCourseResponse(BaseModel):
    """Student course response schema."""
    id: str
    course_id: str
    course_code: str
    course_title: str
    credit_units: int
    registration_date: date
    status: str
    
    class Config:
        from_attributes = True


class StudentProfileResponse(BaseModel):
    """Student profile response schema."""
    id: str
    user_id: str
    matric_number: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    admission_year: int
    current_level: int
    department_id: str
    department_name: str
    academic_session_id: str
    academic_session_code: str
    is_active: bool
    graduated: bool
    graduation_year: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentSummaryResponse(BaseModel):
    """Student summary response schema."""
    id: str
    matric_number: str
    full_name: str
    email: str
    current_level: int
    department_name: str
    status: StudentStatus
    is_active: bool
    last_login_at: Optional[datetime]


class StudentStatisticsResponse(BaseModel):
    """Student statistics response schema."""
    total_students: int
    active_students: int
    inactive_students: int
    graduated_students: int
    by_level: Dict[int, int]
    by_department: Dict[str, int]
    by_status: Dict[str, int]


class StudentActivityResponse(BaseModel):
    """Student activity response schema."""
    student_id: str
    exam_attempts: int
    exams_completed: int
    average_score: float
    last_exam_date: Optional[datetime]
    course_registrations: int
    recent_activities: List[Dict[str, Any]]
