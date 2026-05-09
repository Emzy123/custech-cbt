# Course and Curriculum Management API

## Overview

This document defines the comprehensive Course and Curriculum Management API for the CBT system, providing endpoints for course creation, curriculum management, academic session handling, and departmental course assignments.

## API Architecture

### RESTful Design Principles
```
Base URL: https://api.cbt.custech.edu.ng/api/v1
Authentication: JWT Bearer Token
Content-Type: application/json
Rate Limiting: 100 requests per minute per user
Pagination: Cursor-based for large datasets
```

### Academic Structure
```
Academic Session → Semester → Courses → Departments → Students
2026/2027        → First   → GST111 → Computer Science → 100L Students
                 → Second  → GST112 → All Departments → 100L Students
```

### Data Models
```python
# models/course.py
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class SemesterType(str, Enum):
    FIRST = "FIRST"
    SECOND = "SECOND"

class CourseLevel(int, Enum):
    LEVEL_100 = 100
    LEVEL_200 = 200
    LEVEL_300 = 300
    LEVEL_400 = 400
    LEVEL_500 = 500
    LEVEL_600 = 600
    LEVEL_700 = 700
    LEVEL_800 = 800
    LEVEL_900 = 900

class CourseBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    credit_units: int
    level: CourseLevel
    semester_type: SemesterType

class CourseCreate(CourseBase):
    department_id: Optional[str] = None
    
    @validator('code')
    def validate_code(cls, v):
        import re
        if not re.match(r'^[A-Z]{3,4}\d{3,4}$', v):
            raise ValueError('Course code must follow format: ABC123 or ABCD1234')
        return v
    
    @validator('credit_units')
    def validate_credit_units(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Credit units must be between 1 and 10')
        return v

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    credit_units: Optional[int] = None
    is_active: Optional[bool] = None

class CourseResponse(CourseBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class AcademicSessionBase(BaseModel):
    session_code: str
    start_date: date
    end_date: date

class AcademicSessionCreate(AcademicSessionBase):
    pass

class AcademicSessionUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

class AcademicSessionResponse(AcademicSessionBase):
    id: str
    is_current: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SemesterBase(BaseModel):
    academic_session_id: str
    semester_type: SemesterType
    start_date: date
    end_date: date

class SemesterCreate(SemesterBase):
    pass

class SemesterResponse(SemesterBase):
    id: str
    is_current: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CourseDepartmentAssignment(BaseModel):
    course_id: str
    department_id: str
    is_mandatory: bool = False

class CurriculumPlan(BaseModel):
    academic_session_id: str
    courses: List[CourseDepartmentAssignment]

class StudentCourseRegistration(BaseModel):
    student_id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    registration_date: date

class CourseSearch(BaseModel):
    query: Optional[str] = None
    department_id: Optional[str] = None
    level: Optional[CourseLevel] = None
    semester_type: Optional[SemesterType] = None
    is_active: Optional[bool] = None
    limit: int = 50
    cursor: Optional[str] = None
```

---

## API Endpoints

### 1. Academic Session Management

#### Academic Session CRUD
```python
# api/academic_sessions.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.course import (
    AcademicSessionCreate, AcademicSessionUpdate, AcademicSessionResponse
)
from ..services.course_service import CourseService
from ..middleware.authorization_middleware import require_permission
from ..authorization import Permission

router = APIRouter(prefix="/academic-sessions", tags=["academic-sessions"])

@router.post("/", response_model=AcademicSessionResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.COURSE_CREATE)
async def create_academic_session(
    session_data: AcademicSessionCreate,
    course_service: CourseService = Depends()
):
    """Create a new academic session"""
    try:
        session = await course_service.create_academic_session(session_data)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[AcademicSessionResponse])
@require_permission(Permission.COURSE_READ)
async def list_academic_sessions(
    is_current: Optional[bool] = Query(None),
    course_service: CourseService = Depends()
):
    """List all academic sessions"""
    sessions = await course_service.list_academic_sessions(is_current)
    return sessions

@router.get("/{session_id}", response_model=AcademicSessionResponse)
@require_permission(Permission.COURSE_READ)
async def get_academic_session(
    session_id: str,
    course_service: CourseService = Depends()
):
    """Get academic session by ID"""
    session = await course_service.get_academic_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found"
        )
    return session

@router.put("/{session_id}", response_model=AcademicSessionResponse)
@require_permission(Permission.COURSE_UPDATE)
async def update_academic_session(
    session_id: str,
    session_data: AcademicSessionUpdate,
    course_service: CourseService = Depends()
):
    """Update academic session"""
    try:
        session = await course_service.update_academic_session(session_id, session_data)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found"
            )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{session_id}/set-current")
@require_permission(Permission.COURSE_UPDATE)
async def set_current_session(
    session_id: str,
    course_service: CourseService = Depends()
):
    """Set academic session as current"""
    try:
        session = await course_service.set_current_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found"
            )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
```

