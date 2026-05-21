"""
Examination management API endpoints.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request, Body
from pydantic import BaseModel

from ..models.exam import Examination, ExamStatus, ExamInstance, ExamInstanceStatus
from ..models.student import Student, StudentCourse
from ..models.academic import Department
from ..core.security import security
from ..core.redis import cache_manager
from ..services.authorization_service import AuthorizationService
from ..schemas.exam import (
    ExaminationCreate, ExaminationUpdate, ExaminationResponse,
    ExamInstanceResponse, ExamSubmissionRequest, ExamSubmissionResponse,
    ExamStartRequest, ExamStartResponse, ExamReviewResponse,
    AnswerSaveRequest, ExamRegisteredStudentResponse
)
from ..services.exam_service import ExamService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/examinations", tags=["examinations"])





async def _ensure_instance_access(instance_id: str, current_user) -> ExamInstance:
    """Ensure the caller owns the instance or has staff proctoring permissions."""
    instance = await ExamInstance.get(instance_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam instance not found")

    authz = AuthorizationService(cache_manager)
    permissions = await authz.get_user_permissions(str(current_user.id))
    staff_permissions = {"exam.manage", "exam.invigilate", "system.admin", "*"}
    if permissions.intersection(staff_permissions):
        return instance

    student = await Student.find_one(Student.user_id == str(current_user.id))
    if student and str(instance.student_id) == str(student.id):
        return instance

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized for this exam instance",
    )


@router.post("/", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.create"))])
async def create_examination(
    exam_data: ExaminationCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Create a new examination."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.create_examination(exam_data, current_user.id)
        return ExaminationResponse.from_orm(examination)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create examination"
        )


@router.get("/", response_model=List[ExaminationResponse], dependencies=[Depends(require_permission("exam.read"))])
async def list_examinations(
    course_id: Optional[str] = Query(None),
    academic_session_id: Optional[str] = Query(None),
    status: Optional[ExamStatus] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[ExaminationResponse]:
    """List examinations with filtering and pagination."""
    try:
        exam_service = ExamService(db)
        examinations = await exam_service.list_examinations(
            course_id, academic_session_id, status, limit, cursor
        )
        return [ExaminationResponse.from_orm(exam) for exam in examinations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list examinations"
        )


@router.get("/{exam_id}", response_model=ExaminationResponse, dependencies=[Depends(require_permission("exam.read"))])
async def get_examination(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Get examination by ID."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.get_examination(exam_id)
        if not examination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        return ExaminationResponse.from_orm(examination)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get examination"
        )


@router.put("/{exam_id}", response_model=ExaminationResponse, dependencies=[Depends(require_permission("exam.update"))])
async def update_examination(
    exam_id: str,
    exam_data: ExaminationUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Update examination."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.update_examination(exam_id, exam_data, current_user.id)
        if not examination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        return ExaminationResponse.from_orm(examination)
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
            detail="Failed to update examination"
        )


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("exam.delete"))])
async def delete_examination(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete examination (soft delete)."""
    try:
        exam_service = ExamService(db)
        success = await exam_service.delete_examination(exam_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete examination"
        )


@router.post("/{exam_id}/schedule", dependencies=[Depends(require_permission("exam.schedule"))])
async def schedule_examination(
    exam_id: str,
    schedule_data: dict,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Schedule examination for specific date and time."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.schedule_examination(exam_id, schedule_data, current_user.id)
        if not examination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        return ExaminationResponse.from_orm(examination)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule examination"
        )


@router.post("/{exam_id}/publish", dependencies=[Depends(require_permission("exam.publish"))])
async def publish_examination(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Publish examination for students."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.publish_examination(exam_id, current_user.id)
        if not examination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        return ExaminationResponse.from_orm(examination)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish examination"
        )


@router.post("/{exam_id}/cancel", dependencies=[Depends(require_permission("exam.cancel"))])
async def cancel_examination(
    exam_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExaminationResponse:
    """Cancel examination."""
    try:
        exam_service = ExamService(db)
        examination = await exam_service.cancel_examination(exam_id, reason, current_user.id)
        if not examination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        return ExaminationResponse.from_orm(examination)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel examination"
        )





