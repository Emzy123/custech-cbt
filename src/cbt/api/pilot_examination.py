"""
Pilot examination API endpoints for testing and iterative refinement.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from ..schemas.pilot import (
    PilotExaminationCreate, PilotExaminationResponse, PilotEnrollmentRequest,
    PilotEnrollmentResponse, PilotEnvironmentResponse, PilotExecutionResponse,
    PilotFeedbackResponse, PilotAnalysisResponse, PilotImprovementRequest,
    PilotImprovementResponse, PilotReportResponse, PilotSummaryResponse
)
from ..services.pilot_examination_service import PilotExaminationService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/pilot-examination", tags=["pilot-examination"])


@router.post("/create", response_model=PilotExaminationResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def create_pilot_examination(
    pilot_data: PilotExaminationCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotExaminationResponse:
    """Create a new pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service.create_pilot_examination(pilot_data.model_dump())
        return PilotExaminationResponse(**pilot)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pilot examination"
        )


@router.post("/{pilot_id}/enroll-participants", response_model=PilotEnrollmentResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def enroll_pilot_participants(
    pilot_id: str,
    enrollment_data: PilotEnrollmentRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotEnrollmentResponse:
    """Enroll participants for pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        result = await pilot_service.enroll_pilot_participants(
            pilot_id, enrollment_data.participant_criteria
        )
        return PilotEnrollmentResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll participants"
        )


@router.post("/{pilot_id}/prepare-environment", response_model=PilotEnvironmentResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def prepare_pilot_environment(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotEnvironmentResponse:
    """Prepare pilot examination environment."""
    try:
        pilot_service = PilotExaminationService(db)
        result = await pilot_service.prepare_pilot_environment(pilot_id)
        return PilotEnvironmentResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare pilot environment"
        )


@router.post("/{pilot_id}/execute", response_model=PilotExecutionResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def execute_pilot_examination(
    pilot_id: str,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotExecutionResponse:
    """Execute pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        
        # Execute in background for long-running pilot
        background_tasks.add_task(pilot_service.execute_pilot_examination, pilot_id)
        
        return PilotExecutionResponse(
            pilot_id=pilot_id,
            status="started",
            message="Pilot examination execution started in background"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute pilot examination"
        )


@router.post("/{pilot_id}/collect-feedback", response_model=PilotFeedbackResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def collect_pilot_feedback(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotFeedbackResponse:
    """Collect feedback from pilot participants."""
    try:
        pilot_service = PilotExaminationService(db)
        result = await pilot_service.collect_pilot_feedback(pilot_id)
        return PilotFeedbackResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect pilot feedback"
        )


@router.post("/{pilot_id}/analyze", response_model=PilotAnalysisResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def analyze_pilot_results(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotAnalysisResponse:
    """Analyze pilot examination results."""
    try:
        pilot_service = PilotExaminationService(db)
        result = await pilot_service.analyze_pilot_results(pilot_id)
        return PilotAnalysisResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze pilot results"
        )


@router.post("/{pilot_id}/implement-improvements", response_model=PilotImprovementResponse, dependencies=[Depends(require_permission("pilot.manage"))])
async def implement_improvements(
    pilot_id: str,
    improvement_data: PilotImprovementRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotImprovementResponse:
    """Implement improvements based on pilot analysis."""
    try:
        pilot_service = PilotExaminationService(db)
        
        # Implement in background for long-running improvements
        background_tasks.add_task(
            pilot_service.implement_improvements,
            pilot_id,
            improvement_data.improvement_plan
        )
        
        return PilotImprovementResponse(
            pilot_id=pilot_id,
            status="started",
            message="Improvement implementation started in background"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to implement improvements"
        )


@router.get("/{pilot_id}/report", response_model=PilotReportResponse, dependencies=[Depends(require_permission("pilot.read"))])
async def generate_pilot_report(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotReportResponse:
    """Generate comprehensive pilot examination report."""
    try:
        pilot_service = PilotExaminationService(db)
        report = await pilot_service.generate_pilot_report(pilot_id)
        return PilotReportResponse(**report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate pilot report"
        )


@router.get("/{pilot_id}/summary", response_model=PilotSummaryResponse, dependencies=[Depends(require_permission("pilot.read"))])
async def get_pilot_summary(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PilotSummaryResponse:
    """Get pilot examination summary."""
    try:
        pilot_service = PilotExaminationService(db)
        summary = await pilot_service.get_pilot_summary(pilot_id)
        return PilotSummaryResponse(**summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pilot summary"
        )


@router.get("/{pilot_id}", dependencies=[Depends(require_permission("pilot.read"))])
async def get_pilot_examination(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed pilot examination information."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        return pilot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pilot examination"
        )


@router.get("/", dependencies=[Depends(require_permission("pilot.read"))])
async def list_pilot_examinations(
    status: Optional[str] = None,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all pilot examinations."""
    try:
        # This would typically query a database
        # For now, return empty list
        return {
            "pilots": [],
            "total_count": 0,
            "filters": {
                "status": status,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pilot examinations"
        )


@router.get("/{pilot_id}/events", dependencies=[Depends(require_permission("pilot.read"))])
async def get_pilot_events(
    pilot_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get pilot examination events."""
    try:
        pilot_service = PilotExaminationService(db)
        
        # Get events from cache
        events_cache_key = f"pilot_events:{pilot_id}"
        events = await pilot_service.cache.get(events_cache_key) or []
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        
        # Apply limit
        if len(events) > limit:
            events = events[-limit:]
        
        return {
            "pilot_id": pilot_id,
            "events": events,
            "total_events": len(events),
            "filters": {
                "event_type": event_type,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pilot events"
        )


@router.post("/{pilot_id}/cancel", dependencies=[Depends(require_permission("pilot.manage"))])
async def cancel_pilot_examination(
    pilot_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Cancel pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        
        # Update pilot status
        pilot["status"] = "cancelled"
        pilot["cancelled_at"] = datetime.utcnow()
        pilot["cancellation_reason"] = reason
        pilot["cancelled_by"] = current_user.id
        await pilot_service._update_pilot_examination(pilot_id, pilot)
        
        # Log cancellation
        await pilot_service._log_pilot_event(
            pilot_id, "PILOT_CANCELLED",
            {"reason": reason, "cancelled_by": current_user.id}
        )
        
        return {
            "pilot_id": pilot_id,
            "status": "cancelled",
            "cancelled_at": pilot["cancelled_at"],
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel pilot examination"
        )


@router.post("/{pilot_id}/pause", dependencies=[Depends(require_permission("pilot.manage"))])
async def pause_pilot_examination(
    pilot_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pause pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        
        if pilot["status"] != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only in-progress pilot examinations can be paused"
            )
        
        # Update pilot status
        pilot["status"] = "paused"
        pilot["paused_at"] = datetime.utcnow()
        pilot["pause_reason"] = reason
        pilot["paused_by"] = current_user.id
        await pilot_service._update_pilot_examination(pilot_id, pilot)
        
        # Log pause
        await pilot_service._log_pilot_event(
            pilot_id, "PILOT_PAUSED",
            {"reason": reason, "paused_by": current_user.id}
        )
        
        return {
            "pilot_id": pilot_id,
            "status": "paused",
            "paused_at": pilot["paused_at"],
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause pilot examination"
        )


@router.post("/{pilot_id}/resume", dependencies=[Depends(require_permission("pilot.manage"))])
async def resume_pilot_examination(
    pilot_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Resume paused pilot examination."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        
        if pilot["status"] != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only paused pilot examinations can be resumed"
            )
        
        # Update pilot status
        pilot["status"] = "in_progress"
        pilot["resumed_at"] = datetime.utcnow()
        pilot["resumed_by"] = current_user.id
        await pilot_service._update_pilot_examination(pilot_id, pilot)
        
        # Log resume
        await pilot_service._log_pilot_event(
            pilot_id, "PILOT_RESUMED",
            {"resumed_by": current_user.id}
        )
        
        return {
            "pilot_id": pilot_id,
            "status": "in_progress",
            "resumed_at": pilot["resumed_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume pilot examination"
        )


@router.get("/{pilot_id}/participants", dependencies=[Depends(require_permission("pilot.read"))])
async def get_pilot_participants(
    pilot_id: str,
    status: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get pilot examination participants."""
    try:
        pilot_service = PilotExaminationService(db)
        
        # Get enrollments
        enrollment_cache_key = f"pilot_enrollments:{pilot_id}"
        enrollments = await pilot_service.cache.get(enrollment_cache_key) or []
        
        # Filter by status if specified
        if status:
            enrollments = [e for e in enrollments if e.get("status") == status]
        
        return {
            "pilot_id": pilot_id,
            "participants": enrollments,
            "total_participants": len(enrollments),
            "filters": {
                "status": status
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pilot participants"
        )


@router.post("/{pilot_id}/participants/{enrollment_id}/communicate", dependencies=[Depends(require_permission("pilot.manage"))])
async def communicate_with_participant(
    pilot_id: str,
    enrollment_id: str,
    message: str,
    communication_type: str = "email",
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Send communication to pilot participant."""
    try:
        pilot_service = PilotExaminationService(db)
        
        # Get enrollment
        enrollment_cache_key = f"pilot_enrollments:{pilot_id}"
        enrollments = await pilot_service.cache.get(enrollment_cache_key) or []
        enrollment = next((e for e in enrollments if e["enrollment_id"] == enrollment_id), None)
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found"
            )
        
        # Log communication
        await pilot_service._log_pilot_event(
            pilot_id, "PARTICIPANT_COMMUNICATION",
            {
                "enrollment_id": enrollment_id,
                "communication_type": communication_type,
                "message": message,
                "sent_by": current_user.id
            }
        )
        
        return {
            "pilot_id": pilot_id,
            "enrollment_id": enrollment_id,
            "communication_type": communication_type,
            "sent_at": datetime.utcnow(),
            "message": "Communication sent successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send communication"
        )


@router.get("/{pilot_id}/metrics", dependencies=[Depends(require_permission("pilot.read"))])
async def get_pilot_metrics(
    pilot_id: str,
    metric_type: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get pilot examination metrics."""
    try:
        pilot_service = PilotExaminationService(db)
        pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        
        metrics = {}
        
        # Get execution results if available
        execution_results = pilot.get("execution_results", {})
        if execution_results:
            if not metric_type or metric_type == "engagement":
                metrics["engagement"] = execution_results.get("participant_engagement", {})
            if not metric_type or metric_type == "performance":
                metrics["performance"] = execution_results.get("system_performance", {})
            if not metric_type or metric_type == "incidents":
                metrics["incidents"] = execution_results.get("incident_tracking", {})
            if not metric_type or metric_type == "real_time":
                metrics["real_time"] = execution_results.get("real_time_metrics", {})
        
        # Get feedback results if available
        feedback_results = pilot.get("feedback_results", {})
        if feedback_results and (not metric_type or metric_type == "feedback"):
            metrics["feedback"] = feedback_results
        
        # Get analysis results if available
        analysis_results = pilot.get("analysis_results", {})
        if analysis_results and (not metric_type or metric_type == "analysis"):
            metrics["analysis"] = analysis_results
        
        return {
            "pilot_id": pilot_id,
            "metrics": metrics,
            "metric_type": metric_type,
            "generated_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pilot metrics"
        )


@router.post("/{pilot_id}/duplicate", dependencies=[Depends(require_permission("pilot.manage"))])
async def duplicate_pilot_examination(
    pilot_id: str,
    new_title: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Duplicate pilot examination configuration."""
    try:
        pilot_service = PilotExaminationService(db)
        original_pilot = await pilot_service._get_pilot_examination(pilot_id)
        if not original_pilot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pilot examination not found"
            )
        
        # Create duplicate configuration
        duplicate_config = original_pilot["configuration"].copy()
        duplicate_config["title"] = new_title
        duplicate_config["based_on"] = pilot_id
        duplicate_config["duplicated_by"] = current_user.id
        duplicate_config["duplicated_at"] = datetime.utcnow().isoformat()
        
        # Create new pilot
        new_pilot = await pilot_service.create_pilot_examination(duplicate_config)
        
        # Log duplication
        await pilot_service._log_pilot_event(
            pilot_id, "PILOT_DUPLICATED",
            {
                "new_pilot_id": new_pilot["pilot_id"],
                "new_title": new_title,
                "duplicated_by": current_user.id
            }
        )
        
        return {
            "original_pilot_id": pilot_id,
            "new_pilot_id": new_pilot["pilot_id"],
            "new_title": new_title,
            "duplicated_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate pilot examination"
        )
