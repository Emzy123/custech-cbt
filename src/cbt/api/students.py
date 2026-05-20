"""
Student management API endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File

from ..models.student import Student, StudentStatus
from ..schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse, StudentSearch,
    BulkImportRequest, BulkImportResponse, StudentCourseRegistration,
    StudentStatusUpdate
)
from ..services.student_service import StudentService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("student.create"))])
async def create_student(
    student_data: StudentCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Create a new student record."""
    try:
        student_service = StudentService(db)
        student = await student_service.create_student(student_data, current_user.id)
        return StudentResponse.from_orm(student)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student record"
        )


@router.get("/", response_model=List[StudentResponse], dependencies=[Depends(require_permission("student.read"))])
async def list_students(
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    student_status: Optional[StudentStatus] = Query(None, alias="status"),
    academic_session: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[StudentResponse]:
    """List students with filtering and pagination."""
    try:
        student_service = StudentService(db)
        search_params = StudentSearch(
            department_id=department_id,
            level=level,
            status=student_status,
            academic_session=academic_session,
            limit=limit,
            cursor=cursor
        )
        
        students = await student_service.list_students(search_params)
        return [StudentResponse.from_orm(student) for student in students]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list students"
        )


@router.get("/search", response_model=List[StudentResponse], dependencies=[Depends(require_permission("student.read"))])
async def search_students(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[StudentResponse]:
    """Search students by name or matric number."""
    try:
        student_service = StudentService(db)
        students = await student_service.search_students(query, limit)
        return [StudentResponse.from_orm(student) for student in students]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search students"
        )


@router.get("/{student_id}", response_model=StudentResponse, dependencies=[Depends(require_permission("student.read"))])
async def get_student(
    student_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Get student by ID."""
    try:
        student_service = StudentService(db)
        student = await student_service.get_student(student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student"
        )


@router.get("/matric/{matric_number}", response_model=StudentResponse, dependencies=[Depends(require_permission("student.read"))])
async def get_student_by_matric(
    matric_number: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Get student by matric number."""
    try:
        student_service = StudentService(db)
        student = await student_service.get_student_by_matric(matric_number)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student"
        )


@router.put("/{student_id}", response_model=StudentResponse, dependencies=[Depends(require_permission("student.update"))])
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Update student record."""
    try:
        student_service = StudentService(db)
        student = await student_service.update_student(student_id, student_data, current_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
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
            detail="Failed to update student"
        )


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("student.delete"))])
async def delete_student(
    student_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete student record (soft delete)."""
    try:
        student_service = StudentService(db)
        success = await student_service.delete_student(student_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete student"
        )


@router.post("/import", response_model=BulkImportResponse, dependencies=[Depends(require_permission("student.import"))])
async def bulk_import_students(
    import_request: BulkImportRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BulkImportResponse:
    """Bulk import students from data."""
    try:
        student_service = StudentService(db)
        result = await student_service.bulk_import_students(import_request, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )


@router.post("/import/csv", dependencies=[Depends(require_permission("student.import"))])
async def import_students_from_csv(
    file: UploadFile = File(...),
    validate_only: bool = Query(False),
    continue_on_error: bool = Query(False),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BulkImportResponse:
    """Import students from CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        student_service = StudentService(db)
        result = await student_service.import_from_csv(
            file, validate_only, continue_on_error, current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV import failed: {str(e)}"
        )


@router.get("/import/{import_id}/status", dependencies=[Depends(require_permission("student.read"))])
async def get_import_status(
    import_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get bulk import status."""
    try:
        student_service = StudentService(db)
        status = await student_service.get_import_status(import_id)
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get import status"
        )


@router.put("/{student_id}/status", dependencies=[Depends(require_permission("student.update"))])
async def update_student_status(
    student_id: str,
    status_update: StudentStatusUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Update student status."""
    try:
        student_service = StudentService(db)
        student = await student_service.update_student_status(
            student_id, status_update, current_user.id
        )
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
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
            detail="Failed to update student status"
        )


@router.post("/{student_id}/activate", dependencies=[Depends(require_permission("student.update"))])
async def activate_student(
    student_id: str,
    reason: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Activate student account."""
    try:
        student_service = StudentService(db)
        student = await student_service.activate_student(student_id, reason, current_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student activation failed: {str(e)}"
        )


@router.post("/{student_id}/deactivate", dependencies=[Depends(require_permission("student.update"))])
async def deactivate_student(
    student_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Deactivate student account."""
    try:
        student_service = StudentService(db)
        student = await student_service.deactivate_student(student_id, reason, current_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student deactivation failed: {str(e)}"
        )


@router.post("/{student_id}/graduate", dependencies=[Depends(require_permission("student.update"))])
async def graduate_student(
    student_id: str,
    graduation_year: int,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StudentResponse:
    """Mark student as graduated."""
    try:
        student_service = StudentService(db)
        student = await student_service.graduate_student(student_id, graduation_year, current_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentResponse.from_orm(student)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student graduation failed: {str(e)}"
        )


@router.get("/{student_id}/courses", dependencies=[Depends(require_permission("student.read"))])
async def get_student_courses(
    student_id: str,
    academic_session: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get student's course registrations."""
    try:
        student_service = StudentService(db)
        courses = await student_service.get_student_courses(
            student_id, academic_session, semester
        )
        return courses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student courses"
        )


@router.post("/{student_id}/courses", dependencies=[Depends(require_permission("student.update"))])
async def register_student_for_course(
    student_id: str,
    registration: StudentCourseRegistration,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Register student for course."""
    try:
        student_service = StudentService(db)
        result = await student_service.register_for_course(registration, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register student for course"
        )


@router.delete("/{student_id}/courses/{course_id}", dependencies=[Depends(require_permission("student.update"))])
async def withdraw_student_from_course(
    student_id: str,
    course_id: str,
    academic_session: str,
    semester: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Withdraw student from course."""
    try:
        student_service = StudentService(db)
        result = await student_service.withdraw_from_course(
            student_id, course_id, academic_session, semester, current_user.id
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
            detail="Failed to withdraw student from course"
        )
