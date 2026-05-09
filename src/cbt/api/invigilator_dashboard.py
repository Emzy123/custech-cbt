"""
Invigilator monitoring dashboard API endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.proctoring import (
    ProctoringDashboard, ProctoringSessionStatus, InvigilatorAction,
    ProctoringAlert, ProctoringIntervention
)
from ..services.invigilator_dashboard_service import InvigilatorDashboardService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/invigilator-dashboard", tags=["invigilator-dashboard"])


@router.get("/examination/{examination_id}/dashboard", response_model=ProctoringDashboard)
@require_permission("exam.invigilate")
async def get_dashboard(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ProctoringDashboard:
    """Get invigilator dashboard for examination."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        return ProctoringDashboard(**dashboard)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )


@router.get("/examination/{examination_id}/student/{student_id}/detail")
@require_permission("exam.invigilate")
async def get_student_detail(
    examination_id: str,
    student_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed student information."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        detail = await dashboard_service.get_student_detail(
            examination_id, student_id, current_user.id
        )
        return detail
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student detail"
        )


@router.post("/examination/{examination_id}/student/{student_id}/message")
@require_permission("exam.invigilate")
async def send_student_message(
    examination_id: str,
    student_id: str,
    message: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Send message to student."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        result = await dashboard_service.send_student_message(
            examination_id, student_id, message, current_user.id
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
            detail="Failed to send message"
        )


@router.post("/examination/{examination_id}/student/{student_id}/pause")
@require_permission("exam.invigilate")
async def pause_student_exam(
    examination_id: str,
    student_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pause student's exam."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        result = await dashboard_service.pause_student_exam(
            examination_id, student_id, reason, current_user.id
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
            detail="Failed to pause exam"
        )


@router.post("/examination/{examination_id}/student/{student_id}/resume")
@require_permission("exam.invigilate")
async def resume_student_exam(
    examination_id: str,
    student_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Resume paused student's exam."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        result = await dashboard_service.resume_student_exam(
            examination_id, student_id, current_user.id
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
            detail="Failed to resume exam"
        )


@router.post("/examination/{examination_id}/student/{student_id}/terminate")
@require_permission("exam.invigilate")
async def terminate_student_exam(
    examination_id: str,
    student_id: str,
    reason: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Terminate student's exam."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        result = await dashboard_service.terminate_student_exam(
            examination_id, student_id, reason, current_user.id
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
            detail="Failed to terminate exam"
        )


