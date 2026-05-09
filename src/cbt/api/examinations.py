"""
Examination management API endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models.exam import Examination, ExamStatus, ExamInstance, ExamInstanceStatus
from ..schemas.exam import (
    ExaminationCreate, ExaminationUpdate, ExaminationResponse,
    ExamInstanceResponse, ExamSubmissionRequest, ExamSubmissionResponse,
    ExamStartRequest, ExamStartResponse, ExamReviewResponse
)
from ..services.exam_service import ExamService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/examinations", tags=["examinations"])


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
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamStartResponse:
    """Start exam for student."""
    try:
        exam_service = ExamService(db)
        result = await exam_service.start_exam(exam_id, start_request.student_id, current_user.id)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start exam"
        )


@router.post("/{exam_id}/instances/{instance_id}/submit", response_model=ExamSubmissionResponse, dependencies=[Depends(require_permission("exam.submit"))])
async def submit_exam(
    exam_id: str,
    instance_id: str,
    submission: ExamSubmissionRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamSubmissionResponse:
    """Submit exam answers."""
    try:
        exam_service = ExamService(db)
        result = await exam_service.submit_exam(instance_id, submission, current_user.id)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message
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
