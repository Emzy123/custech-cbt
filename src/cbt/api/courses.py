"""
Course and curriculum management API endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models.academic import Course, Department, AcademicSession, Semester, SemesterType
from ..schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseSearch,
    AcademicSessionCreate, AcademicSessionUpdate, AcademicSessionResponse,
    SemesterCreate, SemesterResponse, CourseDepartmentAssignment,
    CurriculumPlan, StudentCourseRegistration
)
from ..services.course_service import CourseService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/courses", tags=["courses"])


# Academic Session Management
@router.post("/academic-sessions", response_model=AcademicSessionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("course.create"))])
async def create_academic_session(
    session_data: AcademicSessionCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> AcademicSessionResponse:
    """Create a new academic session."""
    try:
        course_service = CourseService(db)
        session = await course_service.create_academic_session(session_data, current_user.id)
        return AcademicSessionResponse.from_orm(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create academic session"
        )


@router.get("/academic-sessions", response_model=List[AcademicSessionResponse], dependencies=[Depends(require_permission("course.read"))])
async def list_academic_sessions(
    is_current: Optional[bool] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[AcademicSessionResponse]:
    """List all academic sessions."""
    try:
        course_service = CourseService(db)
        sessions = await course_service.list_academic_sessions(is_current)
        return [AcademicSessionResponse.from_orm(session) for session in sessions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list academic sessions"
        )


@router.get("/academic-sessions/{session_id}", response_model=AcademicSessionResponse, dependencies=[Depends(require_permission("course.read"))])
async def get_academic_session(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> AcademicSessionResponse:
    """Get academic session by ID."""
    try:
        course_service = CourseService(db)
        session = await course_service.get_academic_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found"
            )
        return AcademicSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get academic session"
        )


@router.put("/academic-sessions/{session_id}", response_model=AcademicSessionResponse, dependencies=[Depends(require_permission("course.update"))])
async def update_academic_session(
    session_id: str,
    session_data: AcademicSessionUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> AcademicSessionResponse:
    """Update academic session."""
    try:
        course_service = CourseService(db)
        session = await course_service.update_academic_session(session_id, session_data, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found"
            )
        return AcademicSessionResponse.from_orm(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update academic session"
        )


@router.post("/academic-sessions/{session_id}/set-current", dependencies=[Depends(require_permission("course.update"))])
async def set_current_session(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> AcademicSessionResponse:
    """Set academic session as current."""
    try:
        course_service = CourseService(db)
        session = await course_service.set_current_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found"
            )
        return AcademicSessionResponse.from_orm(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set current session"
        )


# Semester Management
@router.post("/academic-sessions/{session_id}/semesters", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("course.create"))])
async def create_semester(
    session_id: str,
    semester_data: SemesterCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> SemesterResponse:
    """Create a new semester."""
    try:
        course_service = CourseService(db)
        semester = await course_service.create_semester(session_id, semester_data, current_user.id)
        return SemesterResponse.from_orm(semester)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create semester"
        )


@router.get("/academic-sessions/{session_id}/semesters", response_model=List[SemesterResponse], dependencies=[Depends(require_permission("course.read"))])
async def list_semesters(
    session_id: str,
    is_current: Optional[bool] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[SemesterResponse]:
    """List semesters for academic session."""
    try:
        course_service = CourseService(db)
        semesters = await course_service.list_semesters(session_id, is_current)
        return [SemesterResponse.from_orm(semester) for semester in semesters]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list semesters"
        )


# Course Management
@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("course.create"))])
async def create_course(
    course_data: CourseCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> CourseResponse:
    """Create a new course."""
    try:
        course_service = CourseService(db)
        course = await course_service.create_course(course_data, current_user.id)
        return CourseResponse.from_orm(course)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )


@router.get("/", response_model=List[CourseResponse], dependencies=[Depends(require_permission("course.read"))])
async def list_courses(
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    semester_type: Optional[SemesterType] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[CourseResponse]:
    """List courses with filtering and pagination."""
    try:
        course_service = CourseService(db)
        search_params = CourseSearch(
            department_id=department_id,
            level=level,
            semester_type=semester_type,
            is_active=is_active,
            limit=limit,
            cursor=cursor
        )
        
        courses = await course_service.list_courses(search_params)
        return [CourseResponse.from_orm(course) for course in courses]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list courses"
        )


@router.get("/search", response_model=List[CourseResponse], dependencies=[Depends(require_permission("course.read"))])
async def search_courses(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[CourseResponse]:
    """Search courses by code or title."""
    try:
        course_service = CourseService(db)
        courses = await course_service.search_courses(query, limit)
        return [CourseResponse.from_orm(course) for course in courses]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search courses"
        )


@router.get("/{course_id}", response_model=CourseResponse, dependencies=[Depends(require_permission("course.read"))])
async def get_course(
    course_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> CourseResponse:
    """Get course by ID."""
    try:
        course_service = CourseService(db)
        course = await course_service.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return CourseResponse.from_orm(course)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course"
        )


@router.get("/code/{course_code}", response_model=CourseResponse, dependencies=[Depends(require_permission("course.read"))])
async def get_course_by_code(
    course_code: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> CourseResponse:
    """Get course by code."""
    try:
        course_service = CourseService(db)
        course = await course_service.get_course_by_code(course_code)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return CourseResponse.from_orm(course)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course"
        )


@router.put("/{course_id}", response_model=CourseResponse, dependencies=[Depends(require_permission("course.update"))])
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> CourseResponse:
    """Update course."""
    try:
        course_service = CourseService(db)
        course = await course_service.update_course(course_id, course_data, current_user.id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return CourseResponse.from_orm(course)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("course.delete"))])
async def delete_course(
    course_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete course (soft delete)."""
    try:
        course_service = CourseService(db)
        success = await course_service.delete_course(course_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )


# Department Assignment Management
@router.post("/{course_id}/departments", dependencies=[Depends(require_permission("course.update"))])
async def assign_course_to_department(
    course_id: str,
    assignment: CourseDepartmentAssignment,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Assign course to department."""
    try:
        course_service = CourseService(db)
        result = await course_service.assign_course_to_department(
            course_id, assignment.department_id, assignment.is_mandatory, current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign course to department"
        )


@router.get("/{course_id}/departments", dependencies=[Depends(require_permission("course.read"))])
async def get_course_departments(
    course_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get departments offering this course."""
    try:
        course_service = CourseService(db)
        departments = await course_service.get_course_departments(course_id)
        return departments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course departments"
        )


@router.get("/department/{department_id}/courses", dependencies=[Depends(require_permission("course.read"))])
async def get_department_courses(
    department_id: str,
    level: Optional[int] = Query(None),
    semester_type: Optional[SemesterType] = Query(None),
    is_mandatory: Optional[bool] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get courses offered by department."""
    try:
        course_service = CourseService(db)
        courses = await course_service.get_department_courses(
            department_id, level, semester_type, is_mandatory
        )
        return [CourseResponse.from_orm(course) for course in courses]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get department courses"
        )


# Curriculum Management
@router.post("/curriculum/plan", dependencies=[Depends(require_permission("course.create"))])
async def create_curriculum_plan(
    curriculum_plan: CurriculumPlan,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create curriculum plan for academic session."""
    try:
        course_service = CourseService(db)
        result = await course_service.create_curriculum_plan(curriculum_plan, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create curriculum plan"
        )


@router.get("/curriculum/{session_id}", dependencies=[Depends(require_permission("course.read"))])
async def get_curriculum_plan(
    session_id: str,
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get curriculum plan for academic session."""
    try:
        course_service = CourseService(db)
        curriculum = await course_service.get_curriculum_plan(
            session_id, department_id, level
        )
        return curriculum
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get curriculum plan"
        )


@router.post("/curriculum/{session_id}/activate", dependencies=[Depends(require_permission("course.update"))])
async def activate_curriculum_plan(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Activate curriculum plan for registration."""
    try:
        course_service = CourseService(db)
        result = await course_service.activate_curriculum_plan(session_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate curriculum plan"
        )