@router.post("/alert/{alert_id}/acknowledge")
@require_permission("exam.invigilate")
async def acknowledge_alert(
    alert_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Acknowledge proctoring alert."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        result = await dashboard_service.acknowledge_alert(alert_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.get("/examination/{examination_id}/students")
@require_permission("exam.invigilate")
async def get_student_sessions(
    examination_id: str,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get student sessions with filtering."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        sessions = dashboard.get("student_sessions", [])
        
        # Apply filters
        if status:
            sessions = [s for s in sessions if s.get("status") == status]
        
        if risk_level:
            if risk_level == "high":
                sessions = [s for s in sessions if s.get("risk_score", 0) > 70]
            elif risk_level == "medium":
                sessions = [s for s in sessions if 40 < s.get("risk_score", 0) <= 70]
            elif risk_level == "low":
                sessions = [s for s in sessions if s.get("risk_score", 0) <= 40]
        
        # Apply limit
        if len(sessions) > limit:
            sessions = sessions[:limit]
        
        return {
            "examination_id": examination_id,
            "students": sessions,
            "total_students": len(dashboard.get("student_sessions", [])),
            "filtered_students": len(sessions),
            "filters": {
                "status": status,
                "risk_level": risk_level,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student sessions"
        )


@router.get("/examination/{examination_id}/alerts")
@require_permission("exam.invigilate")
async def get_examination_alerts(
    examination_id: str,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get examination alerts with filtering."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        alerts = dashboard.get("alerts", [])
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.get("acknowledged", False) == acknowledged]
        
        # Apply limit
        if len(alerts) > limit:
            alerts = alerts[:limit]
        
        return {
            "examination_id": examination_id,
            "alerts": alerts,
            "total_alerts": len(dashboard.get("alerts", [])),
            "filtered_alerts": len(alerts),
            "filters": {
                "severity": severity,
                "acknowledged": acknowledged,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get examination alerts"
        )


@router.get("/examination/{examination_id}/statistics")
@require_permission("exam.invigilate")
async def get_examination_statistics(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed examination statistics."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        return {
            "examination_id": examination_id,
            "statistics": dashboard.get("statistics", {}),
            "generated_at": dashboard.get("last_updated")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get examination statistics"
        )


@router.get("/examination/{examination_id}/high-risk-students")
@require_permission("exam.invigilate")
async def get_high_risk_students(
    examination_id: str,
    threshold: int = 70,
    limit: int = 20,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get high-risk students."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        sessions = dashboard.get("student_sessions", [])
        high_risk = [s for s in sessions if s.get("risk_score", 0) >= threshold]
        
        # Sort by risk score (highest first)
        high_risk.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        # Apply limit
        if len(high_risk) > limit:
            high_risk = high_risk[:limit]
        
        return {
            "examination_id": examination_id,
            "threshold": threshold,
            "high_risk_students": high_risk,
            "total_high_risk": len([s for s in sessions if s.get("risk_score", 0) >= threshold]),
            "showing": len(high_risk)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get high-risk students"
        )


@router.get("/examination/{examination_id}/recent-events")
@require_permission("exam.invigilate")
async def get_recent_events(
    examination_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get recent proctoring events."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        all_events = []
        
        # Collect events from all student sessions
        for session in dashboard.get("student_sessions", []):
            student_id = session.get("student_id")
            
            # Get proctoring events
            proctoring_events = await dashboard_service._get_student_proctoring_events(
                examination_id, student_id
            )
            
            for event in proctoring_events:
                all_events.append({
                    **event,
                    "student_id": student_id,
                    "event_source": "proctoring"
                })
        
        # Filter by event type if specified
        if event_type:
            all_events = [e for e in all_events if e.get("event_type") == event_type]
        
        # Sort by timestamp (newest first)
        all_events.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        # Apply limit
        if len(all_events) > limit:
            all_events = all_events[:limit]
        
        return {
            "examination_id": examination_id,
            "events": all_events,
            "total_events": len(all_events),
            "filters": {
                "event_type": event_type,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent events"
        )


@router.post("/examination/{examination_id}/broadcast-message")
@require_permission("exam.invigilate")
async def broadcast_message(
    examination_id: str,
    message: str,
    target_students: Optional[List[str]] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Broadcast message to multiple students."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        # Determine target students
        if target_students:
            target_student_ids = target_students
        else:
            # Send to all students
            target_student_ids = [
                s.get("student_id") 
                for s in dashboard.get("student_sessions", [])
                if s.get("student_id")
            ]
        
        results = []
        for student_id in target_student_ids:
            try:
                result = await dashboard_service.send_student_message(
                    examination_id, student_id, message, current_user.id
                )
                results.append({
                    "student_id": student_id,
                    "success": True,
                    "message_id": result.get("message_id")
                })
            except Exception as e:
                results.append({
                    "student_id": student_id,
                    "success": False,
                    "error": str(e)
                })
        
        successful_count = len([r for r in results if r.get("success")])
        
        return {
            "examination_id": examination_id,
            "message": message,
            "target_students": target_student_ids,
            "total_sent": len(target_student_ids),
            "successful": successful_count,
            "failed": len(target_student_ids) - successful_count,
            "results": results,
            "broadcast_by": current_user.id,
            "broadcast_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message"
        )


@router.get("/examination/{examination_id}/audit-log")
@require_permission("exam.invigilate")
async def get_audit_log(
    examination_id: str,
    action_type: Optional[str] = None,
    limit: int = 200,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get invigilator action audit log."""
    try:
        # Get audit log from cache
        audit_cache_key = f"invigilator_audit:{examination_id}"
        dashboard_service = InvigilatorDashboardService(db)
        audit_events = await dashboard_service.cache.get(audit_cache_key) or []
        
        # Filter by action type if specified
        if action_type:
            audit_events = [e for e in audit_events if e.get("action") == action_type]
        
        # Sort by timestamp (newest first)
        audit_events.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        # Apply limit
        if len(audit_events) > limit:
            audit_events = audit_events[:limit]
        
        return {
            "examination_id": examination_id,
            "audit_events": audit_events,
            "total_events": len(audit_events),
            "filters": {
                "action_type": action_type,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log"
        )


@router.post("/examination/{examination_id}/force-refresh")
@require_permission("exam.invigilate")
async def force_refresh_dashboard(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Force refresh dashboard data."""
    try:
        # Clear cache to force refresh
        cache_key = f"dashboard:{examination_id}:{current_user.id}"
        dashboard_service = InvigilatorDashboardService(db)
        await dashboard_service.cache.delete(cache_key)
        
        # Get fresh data
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        return {
            "examination_id": examination_id,
            "refreshed_at": datetime.utcnow(),
            "dashboard_data": dashboard
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh dashboard"
        )


@router.get("/examination/{examination_id}/system-status")
@require_permission("exam.invigilate")
async def get_system_status(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get system status for examination."""
    try:
        dashboard_service = InvigilatorDashboardService(db)
        dashboard = await dashboard_service.get_dashboard_data(
            examination_id, current_user.id
        )
        
        # Calculate system health metrics
        total_students = len(dashboard.get("student_sessions", []))
        active_sessions = len([s for s in dashboard.get("student_sessions", []) if s.get("status") == "active"])
        total_alerts = len(dashboard.get("alerts", []))
        high_severity_alerts = len([a for a in dashboard.get("alerts", []) if a.get("severity") == "high"])
        
        # System status calculation
        system_health = 100
        if total_alerts > 0:
            system_health -= (high_severity_alerts / total_alerts) * 30
        if total_students > 0:
            system_health -= ((total_students - active_sessions) / total_students) * 20
        
        system_health = max(0, system_health)
        
        return {
            "examination_id": examination_id,
            "system_health": round(system_health, 2),
            "status": "healthy" if system_health > 80 else "warning" if system_health > 60 else "critical",
            "metrics": {
                "total_students": total_students,
                "active_sessions": active_sessions,
                "total_alerts": total_alerts,
                "high_severity_alerts": high_severity_alerts
            },
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )
