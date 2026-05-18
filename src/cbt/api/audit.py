"""
Audit log query API for admin/officer access.
"""

from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..services.audit_service import AuditService
from ..models.security import AuditLog, AuditAction
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", dependencies=[Depends(require_permission("admin.read"))])
async def list_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Any = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> List[dict]:
    """Query audit logs with optional filters (admin/officer only)."""
    svc = AuditService(db)
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown audit action '{action}'",
            )
    logs = await svc.get_audit_logs(
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action.value,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "success": log.success,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "details": (log.new_values or {}).get("details"),
        }
        for log in logs
    ]


@router.get("/security-events", dependencies=[Depends(require_permission("admin.read"))])
async def list_security_events(
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="OPEN or RESOLVED"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Any = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> List[dict]:
    """Query security events with optional filters (admin only)."""
    svc = AuditService(db)
    events = await svc.get_security_events(
        user_id=user_id,
        event_type=event_type,
        severity=severity,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "severity": e.severity,
            "description": e.description,
            "user_id": e.user_id,
            "resolved": e.resolved,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/summary", dependencies=[Depends(require_permission("admin.read"))])
async def security_summary(
    hours: int = Query(24, ge=1, le=168),
    db: Any = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict:
    """Return system security summary for the last N hours (admin dashboard)."""
    svc = AuditService(db)
    return await svc.get_system_security_summary(hours=hours)
