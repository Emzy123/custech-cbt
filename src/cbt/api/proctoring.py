"""
Proctoring API endpoints for browser lockdown and monitoring.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.proctoring import (
    ProctoringSessionStart, ProctoringSessionResponse, FocusLossEvent,
    FullscreenExitEvent, KeyboardViolationEvent, ClipboardEvent,
    HeartbeatUpdate, ProctoringSummary, ScreenRecordingDetection
)
from ..services.proctoring_service import ProctoringService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/proctoring", tags=["proctoring"])


@router.post("/session/start", response_model=ProctoringSessionResponse, dependencies=[Depends(require_permission("exam.start"))])
async def start_proctoring_session(
    session_data: ProctoringSessionStart,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ProctoringSessionResponse:
    """Start proctoring session for exam."""
    try:
        proctoring_service = ProctoringService(db)
        session = await proctoring_service.start_proctoring_session(
            session_data.examination_id,
            session_data.student_id,
            session_data.device_fingerprint,
            session_data.ip_address
        )
        return ProctoringSessionResponse(**session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start proctoring session"
        )


@router.post("/session/{session_id}/focus-loss", dependencies=[Depends(require_permission("exam.active"))])
async def record_focus_loss(
    session_id: str,
    focus_data: FocusLossEvent,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record focus loss event."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.record_focus_loss(
            session_id, focus_data.duration, focus_data.reason
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
            detail="Failed to record focus loss"
        )


@router.post("/session/{session_id}/fullscreen-exit", dependencies=[Depends(require_permission("exam.active"))])
async def record_fullscreen_exit(
    session_id: str,
    fullscreen_data: FullscreenExitEvent,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record fullscreen exit event."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.record_fullscreen_exit(
            session_id, fullscreen_data.reason
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
            detail="Failed to record fullscreen exit"
        )


@router.post("/session/{session_id}/keyboard-violation", dependencies=[Depends(require_permission("exam.active"))])
async def record_keyboard_violation(
    session_id: str,
    keyboard_data: KeyboardViolationEvent,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record keyboard violation."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.record_keyboard_violation(
            session_id, keyboard_data.key_combination, keyboard_data.action
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
            detail="Failed to record keyboard violation"
        )


@router.post("/session/{session_id}/clipboard-event", dependencies=[Depends(require_permission("exam.active"))])
async def record_clipboard_event(
    session_id: str,
    clipboard_data: ClipboardEvent,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record clipboard event."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.record_clipboard_event(
            session_id, clipboard_data.event_type, clipboard_data.data_length
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
            detail="Failed to record clipboard event"
        )


@router.post("/session/{session_id}/heartbeat", dependencies=[Depends(require_permission("exam.active"))])
async def update_heartbeat(
    session_id: str,
    heartbeat_data: HeartbeatUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update session heartbeat."""
    try:
        proctoring_service = ProctoringService(db)
        success = await proctoring_service.update_heartbeat(session_id, heartbeat_data.status_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proctoring session not found"
            )
        return {"success": True, "message": "Heartbeat updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update heartbeat"
        )


@router.get("/session/{session_id}", dependencies=[Depends(require_permission("exam.read"))])
async def get_proctoring_session(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get proctoring session details."""
    try:
        proctoring_service = ProctoringService(db)
        session = await proctoring_service._get_proctoring_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proctoring session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proctoring session"
        )


@router.post("/session/{session_id}/end", dependencies=[Depends(require_permission("exam.manage"))])
async def end_proctoring_session(
    session_id: str,
    reason: Optional[str] = "exam_completed",
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """End proctoring session."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.end_proctoring_session(session_id, reason)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end proctoring session"
        )


@router.get("/examination/{examination_id}/summary", response_model=ProctoringSummary, dependencies=[Depends(require_permission("exam.manage"))])
async def get_proctoring_summary(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ProctoringSummary:
    """Get proctoring summary for examination."""
    try:
        proctoring_service = ProctoringService(db)
        summary = await proctoring_service.get_proctoring_summary(examination_id)
        return ProctoringSummary(**summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proctoring summary"
        )


@router.post("/session/{session_id}/watermark", dependencies=[Depends(require_permission("exam.active"))])
async def generate_session_watermark(
    session_id: str,
    student_info: dict,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Generate session watermark."""
    try:
        proctoring_service = ProctoringService(db)
        watermark = await proctoring_service.generate_session_watermark(session_id, student_info)
        return watermark
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate watermark"
        )


@router.post("/session/{session_id}/detect-recording", dependencies=[Depends(require_permission("exam.active"))])
async def detect_screen_recording(
    session_id: str,
    browser_info: dict,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ScreenRecordingDetection:
    """Detect screen recording software."""
    try:
        proctoring_service = ProctoringService(db)
        detection = await proctoring_service.detect_screen_recording(session_id, browser_info)
        return ScreenRecordingDetection(**detection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect screen recording"
        )


@router.get("/session/{session_id}/events", dependencies=[Depends(require_permission("exam.manage"))])
async def get_session_events(
    session_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get security events for session."""
    try:
        proctoring_service = ProctoringService(db)
        session = await proctoring_service._get_proctoring_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proctoring session not found"
            )
        
        events = session.get("security_events", [])
        
        # Filter by event type if specified
        if event_type:
            events = [event for event in events if event.get("event_type") == event_type]
        
        # Limit results
        events = events[-limit:] if len(events) > limit else events
        
        return {
            "session_id": session_id,
            "events": events,
            "total_events": len(session.get("security_events", [])),
            "filtered_events": len(events)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session events"
        )


@router.post("/session/{session_id}/pause", dependencies=[Depends(require_permission("exam.manage"))])
async def pause_exam_session(
    session_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pause exam session (invigilator action)."""
    try:
        proctoring_service = ProctoringService(db)
        session = await proctoring_service._get_proctoring_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proctoring session not found"
            )
        
        # Update session status to paused
        session["status"] = "paused"
        session["paused_at"] = datetime.utcnow()
        session["paused_by"] = current_user.id
        session["pause_reason"] = reason
        
        await proctoring_service._update_proctoring_session(session_id, session)
        
        return {
            "success": True,
            "message": "Exam session paused",
            "paused_at": session["paused_at"],
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause exam session"
        )


@router.post("/session/{session_id}/resume", dependencies=[Depends(require_permission("exam.manage"))])
async def resume_exam_session(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Resume paused exam session (invigilator action)."""
    try:
        proctoring_service = ProctoringService(db)
        session = await proctoring_service._get_proctoring_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proctoring session not found"
            )
        
        if session.get("status") != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused"
            )
        
        # Update session status to active
        session["status"] = "active"
        session["resumed_at"] = datetime.utcnow()
        session["resumed_by"] = current_user.id
        
        await proctoring_service._update_proctoring_session(session_id, session)
        
        return {
            "success": True,
            "message": "Exam session resumed",
            "resumed_at": session["resumed_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume exam session"
        )


@router.post("/session/{session_id}/terminate", dependencies=[Depends(require_permission("exam.manage"))])
async def terminate_exam_session(
    session_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Terminate exam session (invigilator action)."""
    try:
        proctoring_service = ProctoringService(db)
        result = await proctoring_service.end_proctoring_session(session_id, f"terminated: {reason}")
        
        # Log termination
        await proctoring_service._log_security_event(
            student_id=result.get("student_id", "unknown"),
            event_type="EXAM_TERMINATED",
            details={
                "reason": reason,
                "terminated_by": current_user.id,
                "session_id": session_id
            }
        )
        
        return {
            "success": True,
            "message": "Exam session terminated",
            "termination_reason": reason,
            "terminated_by": current_user.id,
            "final_summary": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate exam session"
        )
