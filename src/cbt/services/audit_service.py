"""
Audit service for comprehensive logging and security monitoring (MongoDB / Beanie).
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from ..models.security import AuditLog, AuditAction, SecurityEvent
from ..core.redis import cache_manager


class AuditService:
    """Audit logging and security monitoring service."""

    def __init__(self, db: Any = None):
        # ``db`` retained for API compatibility; persistence uses Beanie documents.
        self.db = db
        self.cache = cache_manager

    async def log_action(
        self,
        user_id: Optional[str],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
    ):
        nv = dict(new_values) if new_values else {}
        if details:
            nv["details"] = details
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=nv or None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        await audit_log.insert()

    async def log_request_start(
        self,
        user_id: Optional[str],
        method: str,
        path: str,
        query_params: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log request start for audit trail."""
        await self.log_action(
            user_id=user_id,
            action=AuditAction.SYSTEM_CHANGE,
            resource_type="request",
            details=f"{method} {path}",
            ip_address=ip_address,
            user_agent=user_agent,
            new_values={
                "method": method,
                "path": path,
                "query_params": query_params,
                "session_id": session_id,
                "request_start": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def log_request_end(
        self,
        user_id: Optional[str],
        method: str,
        path: str,
        status_code: int,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log request completion for audit trail."""
        await self.log_action(
            user_id=user_id,
            action=AuditAction.SYSTEM_CHANGE,
            resource_type="request",
            details=f"{method} {path} - {status_code}",
            success=success,
            error_message=error_message,
            new_values={
                "method": method,
                "path": path,
                "status_code": status_code,
                "session_id": session_id,
                "request_end": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        event_data: Optional[Dict] = None,
        affected_resources: Optional[List] = None,
    ):
        """Persist a security event."""
        desc_parts = [description]
        if user_agent:
            desc_parts.append(f"ua={user_agent}")
        if device_fingerprint:
            desc_parts.append(f"device={device_fingerprint}")
        if event_data:
            desc_parts.append(f"data={json.dumps(event_data, default=str)[:500]}")
        if affected_resources:
            desc_parts.append(f"resources={affected_resources!s}"[:500])
        full_description = " | ".join(desc_parts)[:4000]

        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=full_description,
            user_id=user_id,
            ip_address=ip_address,
            resolved=False,
        )
        await security_event.insert()

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Get audit logs with filtering."""
        clauses: List[Any] = []
        if user_id:
            clauses.append(AuditLog.user_id == user_id)
        if action:
            clauses.append(AuditLog.action == action)
        if resource_type:
            clauses.append(AuditLog.resource_type == resource_type)
        if resource_id:
            clauses.append(AuditLog.resource_id == resource_id)
        if start_date:
            clauses.append(AuditLog.created_at >= start_date)
        if end_date:
            clauses.append(AuditLog.created_at <= end_date)

        q = AuditLog.find(*clauses) if clauses else AuditLog.find_all()
        return await q.sort(-AuditLog.created_at).skip(offset).limit(limit).to_list()

    async def get_security_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityEvent]:
        """Get security events with filtering."""
        clauses: List[Any] = []
        if user_id:
            clauses.append(SecurityEvent.user_id == user_id)
        if event_type:
            clauses.append(SecurityEvent.event_type == event_type)
        if severity:
            clauses.append(SecurityEvent.severity == severity)
        if status is not None:
            if status.upper() == "OPEN":
                clauses.append(SecurityEvent.resolved == False)
            elif status.upper() == "RESOLVED":
                clauses.append(SecurityEvent.resolved == True)
        if start_date:
            clauses.append(SecurityEvent.created_at >= start_date)
        if end_date:
            clauses.append(SecurityEvent.created_at <= end_date)

        q = SecurityEvent.find(*clauses) if clauses else SecurityEvent.find_all()
        return await q.sort(-SecurityEvent.created_at).skip(offset).limit(limit).to_list()

    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        audit_logs = await self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000,
        )

        security_events = await self.get_security_events(
            user_id=user_id,
            start_date=start_date,
            limit=100,
        )

        login_count = len([log for log in audit_logs if log.action == AuditAction.LOGIN])
        failed_logins = len(
            [log for log in audit_logs if log.action == AuditAction.LOGIN and not log.success]
        )
        exam_starts = len([log for log in audit_logs if log.action == AuditAction.EXAM_START])
        exam_submissions = len([log for log in audit_logs if log.action == AuditAction.EXAM_SUBMIT])

        recent_logs = audit_logs[:10]

        return {
            "user_id": user_id,
            "period_days": days,
            "login_count": login_count,
            "failed_login_attempts": failed_logins,
            "exam_starts": exam_starts,
            "exam_submissions": exam_submissions,
            "total_actions": len(audit_logs),
            "security_events": len(security_events),
            "recent_activity": [
                {
                    "action": log.action.value,
                    "resource_type": log.resource_type,
                    "description": (log.new_values or {}).get("details", log.action.value),
                    "timestamp": log.created_at,
                    "success": log.success,
                }
                for log in recent_logs
            ],
        }

    async def get_system_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get system security summary."""
        start_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        security_events = await self.get_security_events(
            start_date=start_date,
            limit=1000,
        )

        critical_events = [event for event in security_events if event.severity == "CRITICAL"]
        high_events = [event for event in security_events if event.severity == "HIGH"]
        medium_events = [event for event in security_events if event.severity == "MEDIUM"]
        low_events = [event for event in security_events if event.severity == "LOW"]

        event_types: Dict[str, int] = {}
        for event in security_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        status_breakdown = {
            "OPEN": len([e for e in security_events if not e.resolved]),
            "INVESTIGATING": 0,
            "RESOLVED": len([e for e in security_events if e.resolved]),
        }

        return {
            "period_hours": hours,
            "total_events": len(security_events),
            "severity_breakdown": {
                "critical": len(critical_events),
                "high": len(high_events),
                "medium": len(medium_events),
                "low": len(low_events),
            },
            "status_breakdown": status_breakdown,
            "event_types": event_types,
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "description": event.description,
                    "timestamp": event.created_at,
                    "status": "RESOLVED" if event.resolved else "OPEN",
                }
                for event in security_events[:10]
            ],
        }

    async def resolve_security_event(
        self,
        event_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Mark a security event resolved."""
        event = await SecurityEvent.find_one(SecurityEvent.id == event_id)
        if not event:
            return False

        event.resolved = True
        event.resolved_at = datetime.now(timezone.utc)
        event.resolution_notes = resolution_notes
        await event.save()

        await self.log_action(
            user_id=resolved_by,
            action=AuditAction.SYSTEM_CHANGE,
            resource_type="security_event",
            resource_id=event_id,
            details=f"Resolved security event: {event.event_type}",
            new_values={
                "resolved": True,
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes,
            },
        )

        return True

    async def export_audit_logs(self, start_date: datetime, end_date: datetime, format: str = "json") -> str:
        """Export audit logs for compliance."""
        logs = await self.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )

        if format == "json":
            return json.dumps(
                [
                    {
                        "id": log.id,
                        "user_id": log.user_id,
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "description": (log.new_values or {}).get("details", ""),
                        "ip_address": str(log.ip_address) if log.ip_address else None,
                        "success": log.success,
                        "error_message": log.error_message,
                        "created_at": log.created_at.isoformat(),
                    }
                    for log in logs
                ],
                indent=2,
            )

        return ""

    async def cleanup_old_logs(self, days: int = 365) -> int:
        """Clean up old audit logs (placeholder)."""
        _ = datetime.now(timezone.utc) - timedelta(days=days)
        return 0