# Exam Instance Management
@router.get("/{exam_id}/instances", response_model=List[ExamInstanceResponse], dependencies=[Depends(require_permission("exam.read"))])
async def list_exam_instances(
    exam_id: str,
    status: Optional[ExamInstanceStatus] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[ExamInstanceResponse]:
    """List exam instances for an examination."""
    try:
        exam_service = ExamService(db)
        instances = await exam_service.list_exam_instances(exam_id, status, limit, cursor)
        return [ExamInstanceResponse.from_orm(instance) for instance in instances]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list exam instances"
        )


@router.get("/{exam_id}/instances/{instance_id}", response_model=ExamInstanceResponse, dependencies=[Depends(require_permission("exam.read"))])
async def get_exam_instance(
    exam_id: str,
    instance_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamInstanceResponse:
    """Get exam instance by ID."""
    try:
        exam_service = ExamService(db)
        instance = await exam_service.get_exam_instance(instance_id)
        if not instance or instance.examination_id != exam_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam instance not found"
            )
        return ExamInstanceResponse.from_orm(instance)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exam instance"
        )


@router.post("/{exam_id}/start", response_model=ExamStartResponse, dependencies=[Depends(require_permission("exam.start"))])
async def start_exam(
    exam_id: str,
    start_request: ExamStartRequest,
    request: Request,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamStartResponse:
    """Start exam for student."""
    try:
        student = await Student.find_one(Student.user_id == str(current_user.id))
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student profile not found for this account",
            )

        student_id = start_request.student_id or str(student.id)
        if str(student_id) != str(student.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot start an exam for another student",
            )

        if not start_request.rules_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam rules must be accepted before starting",
            )

        exam_service = ExamService(db)
        result = await exam_service.start_exam(exam_id, student_id, current_user.id)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start exam"
        )


