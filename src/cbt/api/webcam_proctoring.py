"""
Webcam proctoring API endpoints with AI-assisted anomaly detection.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from ..schemas.proctoring import (
    ProctoringSessionStart, ProctoringSessionResponse, WebcamCaptureRequest,
    WebcamCaptureResponse, IdentityVerificationRequest, IdentityVerificationResponse,
    ProctoringSummary, ProctoringAlert
)
from ..services.webcam_proctoring_service import WebcamProctoringService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/webcam-proctoring", tags=["webcam-proctoring"])


@router.post("/session/start", response_model=ProctoringSessionResponse, dependencies=[Depends(require_permission("exam.start"))])
async def start_webcam_session(
    session_data: ProctoringSessionStart,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ProctoringSessionResponse:
    """Start webcam proctoring session."""
    try:
        proctoring_service = WebcamProctoringService(db)
        session = await proctoring_service.start_webcam_session(
            session_data.examination_id,
            session_data.student_id,
            session_data.device_info
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
            detail="Failed to start webcam session"
        )


@router.post("/session/{session_id}/capture", response_model=WebcamCaptureResponse, dependencies=[Depends(require_permission("exam.active"))])
async def capture_snapshot(
    session_id: str,
    capture_data: WebcamCaptureRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> WebcamCaptureResponse:
    """Capture and analyze webcam snapshot."""
    try:
        proctoring_service = WebcamProctoringService(db)
        result = await proctoring_service.capture_snapshot(
            session_id, capture_data.image_data, capture_data.timestamp
        )
        return WebcamCaptureResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture snapshot"
        )


@router.post("/session/{session_id}/verify-identity", response_model=IdentityVerificationResponse, dependencies=[Depends(require_permission("exam.active"))])
async def verify_identity(
    session_id: str,
    verification_data: IdentityVerificationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> IdentityVerificationResponse:
    """Verify student identity using facial recognition."""
    try:
        proctoring_service = WebcamProctoringService(db)
        result = await proctoring_service.verify_identity(
            session_id, verification_data.current_image, verification_data.reference_photo
        )
        return IdentityVerificationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify identity"
        )


@router.get("/session/{session_id}/summary", response_model=ProctoringSummary, dependencies=[Depends(require_permission("exam.read"))])
async def get_session_summary(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ProctoringSummary:
    """Get webcam proctoring session summary."""
    try:
        proctoring_service = WebcamProctoringService(db)
        summary = await proctoring_service.get_session_summary(session_id)
        return ProctoringSummary(**summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session summary"
        )


@router.post("/session/{session_id}/end", dependencies=[Depends(require_permission("exam.manage"))])
async def end_webcam_session(
    session_id: str,
    reason: Optional[str] = "exam_completed",
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """End webcam proctoring session."""
    try:
        proctoring_service = WebcamProctoringService(db)
        summary = await proctoring_service.end_webcam_session(session_id, reason)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end webcam session"
        )


@router.get("/session/{session_id}", dependencies=[Depends(require_permission("exam.read"))])
async def get_webcam_session(
    session_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get webcam session details."""
    try:
        proctoring_service = WebcamProctoringService(db)
        session = await proctoring_service._get_webcam_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webcam session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webcam session"
        )