#### Semester Management
```python
@router.post("/{session_id}/semesters", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.COURSE_CREATE)
async def create_semester(
    session_id: str,
    semester_data: SemesterCreate,
    course_service: CourseService = Depends()
):
    """Create a new semester"""
    try:
        semester = await course_service.create_semester(session_id, semester_data)
        return semester
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{session_id}/semesters", response_model=List[SemesterResponse])
@require_permission(Permission.COURSE_READ)
async def list_semesters(
    session_id: str,
    is_current: Optional[bool] = Query(None),
    course_service: CourseService = Depends()
):
    """List semesters for academic session"""
    semesters = await course_service.list_semesters(session_id, is_current)
    return semesters

@router.get("/{session_id}/semesters/{semester_id}", response_model=SemesterResponse)
@require_permission(Permission.COURSE_READ)
async def get_semester(
    session_id: str,
    semester_id: str,
    course_service: CourseService = Depends()
):
    """Get semester by ID"""
    semester = await course_service.get_semester(semester_id)
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found"
        )
    return semester

@router.post("/{session_id}/semesters/{semester_id}/set-current")
@require_permission(Permission.COURSE_UPDATE)
async def set_current_semester(
    session_id: str,
    semester_id: str,
    course_service: CourseService = Depends()
):
    """Set semester as current"""
    try:
        semester = await course_service.set_current_semester(semester_id)
        if not semester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Semester not found"
            )
        return semester
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
```

### 2. Course Management

#### Course CRUD Operations
```python
# api/courses.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseSearch
)
from ..services.course_service import CourseService
from ..middleware.authorization_middleware import require_permission
from ..authorization import Permission

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.COURSE_CREATE)
async def create_course(
    course_data: CourseCreate,
    course_service: CourseService = Depends()
):
    """Create a new course"""
    try:
        course = await course_service.create_course(course_data)
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[CourseResponse])
@require_permission(Permission.COURSE_READ)
async def list_courses(
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    semester_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    course_service: CourseService = Depends()
):
    """List courses with filtering and pagination"""
    search_params = CourseSearch(
        department_id=department_id,
        level=level,
        semester_type=semester_type,
        is_active=is_active,
        limit=limit,
        cursor=cursor
    )
    
    courses = await course_service.list_courses(search_params)
    return courses

@router.get("/search", response_model=List[CourseResponse])
@require_permission(Permission.COURSE_READ)
async def search_courses(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    course_service: CourseService = Depends()
):
    """Search courses by code or title"""
    courses = await course_service.search_courses(query, limit)
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
@require_permission(Permission.COURSE_READ)
async def get_course(
    course_id: str,
    course_service: CourseService = Depends()
):
    """Get course by ID"""
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.get("/code/{course_code}", response_model=CourseResponse)
@require_permission(Permission.COURSE_READ)
async def get_course_by_code(
    course_code: str,
    course_service: CourseService = Depends()
):
    """Get course by code"""
    course = await course_service.get_course_by_code(course_code)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.put("/{course_id}", response_model=CourseResponse)
@require_permission(Permission.COURSE_UPDATE)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    course_service: CourseService = Depends()
):
    """Update course"""
    try:
        course = await course_service.update_course(course_id, course_data)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission(Permission.COURSE_DELETE)
async def delete_course(
    course_id: str,
    course_service: CourseService = Depends()
):
    """Delete course (soft delete)"""
    success = await course_service.delete_course(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
```

### 3. Department Course Assignment

