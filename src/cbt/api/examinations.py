"""
Examination management API endpoints.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response

from ..models.exam import Examination, ExamStatus, ExamInstance, ExamInstanceStatus
from ..schemas.exam import (
    ExaminationCreate, ExaminationUpdate, ExaminationResponse,
    ExamInstanceResponse, ExamSubmissionRequest, ExamSubmissionResponse,
    ExamStartRequest, ExamStartResponse, ExamReviewResponse,
    AnswerSaveRequest, ProctoringEventRequest
)
from ..services.exam_service import ExamService
from ..services.venue_allocation_service import VenueAllocationService
from ..services.slip_generation_service import SlipGenerationService
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


@router.post("/{exam_id}/allocate-venues", dependencies=[Depends(require_permission("exam.manage"))])
async def allocate_venues(
    exam_id: str,
    venue_ids: List[str],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Allocate students to specific venues for the examination."""
    try:
        allocation_service = VenueAllocationService(db)
        result = await allocation_service.allocate_venues(exam_id, venue_ids, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to allocate venues"
        )


@router.get("/{exam_id}/slips", dependencies=[Depends(require_permission("exam.read"))])
async def download_slips(
    exam_id: str,
    student_id: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Download examination slips as PDF. If student_id is provided, download only for that student."""
    try:
        slip_service = SlipGenerationService(db)
        student_ids = [student_id] if student_id else None
        pdf_bytes = await slip_service.generate_slips(exam_id, student_ids)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=exam_slips_{exam_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate slips"
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
        exam_service = ExamService(db)
        return await exam_service.sync_clock(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{exam_id}/instances/{instance_id}/proctoring/events", dependencies=[Depends(require_permission("exam.start"))])
async def log_proctoring_event(
    exam_id: str,
    instance_id: str,
    event: ProctoringEventRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Log proctoring event like focus loss."""
    try:
        exam_service = ExamService(db)
        return await exam_service.log_proctoring_event(instance_id, event)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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


# ── Phase 5: Results & Analytics ─────────────────────────────────────────────

@router.get("/my/results", dependencies=[Depends(require_permission("exam.read"))])
async def get_my_results(
    exam_id: Optional[str] = Query(None, description="Filter by exam"),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """Return embargo-aware results for the authenticated student."""
    exam_service = ExamService(db)
    return await exam_service.get_student_results(current_user.id, exam_id)


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