@router.get("/{exam_id}/instances/{instance_id}/paper", dependencies=[Depends(require_permission("exam.start"))])
async def get_exam_paper(
    exam_id: str,
    instance_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get randomized exam paper."""
    try:
        await _ensure_instance_access(instance_id, current_user)
        exam_service = ExamService(db)
        return await exam_service.get_paper(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{exam_id}/instances/{instance_id}/answers", dependencies=[Depends(require_permission("exam.submit"))])
async def save_answer(
    exam_id: str,
    instance_id: str,
    answer: AnswerSaveRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Autosave answer."""
    try:
        await _ensure_instance_access(instance_id, current_user)
        exam_service = ExamService(db)
        return await exam_service.save_answer(instance_id, answer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{exam_id}/instances/{instance_id}/clock", dependencies=[Depends(require_permission("exam.start"))])
async def sync_clock(
    exam_id: str,
    instance_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Sync exam clock."""
    try:
        await _ensure_instance_access(instance_id, current_user)
        exam_service = ExamService(db)
        return await exam_service.sync_clock(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )





@router.post("/{exam_id}/instances/{instance_id}/submit", response_model=ExamSubmissionResponse, dependencies=[Depends(require_permission("exam.submit"))])
async def submit_exam(
    exam_id: str,
    instance_id: str,
    submission: Optional[ExamSubmissionRequest] = Body(default=None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamSubmissionResponse:
    """Submit exam answers."""
    try:
        await _ensure_instance_access(instance_id, current_user)
        if submission is None:
            submission = ExamSubmissionRequest()
        exam_service = ExamService(db)
        result = await exam_service.submit_exam(instance_id, submission, current_user.id)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit exam"
        )


@router.get("/{exam_id}/instances/{instance_id}/review", response_model=ExamReviewResponse, dependencies=[Depends(require_permission("exam.review"))])
async def review_exam(
    exam_id: str,
    instance_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamReviewResponse:
    """Review submitted exam."""
    try:
        exam_service = ExamService(db)
        review = await exam_service.review_exam(instance_id, current_user.id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam instance not found or not submitted"
            )
        return review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review exam"
        )


@router.post("/{exam_id}/instances/{instance_id}/timeout", dependencies=[Depends(require_permission("exam.manage"))])
async def timeout_exam(
    exam_id: str,
    instance_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamInstanceResponse:
    """Mark exam instance as timed out."""
    try:
        exam_service = ExamService(db)
        instance = await exam_service.timeout_exam(instance_id, current_user.id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam instance not found"
            )
        return ExamInstanceResponse.from_orm(instance)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to timeout exam"
        )


@router.post("/{exam_id}/instances/{instance_id}/extend-time", dependencies=[Depends(require_permission("exam.manage"))])
async def extend_exam_time(
    exam_id: str,
    instance_id: str,
    extension_minutes: int,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamInstanceResponse:
    """Extend exam time for student."""
    try:
        exam_service = ExamService(db)
        instance = await exam_service.extend_exam_time(instance_id, extension_minutes, reason, current_user.id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam instance not found"
            )
        return ExamInstanceResponse.from_orm(instance)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extend exam time"
        )


# Exam Statistics and Reporting
@router.get("/{exam_id}/statistics", dependencies=[Depends(require_permission("exam.read"))])
async def get_exam_statistics(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get examination statistics."""
    try:
        exam_service = ExamService(db)
        stats = await exam_service.get_exam_statistics(exam_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exam statistics"
        )


@router.get("/{exam_id}/registered-students", response_model=List[ExamRegisteredStudentResponse], dependencies=[Depends(require_permission("exam.read"))])
async def get_exam_registered_students(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[ExamRegisteredStudentResponse]:
    """Get the list of registered students for an examination."""
    try:
        # 1. Fetch examination
        exam = await Examination.get(exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination not found"
            )
        
        # 2. Fetch registered student courses
        student_courses = await StudentCourse.find(
            StudentCourse.course_id == exam.course_id,
            StudentCourse.academic_session_id == exam.academic_session_id,
            StudentCourse.status == "REGISTERED"
        ).to_list()
        
        if not student_courses:
            return []
            
        # 3. Fetch student details and resolve departments
        student_ids = [sc.student_id for sc in student_courses]
        students = await Student.find({"_id": {"$in": student_ids}}).to_list()
        
        # 4. Resolve unique department IDs to get department code and name
        dept_ids = list({s.department_id for s in students if s.department_id})
        departments = await Department.find({"_id": {"$in": dept_ids}}).to_list()
        dept_map = {str(d.id): d for d in departments}
        
        # 5. Build response list
        response_students = []
        for s in students:
            dept = dept_map.get(str(s.department_id))
            response_students.append(
                ExamRegisteredStudentResponse(
                    id=str(s.id),
                    first_name=s.first_name,
                    last_name=s.last_name,
                    email=s.email,
                    matric_number=s.matric_number,
                    department_id=s.department_id,
                    department_code=dept.code if dept else None,
                    department_name=dept.name if dept else None,
                    is_active=s.is_active
                )
            )
        return response_students
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get registered students: {str(e)}"
        )


# ── Phase 5: Results & Analytics ─────────────────────────────────────────────

@router.get("/my/results", dependencies=[Depends(require_permission("exam.read"))])
async def get_my_results(
    exam_id: Optional[str] = Query(None, description="Filter by exam"),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """Return embargo-aware results for the authenticated student."""
    student = await Student.find_one(Student.user_id == str(current_user.id))
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile not found for this account",
        )
    exam_service = ExamService(db)
    return await exam_service.get_student_results(str(student.id), exam_id)


@router.get("/{exam_id}/results", dependencies=[Depends(require_permission("grade.read"))])
async def get_exam_results(
    exam_id: str,
    format: str = Query("summary"),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get examination results."""
    try:
        exam_service = ExamService(db)
        results = await exam_service.get_exam_results(exam_id, format)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exam results"
        )


@router.post("/{exam_id}/grade", dependencies=[Depends(require_permission("grade.update"))])
async def grade_exam(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Grade all submitted exam instances."""
    try:
        exam_service = ExamService(db)
        result = await exam_service.grade_exam(exam_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grade exam"
        )


@router.post("/{exam_id}/publish-results", dependencies=[Depends(require_permission("result.publish"))])
async def publish_results(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Publish examination results."""
    try:
        exam_service = ExamService(db)
        result = await exam_service.publish_results(exam_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish results"
        )




@router.get("/{exam_id}/analytics/items", dependencies=[Depends(require_permission("exam.manage"))])
async def get_item_analysis(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Return per-question P-value, discrimination, and distractor breakdown (lecturer/officer)."""
    exam_service = ExamService(db)
    return await exam_service.get_item_analysis(exam_id)


@router.get("/{exam_id}/results/export", dependencies=[Depends(require_permission("exam.manage"))])
async def export_results_csv(
    exam_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Response:
    """Stream a CSV of all submitted results for Senate / academic records."""
    exam_service = ExamService(db)
    csv_content = await exam_service.export_results_csv(exam_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=results_{exam_id}.csv"},
    )