#### Course Department Management
```python
@router.post("/{course_id}/departments")
@require_permission(Permission.COURSE_UPDATE)
async def assign_course_to_department(
    course_id: str,
    assignment: CourseDepartmentAssignment,
    course_service: CourseService = Depends()
):
    """Assign course to department"""
    try:
        result = await course_service.assign_course_to_department(
            course_id, assignment.department_id, assignment.is_mandatory
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{course_id}/departments")
@require_permission(Permission.COURSE_READ)
async def get_course_departments(
    course_id: str,
    course_service: CourseService = Depends()
):
    """Get departments offering this course"""
    departments = await course_service.get_course_departments(course_id)
    return departments

@router.delete("/{course_id}/departments/{department_id}")
@require_permission(Permission.COURSE_UPDATE)
async def remove_course_from_department(
    course_id: str,
    department_id: str,
    course_service: CourseService = Depends()
):
    """Remove course from department"""
    try:
        result = await course_service.remove_course_from_department(course_id, department_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )

@router.get("/department/{department_id}/courses")
@require_permission(Permission.COURSE_READ)
async def get_department_courses(
    department_id: str,
    level: Optional[int] = Query(None),
    semester_type: Optional[str] = Query(None),
    is_mandatory: Optional[bool] = Query(None),
    course_service: CourseService = Depends()
):
    """Get courses offered by department"""
    courses = await course_service.get_department_courses(
        department_id, level, semester_type, is_mandatory
    )
    return courses
```

### 4. Curriculum Management

#### Curriculum Planning
```python
@router.post("/curriculum/plan")
@require_permission(Permission.COURSE_CREATE)
async def create_curriculum_plan(
    curriculum_plan: CurriculumPlan,
    course_service: CourseService = Depends()
):
    """Create curriculum plan for academic session"""
    try:
        result = await course_service.create_curriculum_plan(curriculum_plan)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )

@router.get("/curriculum/{session_id}")
@require_permission(Permission.COURSE_READ)
async def get_curriculum_plan(
    session_id: str,
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    course_service: CourseService = Depends()
):
    """Get curriculum plan for academic session"""
    curriculum = await course_service.get_curriculum_plan(
        session_id, department_id, level
    )
    return curriculum

@router.post("/curriculum/{session_id}/activate")
@require_permission(Permission.COURSE_UPDATE)
async def activate_curriculum_plan(
    session_id: str,
    course_service: CourseService = Depends()
):
    """Activate curriculum plan for registration"""
    try:
        result = await course_service.activate_curriculum_plan(session_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
```

### 5. Course Registration Management

#### Student Course Registration
```python
@router.post("/registration")
@require_permission(Permission.STUDENT_UPDATE)
async def register_student_for_course(
    registration: StudentCourseRegistration,
    course_service: CourseService = Depends()
):
    """Register student for course"""
    try:
        result = await course_service.register_student_for_course(registration)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/students/{student_id}/courses")
@require_permission(Permission.STUDENT_READ)
async def get_student_registered_courses(
    student_id: str,
    academic_session_id: Optional[str] = Query(None),
    semester_id: Optional[str] = Query(None),
    course_service: CourseService = Depends()
):
    """Get courses registered by student"""
    courses = await course_service.get_student_registered_courses(
        student_id, academic_session_id, semester_id
    )
    return courses

@router.get("/courses/{course_id}/students")
@require_permission(Permission.STUDENT_READ)
async def get_course_registered_students(
    course_id: str,
    academic_session_id: Optional[str] = Query(None),
    semester_id: Optional[str] = Query(None),
    course_service: CourseService = Depends()
):
    """Get students registered for course"""
    students = await course_service.get_course_registered_students(
        course_id, academic_session_id, semester_id
    )
    return students

@router.delete("/registration/{registration_id}")
@require_permission(Permission.STUDENT_UPDATE)
async def withdraw_student_from_course(
    registration_id: str,
    course_service: CourseService = Depends()
):
    """Withdraw student from course"""
    try:
        result = await course_service.withdraw_student_from_course(registration_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
```

---

## Service Implementation