@router.get("/examination/{examination_id}/active-sessions", dependencies=[Depends(require_permission("exam.manage"))])
async def get_active_sessions(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all active webcam sessions for examination."""
    try:
        proctoring_service = WebcamProctoringService(db)
        sessions = await proctoring_service.get_active_sessions(examination_id)
        return {
            "examination_id": examination_id,
            "active_sessions": sessions,
            "total_active": len(sessions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active sessions"
        )


@router.get("/examination/{examination_id}/alerts", dependencies=[Depends(require_permission("exam.manage"))])
async def get_proctoring_alerts(
    examination_id: str,
    severity: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[ProctoringAlert]:
    """Get webcam proctoring alerts for examination."""
    try:
        proctoring_service = WebcamProctoringService(db)
        alerts = await proctoring_service.get_alerts(examination_id, severity)
        return [ProctoringAlert(**alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proctoring alerts"
        )


@router.post("/alert/{alert_id}/acknowledge", dependencies=[Depends(require_permission("exam.manage"))])
async def acknowledge_alert(
    alert_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Acknowledge proctoring alert."""
    try:
        proctoring_service = WebcamProctoringService(db)
        success = await proctoring_service.acknowledge_alert(alert_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        return {"success": True, "acknowledged_by": current_user.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.post("/session/{session_id}/capture/upload", dependencies=[Depends(require_permission("exam.active"))])
async def upload_snapshot(
    session_id: str,
    file: UploadFile = File(...),
    timestamp: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload webcam snapshot as file."""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Read file content
        content = await file.read()
        
        # Convert to base64
        import base64
        image_data = f"data:{file.content_type};base64,{base64.b64encode(content).decode()}"
        
        # Parse timestamp
        from datetime import datetime
        capture_timestamp = datetime.utcnow()
        if timestamp:
            try:
                capture_timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                pass  # Use current time if invalid
        
        # Process capture
        proctoring_service = WebcamProctoringService(db)
        result = await proctoring_service.capture_snapshot(
            session_id, image_data, capture_timestamp
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "analysis": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload snapshot"
        )


@router.post("/session/{session_id}/verify-identity/upload", dependencies=[Depends(require_permission("exam.active"))])
async def upload_identity_verification(
    session_id: str,
    current_image: UploadFile = File(...),
    reference_image: UploadFile = File(...),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload images for identity verification."""
    try:
        if not current_image.content_type.startswith('image/') or not reference_image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Read files
        current_content = await current_image.read()
        reference_content = await reference_image.read()
        
        # Convert to base64
        import base64
        current_data = f"data:{current_image.content_type};base64,{base64.b64encode(current_content).decode()}"
        reference_data = f"data:{reference_image.content_type};base64,{base64.b64encode(reference_content).decode()}"
        
        # Perform verification
        proctoring_service = WebcamProctoringService(db)
        result = await proctoring_service.verify_identity(
            session_id, current_data, reference_data
        )
        
        return {
            "success": True,
            "verification": result,
            "files": {
                "current_image": current_image.filename,
                "reference_image": reference_image.filename
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify identity"
        )


@router.get("/session/{session_id}/snapshots", dependencies=[Depends(require_permission("exam.read"))])
async def get_session_snapshots(
    session_id: str,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get webcam snapshots for session."""
    try:
        proctoring_service = WebcamProctoringService(db)
        session = await proctoring_service._get_webcam_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webcam session not found"
            )
        
        snapshots = session.get("snapshots", [])
        
        # Apply limit
        if len(snapshots) > limit:
            snapshots = snapshots[-limit:]
        
        return {
            "session_id": session_id,
            "snapshots": snapshots,
            "total_snapshots": len(session.get("snapshots", [])),
            "returned_snapshots": len(snapshots)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session snapshots"
        )


@router.get("/session/{session_id}/anomalies", dependencies=[Depends(require_permission("exam.read"))])
async def get_session_anomalies(
    session_id: str,
    anomaly_type: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get anomalies for webcam session."""
    try:
        proctoring_service = WebcamProctoringService(db)
        session = await proctoring_service._get_webcam_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webcam session not found"
            )
        
        anomalies = session.get("anomalies", [])
        
        # Filter by anomaly type if specified
        if anomaly_type:
            filtered_anomalies = []
            for anomaly_event in anomalies:
                for anomaly in anomaly_event.get("anomalies", []):
                    if anomaly.get("type") == anomaly_type:
                        filtered_anomalies.append({
                            "timestamp": anomaly_event["timestamp"],
                            "anomaly": anomaly,
                            "confidence": anomaly_event.get("confidence", 0.0)
                        })
            anomalies = filtered_anomalies
        
        return {
            "session_id": session_id,
            "anomalies": anomalies,
            "total_anomalies": len(session.get("anomalies", [])),
            "filtered_anomalies": len(anomalies)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session anomalies"
        )


@router.get("/examination/{examination_id}/statistics", dependencies=[Depends(require_permission("exam.manage"))])
async def get_proctoring_statistics(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get proctoring statistics for examination."""
    try:
        proctoring_service = WebcamProctoringService(db)
        active_sessions = await proctoring_service.get_active_sessions(examination_id)
        alerts = await proctoring_service.get_alerts(examination_id)
        
        # Calculate statistics
        total_sessions = len(active_sessions)
        high_risk_sessions = sum(1 for s in active_sessions if s.get("risk_score", 0) > 50)
        total_alerts = len(alerts)
        high_severity_alerts = sum(1 for a in alerts if a.get("severity") == "high")
        
        return {
            "examination_id": examination_id,
            "total_active_sessions": total_sessions,
            "high_risk_sessions": high_risk_sessions,
            "total_alerts": total_alerts,
            "high_severity_alerts": high_severity_alerts,
            "average_risk_score": sum(s.get("risk_score", 0) for s in active_sessions) / total_sessions if total_sessions > 0 else 0,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proctoring statistics"
        )


@router.post("/session/{session_id}/force-capture", dependencies=[Depends(require_permission("exam.manage"))])
async def force_capture(
    session_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Force immediate capture (invigilator action)."""
    try:
        proctoring_service = WebcamProctoringService(db)
        session = await proctoring_service._get_webcam_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webcam session not found"
            )
        
        # Update next capture time to now
        session["next_capture_time"] = datetime.utcnow()
        session["force_capture_requested"] = True
        session["force_capture_reason"] = reason
        session["force_capture_requested_by"] = current_user.id
        session["force_capture_requested_at"] = datetime.utcnow()
        
        await proctoring_service._update_webcam_session(session_id, session)
        
        return {
            "success": True,
            "message": "Force capture requested",
            "reason": reason,
            "requested_by": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force capture"
        )