### Course Service
```python
# services/course_service.py
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete

from ..models.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseSearch,
    AcademicSessionCreate, AcademicSessionUpdate, AcademicSessionResponse,
    SemesterCreate, SemesterResponse, CourseDepartmentAssignment,
    CurriculumPlan, StudentCourseRegistration
)
from ..models.database import (
    Course, Department, AcademicSession, Semester, 
    CourseDepartment, StudentCourse
)
from ..services.validation_service import ValidationService
from ..services.audit_service import AuditService

class CourseService:
    def __init__(self, db: AsyncSession, validation_service: ValidationService,
                 audit_service: AuditService):
        self.db = db
        self.validation_service = validation_service
        self.audit_service = audit_service
    
    # Academic Session Management
    async def create_academic_session(self, session_data: AcademicSessionCreate) -> AcademicSessionResponse:
        """Create a new academic session"""
        # Validate session code format
        import re
        if not re.match(r'^\d{4}/\d{4}$', session_data.session_code):
            raise ValueError("Session code must follow format: YYYY/YYYY")
        
        # Validate dates
        if session_data.start_date >= session_data.end_date:
            raise ValueError("Start date must be before end date")
        
        # Check for existing session
        existing = await self.db.execute(
            select(AcademicSession).where(AcademicSession.session_code == session_data.session_code)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Session code already exists")
        
        # Create session
        session = AcademicSession(
            id=str(uuid.uuid4()),
            session_code=session_data.session_code,
            start_date=session_data.start_date,
            end_date=session_data.end_date,
            is_current=False
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Log audit
        await self.audit_service.log_action(
            action="CREATE_ACADEMIC_SESSION",
            resource_type="academic_session",
            resource_id=session.id,
            details=f"Created academic session {session_data.session_code}"
        )
        
        return AcademicSessionResponse.from_orm(session)
    
    async def list_academic_sessions(self, is_current: Optional[bool] = None) -> List[AcademicSessionResponse]:
        """List academic sessions"""
        query = select(AcademicSession)
        
        if is_current is not None:
            query = query.where(AcademicSession.is_current == is_current)
        
        query = query.order_by(AcademicSession.start_date.desc())
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        return [AcademicSessionResponse.from_orm(session) for session in sessions]
    
    async def get_academic_session(self, session_id: str) -> Optional[AcademicSessionResponse]:
        """Get academic session by ID"""
        result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        return AcademicSessionResponse.from_orm(session) if session else None
    
    async def update_academic_session(self, session_id: str, 
                                    session_data: AcademicSessionUpdate) -> Optional[AcademicSessionResponse]:
        """Update academic session"""
        result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        
        # Update fields
        update_dict = session_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(session, field):
                setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        
        # Log audit
        await self.audit_service.log_action(
            action="UPDATE_ACADEMIC_SESSION",
            resource_type="academic_session",
            resource_id=session.id,
            details=f"Updated academic session {session.session_code}"
        )
        
        return AcademicSessionResponse.from_orm(session)
    
    async def set_current_session(self, session_id: str) -> Optional[AcademicSessionResponse]:
        """Set academic session as current"""
        # Unset all current sessions
        await self.db.execute(
            update(AcademicSession).where(AcademicSession.is_current == True)
            .values(is_current=False)
        )
        
        # Set new current session
        result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        
        session.is_current = True
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        
        # Log audit
        await self.audit_service.log_action(
            action="SET_CURRENT_SESSION",
            resource_type="academic_session",
            resource_id=session.id,
            details=f"Set current session to {session.session_code}"
        )
        
        return AcademicSessionResponse.from_orm(session)
    
    # Semester Management
    async def create_semester(self, session_id: str, 
                            semester_data: SemesterCreate) -> SemesterResponse:
        """Create a new semester"""
        # Validate session exists
        session_result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == session_id)
        )
        if not session_result.scalar_one_or_none():
            raise ValueError("Academic session not found")
        
        # Check for duplicate semester
        existing = await self.db.execute(
            select(Semester).where(
                and_(
                    Semester.academic_session_id == session_id,
                    Semester.semester_type == semester_data.semester_type
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Semester already exists for this session")
        
        # Validate dates are within session period
        session = session_result.scalar_one()
        if (semester_data.start_date < session.start_date or 
            semester_data.end_date > session.end_date):
            raise ValueError("Semester dates must be within academic session period")
        
        # Create semester
        semester = Semester(
            id=str(uuid.uuid4()),
            academic_session_id=session_id,
            semester_type=semester_data.semester_type,
            start_date=semester_data.start_date,
            end_date=semester_data.end_date,
            is_current=False
        )
        
        self.db.add(semester)
        await self.db.commit()
        await self.db.refresh(semester)
        
        # Log audit
        await self.audit_service.log_action(
            action="CREATE_SEMESTER",
            resource_type="semester",
            resource_id=semester.id,
            details=f"Created {semester_data.semester_type.value} semester"
        )
        
        return SemesterResponse.from_orm(semester)
    
    async def list_semesters(self, session_id: str, 
                           is_current: Optional[bool] = None) -> List[SemesterResponse]:
        """List semesters for academic session"""
        query = select(Semester).where(Semester.academic_session_id == session_id)
        
        if is_current is not None:
            query = query.where(Semester.is_current == is_current)
        
        query = query.order_by(Semester.start_date)
        
        result = await self.db.execute(query)
        semesters = result.scalars().all()
        
        return [SemesterResponse.from_orm(semester) for semester in semesters]
    
    async def get_semester(self, semester_id: str) -> Optional[SemesterResponse]:
        """Get semester by ID"""
        result = await self.db.execute(
            select(Semester).where(Semester.id == semester_id)
        )
        semester = result.scalar_one_or_none()
        return SemesterResponse.from_orm(semester) if semester else None
    
    async def set_current_semester(self, semester_id: str) -> Optional[SemesterResponse]:
        """Set semester as current"""
        # Get semester
        result = await self.db.execute(
            select(Semester).where(Semester.id == semester_id)
        )
        semester = result.scalar_one_or_none()
        if not semester:
            return None
        
        # Unset other current semesters in same session
        await self.db.execute(
            update(Semester).where(
                and_(
                    Semester.academic_session_id == semester.academic_session_id,
                    Semester.is_current == True
                )
            ).values(is_current=False)
        )
        
        # Set new current semester
        semester.is_current = True
        
        await self.db.commit()
        await self.db.refresh(semester)
        
        # Log audit
        await self.audit_service.log_action(
            action="SET_CURRENT_SEMESTER",
            resource_type="semester",
            resource_id=semester.id,
            details=f"Set current semester to {semester.semester_type.value}"
        )
        
        return SemesterResponse.from_orm(semester)
    
    # Course Management
    async def create_course(self, course_data: CourseCreate) -> CourseResponse:
        """Create a new course"""
        # Validate course code uniqueness
        existing = await self.db.execute(
            select(Course).where(Course.code == course_data.code)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Course code already exists")
        
        # Validate department if provided
        if course_data.department_id:
            dept_result = await self.db.execute(
                select(Department).where(Department.id == course_data.department_id)
            )
            if not dept_result.scalar_one_or_none():
                raise ValueError("Department not found")
        
        # Create course
        course = Course(
            id=str(uuid.uuid4()),
            code=course_data.code,
            title=course_data.title,
            description=course_data.description,
            credit_units=course_data.credit_units,
            level=course_data.level,
            semester_type=course_data.semester_type,
            is_active=True,
            created_by=course_data.created_by  # Would come from auth context
        )
        
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        
        # Auto-assign to department if provided
        if course_data.department_id:
            await self.assign_course_to_department(
                course.id, course_data.department_id, is_mandatory=False
            )
        
        # Log audit
        await self.audit_service.log_action(
            action="CREATE_COURSE",
            resource_type="course",
            resource_id=course.id,
            details=f"Created course {course_data.code}: {course_data.title}"
        )
        
        return CourseResponse.from_orm(course)
    
    async def list_courses(self, search_params: CourseSearch) -> List[CourseResponse]:
        """List courses with filtering"""
        query = select(Course)
        
        # Apply filters
        if search_params.department_id:
            query = query.join(CourseDepartment).where(
                CourseDepartment.department_id == search_params.department_id
            )
        
        if search_params.level:
            query = query.where(Course.level == search_params.level)
        
        if search_params.semester_type:
            query = query.where(Course.semester_type == search_params.semester_type)
        
        if search_params.is_active is not None:
            query = query.where(Course.is_active == search_params.is_active)
        
        # Apply search query
        if search_params.query:
            search_filter = or_(
                Course.code.ilike(f"%{search_params.query}%"),
                Course.title.ilike(f"%{search_params.query}%")
            )
            query = query.where(search_filter)
        
        # Apply pagination
        query = query.limit(search_params.limit)
        
        if search_params.cursor:
            query = query.where(Course.id > search_params.cursor)
        
        # Order by code
        query = query.order_by(Course.code)
        
        result = await self.db.execute(query)
        courses = result.scalars().all()
        
        return [CourseResponse.from_orm(course) for course in courses]
    
    async def search_courses(self, query: str, limit: int = 20) -> List[CourseResponse]:
        """Search courses by code or title"""
        search_filter = or_(
            Course.code.ilike(f"%{query}%"),
            Course.title.ilike(f"%{query}%")
        )
        
        db_query = select(Course).where(search_filter).limit(limit)
        result = await self.db.execute(db_query)
        courses = result.scalars().all()
        
        return [CourseResponse.from_orm(course) for course in courses]
    
    async def get_course(self, course_id: str) -> Optional[CourseResponse]:
        """Get course by ID"""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        return CourseResponse.from_orm(course) if course else None
    
    async def get_course_by_code(self, course_code: str) -> Optional[CourseResponse]:
        """Get course by code"""
        result = await self.db.execute(
            select(Course).where(Course.code == course_code)
        )
        course = result.scalar_one_or_none()
        return CourseResponse.from_orm(course) if course else None
    
    async def update_course(self, course_id: str, 
                         course_data: CourseUpdate) -> Optional[CourseResponse]:
        """Update course"""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        if not course:
            return None
        
        # Update fields
        update_dict = course_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(course, field):
                setattr(course, field, value)
        
        course.updated_at = datetime.utcnow()
        course.updated_by = course_data.updated_by  # Would come from auth context
        
        await self.db.commit()
        await self.db.refresh(course)
        
        # Log audit
        await self.audit_service.log_action(
            action="UPDATE_COURSE",
            resource_type="course",
            resource_id=course.id,
            details=f"Updated course {course.code}"
        )
        
        return CourseResponse.from_orm(course)
    
    async def delete_course(self, course_id: str) -> bool:
        """Delete course (soft delete)"""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        if not course:
            return False
        
        # Soft delete
        course.is_active = False
        course.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Log audit
        await self.audit_service.log_action(
            action="DELETE_COURSE",
            resource_type="course",
            resource_id=course.id,
            details=f"Deleted course {course.code}"
        )
        
        return True
    
    # Department Assignment Management
    async def assign_course_to_department(self, course_id: str, department_id: str,
                                         is_mandatory: bool = False) -> bool:
        """Assign course to department"""
        # Validate course exists
        course_result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        if not course_result.scalar_one_or_none():
            raise ValueError("Course not found")
        
        # Validate department exists
        dept_result = await self.db.execute(
            select(Department).where(Department.id == department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise ValueError("Department not found")
        
        # Check for existing assignment
        existing = await self.db.execute(
            select(CourseDepartment).where(
                and_(
                    CourseDepartment.course_id == course_id,
                    CourseDepartment.department_id == department_id
                )
            )
        )
        if existing.scalar_one_or_none():
            # Update existing assignment
            assignment = existing.scalar_one()
            assignment.is_mandatory = is_mandatory
        else:
            # Create new assignment
            assignment = CourseDepartment(
                id=str(uuid.uuid4()),
                course_id=course_id,
                department_id=department_id,
                is_mandatory=is_mandatory
            )
            self.db.add(assignment)
        
        await self.db.commit()
        
        # Log audit
        await self.audit_service.log_action(
            action="ASSIGN_COURSE_TO_DEPARTMENT",
            resource_type="course_department",
            resource_id=assignment.id,
            details=f"Assigned course {course_id} to department {department_id}"
        )
        
        return True
    
    async def get_course_departments(self, course_id: str) -> List[Dict[str, Any]]:
        """Get departments offering this course"""
        query = select(
            Department.id,
            Department.code,
            Department.name,
            CourseDepartment.is_mandatory
        ).join(
            CourseDepartment, Department.id == CourseDepartment.department_id
        ).where(
            CourseDepartment.course_id == course_id
        )
        
        result = await self.db.execute(query)
        assignments = result.all()
        
        return [
            {
                "id": assignment.id,
                "code": assignment.code,
                "name": assignment.name,
                "is_mandatory": assignment.is_mandatory
            }
            for assignment in assignments
        ]
    
    async def get_department_courses(self, department_id: str, level: Optional[int] = None,
                                    semester_type: Optional[str] = None,
                                    is_mandatory: Optional[bool] = None) -> List[CourseResponse]:
        """Get courses offered by department"""
        query = select(Course).join(
            CourseDepartment, Course.id == CourseDepartment.course_id
        ).where(
            CourseDepartment.department_id == department_id
        )
        
        if level:
            query = query.where(Course.level == level)
        
        if semester_type:
            query = query.where(Course.semester_type == semester_type)
        
        if is_mandatory is not None:
            query = query.where(CourseDepartment.is_mandatory == is_mandatory)
        
        query = query.where(Course.is_active == True)
        query = query.order_by(Course.code)
        
        result = await self.db.execute(query)
        courses = result.scalars().all()
        
        return [CourseResponse.from_orm(course) for course in courses]
    
    async def remove_course_from_department(self, course_id: str, department_id: str) -> bool:
        """Remove course from department"""
        result = await self.db.execute(
            select(CourseDepartment).where(
                and_(
                    CourseDepartment.course_id == course_id,
                    CourseDepartment.department_id == department_id
                )
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False
        
        await self.db.delete(assignment)
        await self.db.commit()
        
        # Log audit
        await self.audit_service.log_action(
            action="REMOVE_COURSE_FROM_DEPARTMENT",
            resource_type="course_department",
            resource_id=assignment.id,
            details=f"Removed course {course_id} from department {department_id}"
        )
        
        return True
    
    # Curriculum Management
    async def create_curriculum_plan(self, curriculum_plan: CurriculumPlan) -> Dict[str, Any]:
        """Create curriculum plan for academic session"""
        # Validate academic session
        session_result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == curriculum_plan.academic_session_id)
        )
        if not session_result.scalar_one_or_none():
            raise ValueError("Academic session not found")
        
        # Process course assignments
        created_assignments = []
        errors = []
        
        for assignment in curriculum_plan.courses:
            try:
                success = await self.assign_course_to_department(
                    assignment.course_id, assignment.department_id, assignment.is_mandatory
                )
                if success:
                    created_assignments.append(assignment)
                else:
                    errors.append(f"Failed to assign course {assignment.course_id} to department {assignment.department_id}")
            except ValueError as e:
                errors.append(f"Error assigning course {assignment.course_id}: {str(e)}")
        
        return {
            "academic_session_id": curriculum_plan.academic_session_id,
            "total_assignments": len(curriculum_plan.courses),
            "successful_assignments": len(created_assignments),
            "failed_assignments": len(errors),
            "errors": errors
        }
    
    async def get_curriculum_plan(self, session_id: str, department_id: Optional[str] = None,
                                level: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get curriculum plan for academic session"""
        query = select(
            Course.id,
            Course.code,
            Course.title,
            Course.credit_units,
            Course.level,
            Course.semester_type,
            Department.id.label("department_id"),
            Department.code.label("department_code"),
            Department.name.label("department_name"),
            CourseDepartment.is_mandatory
        ).join(
            CourseDepartment, Course.id == CourseDepartment.course_id
        ).join(
            Department, CourseDepartment.department_id == Department.id
        ).where(
            Course.is_active == True
        )
        
        if department_id:
            query = query.where(CourseDepartment.department_id == department_id)
        
        if level:
            query = query.where(Course.level == level)
        
        query = query.order_by(Course.level, Course.semester_type, Course.code)
        
        result = await self.db.execute(query)
        courses = result.all()
        
        return [
            {
                "id": course.id,
                "code": course.code,
                "title": course.title,
                "credit_units": course.credit_units,
                "level": course.level,
                "semester_type": course.semester_type,
                "department": {
                    "id": course.department_id,
                    "code": course.department_code,
                    "name": course.department_name
                },
                "is_mandatory": course.is_mandatory
            }
            for course in courses
        ]
    
    # Student Registration Management
    async def register_student_for_course(self, registration: StudentCourseRegistration) -> Dict[str, Any]:
        """Register student for course"""
        # Validate student exists and is active
        student_result = await self.db.execute(
            select(Student).where(
                and_(
                    Student.id == registration.student_id,
                    Student.is_active == True
                )
            )
        )
        student = student_result.scalar_one_or_none()
        if not student:
            raise ValueError("Student not found or inactive")
        
        # Validate course exists and is active
        course_result = await self.db.execute(
            select(Course).where(Course.id == registration.course_id)
        )
        course = course_result.scalar_one_or_none()
        if not course or not course.is_active:
            raise ValueError("Course not found or inactive")
        
        # Check for existing registration
        existing = await self.db.execute(
            select(StudentCourse).where(
                and_(
                    StudentCourse.student_id == registration.student_id,
                    StudentCourse.course_id == registration.course_id,
                    StudentCourse.academic_session_id == registration.academic_session_id,
                    StudentCourse.semester_id == registration.semester_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Student already registered for this course")
        
        # Check if student is eligible (department assignment)
        dept_check = await self.db.execute(
            select(CourseDepartment).where(
                and_(
                    CourseDepartment.course_id == registration.course_id,
                    CourseDepartment.department_id == student.department_id
                )
            )
        )
        if not dept_check.scalar_one_or_none():
            raise ValueError("Student not eligible for this course")
        
        # Create registration
        student_course = StudentCourse(
            id=str(uuid.uuid4()),
            student_id=registration.student_id,
            course_id=registration.course_id,
            academic_session_id=registration.academic_session_id,
            semester_id=registration.semester_id,
            registration_date=registration.registration_date,
            status="REGISTERED"
        )
        
        self.db.add(student_course)
        await self.db.commit()
        await self.db.refresh(student_course)
        
        # Log audit
        await self.audit_service.log_action(
            action="REGISTER_STUDENT_FOR_COURSE",
            resource_type="student_course",
            resource_id=student_course.id,
            details=f"Registered student {registration.student_id} for course {registration.course_id}"
        )
        
        return {
            "registration_id": student_course.id,
            "student_id": registration.student_id,
            "course_id": registration.course_id,
            "status": "REGISTERED",
            "registration_date": registration.registration_date
        }
    
    async def get_student_registered_courses(self, student_id: str,
                                           academic_session_id: Optional[str] = None,
                                           semester_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get courses registered by student"""
        query = select(
            Course.id,
            Course.code,
            Course.title,
            Course.credit_units,
            StudentCourse.registration_date,
            StudentCourse.status
        ).join(
            StudentCourse, Course.id == StudentCourse.course_id
        ).where(
            StudentCourse.student_id == student_id
        )
        
        if academic_session_id:
            query = query.where(StudentCourse.academic_session_id == academic_session_id)
        
        if semester_id:
            query = query.where(StudentCourse.semester_id == semester_id)
        
        query = query.order_by(Course.code)
        
        result = await self.db.execute(query)
        courses = result.all()
        
        return [
            {
                "id": course.id,
                "code": course.code,
                "title": course.title,
                "credit_units": course.credit_units,
                "registration_date": course.registration_date,
                "status": course.status
            }
            for course in courses
        ]
```

---

## Performance Optimization

### Course Caching Strategy
```python
# services/course_cache_service.py
import redis
import json
from typing import Optional, List
from ..models.course import CourseResponse, AcademicSessionResponse

class CourseCacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.cache_ttl = 600  # 10 minutes
        self.curriculum_ttl = 1800  # 30 minutes
    
    async def get_course(self, course_id: str) -> Optional[CourseResponse]:
        """Get course from cache"""
        key = f"course:{course_id}"
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            course_dict = json.loads(cached_data)
            return CourseResponse(**course_dict)
        
        return None
    
    async def cache_course(self, course: CourseResponse):
        """Cache course data"""
        key = f"course:{course.id}"
        course_json = json.dumps(course.dict())
        self.redis_client.setex(key, self.cache_ttl, course_json)
    
    async def get_course_by_code(self, course_code: str) -> Optional[CourseResponse]:
        """Get course by code from cache"""
        key = f"course:code:{course_code}"
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            course_dict = json.loads(cached_data)
            return CourseResponse(**course_dict)
        
        return None
    
    async def cache_course_by_code(self, course_code: str, course: CourseResponse):
        """Cache course by code"""
        key = f"course:code:{course_code}"
        course_json = json.dumps(course.dict())
        self.redis_client.setex(key, self.cache_ttl, course_json)
    
    async def get_curriculum_plan(self, session_id: str, department_id: Optional[str] = None,
                                level: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """Get curriculum plan from cache"""
        cache_key = f"curriculum:{session_id}"
        if department_id:
            cache_key += f":dept:{department_id}"
        if level:
            cache_key += f":level:{level}"
        
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    async def cache_curriculum_plan(self, session_id: str, curriculum: List[Dict[str, Any]],
                                  department_id: Optional[str] = None, level: Optional[int] = None):
        """Cache curriculum plan"""
        cache_key = f"curriculum:{session_id}"
        if department_id:
            cache_key += f":dept:{department_id}"
        if level:
            cache_key += f":level:{level}"
        
        curriculum_json = json.dumps(curriculum)
        self.redis_client.setex(cache_key, self.curriculum_ttl, curriculum_json)
    
    async def invalidate_course(self, course_id: str):
        """Remove course from cache"""
        # Invalidate by ID
        key = f"course:{course_id}"
        self.redis_client.delete(key)
        
        # Get course code and invalidate by code
        course = await self.get_course(course_id)
        if course:
            code_key = f"course:code:{course.code}"
            self.redis_client.delete(code_key)
    
    async def invalidate_curriculum_cache(self, session_id: str):
        """Invalidate all curriculum cache for session"""
        pattern = f"curriculum:{session_id}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
```

This comprehensive Course and Curriculum Management API provides:

1. **Academic Structure Management**: Complete academic session and semester handling
2. **Course CRUD Operations**: Full course lifecycle management with validation
3. **Department Assignment**: Flexible course-department relationship management
4. **Curriculum Planning**: Academic curriculum planning and activation
5. **Student Registration**: Course registration with eligibility validation
6. **Performance Optimization**: Intelligent caching for frequently accessed data
7. **Audit Trail**: Complete logging of all course-related operations
8. **Search and Filtering**: Advanced search capabilities with multiple filters

The API maintains academic integrity while providing efficient operations for managing the complete course and curriculum structure of the university system.
