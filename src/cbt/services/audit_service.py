"""
Audit service for comprehensive logging and security monitoring.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..models.security import AuditLog, AuditAction, SecurityEvent
from ..core.redis import cache_manager


class AuditService:
    """Audit logging and security monitoring service."""
    
    def __init__(self, db: Any = None):
        self.db = db
        self.cache = cache_manager
    
    async def log_action(self, user_id: Optional[str], action: AuditAction,
                        resource_type: str, resource_id: Optional[str] = None,
                        details: Optional[str] = None, ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None, success: bool = True,
                        error_message: Optional[str] = None, old_values: Optional[Dict] = None,
                        new_values: Optional[Dict] = None):
        """
        Log audit action.
        
        Args:
            user_id: User ID
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID
            details: Action details
            ip_address: Client IP address
            user_agent: User agent string
            success: Action success
            error_message: Error message
            old_values: Previous state
            new_values: New state
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        if self.db:
            self.db.add(audit_log)
            await self.db.commit()
    
    async def log_request_start(self, user_id: Optional[str], method: str, path: str,
                               query_params: str, ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None, session_id: Optional[str] = None):
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
                "request_start": datetime.utcnow().isoformat()
            }
        )
    
    async def log_request_end(self, user_id: Optional[str], method: str, path: str,
                             status_code: int, success: bool = True,
                             error_message: Optional[str] = None, session_id: Optional[str] = None):
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
                "request_end": datetime.utcnow().isoformat()
            }
        )
    
    async def log_security_event(self, event_type: str, severity: str, description: str,
                                user_id: Optional[str] = None, ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None, device_fingerprint: Optional[str] = None,
                                event_data: Optional[Dict] = None, affected_resources: Optional[List] = None):
        """
        Log security event.
        
        Args:
            event_type: Event type
            severity: Event severity
            description: Event description
            user_id: User ID
            ip_address: Client IP address
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            event_data: Additional event data
            affected_resources: List of affected resources
        """
        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            event_data=event_data,
            affected_resources=affected_resources,
            status="OPEN"
        )
        
        if self.db:
            self.db.add(security_event)
            await self.db.commit()
    
    async def get_audit_logs(self, user_id: Optional[str] = None, action: Optional[AuditAction] = None,
                           resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                           start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                           limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """
        Get audit logs with filtering.
        
        Args:
            user_id: Filter by user ID
            action: Filter by action
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Result limit
            offset: Result offset
            
        Returns:
            List[AuditLog]: Audit logs
        """
        if not self.db:
            return []
        
        query = select(AuditLog)
        
        # Apply filters
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(AuditLog.created_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_security_events(self, user_id: Optional[str] = None, event_type: Optional[str] = None,
                                 severity: Optional[str] = None, status: Optional[str] = None,
                                 start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                                 limit: int = 100, offset: int = 0) -> List[SecurityEvent]:
        """
        Get security events with filtering.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            severity: Filter by severity
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Result limit
            offset: Result offset
            
        Returns:
            List[SecurityEvent]: Security events
        """
        if not self.db:
            return []
        
        query = select(SecurityEvent)
        
        # Apply filters
        if user_id:
            query = query.where(SecurityEvent.user_id == user_id)
        
        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)
        
        if severity:
            query = query.where(SecurityEvent.severity == severity)
        
        if status:
            query = query.where(SecurityEvent.status == status)
        
        if start_date:
            query = query.where(SecurityEvent.created_at >= start_date)
        
        if end_date:
            query = query.where(SecurityEvent.created_at <= end_date)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(SecurityEvent.created_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dict[str, Any]: Activity summary
        """
        if not self.db:
            return {}
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get audit logs for user
        audit_logs = await self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
        
        # Get security events for user
        security_events = await self.get_security_events(
            user_id=user_id,
            start_date=start_date,
            limit=100
        )
        
        # Analyze activity
        login_count = len([log for log in audit_logs if log.action == AuditAction.LOGIN])
        failed_logins = len([log for log in audit_logs if log.action == AuditAction.LOGIN and not log.success])
        exam_starts = len([log for log in audit_logs if log.action == AuditAction.EXAM_START])
        exam_submissions = len([log for log in audit_logs if log.action == AuditAction.EXAM_SUBMIT])
        
        # Recent activity
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
                    "description": log.action_description,
                    "timestamp": log.created_at,
                    "success": log.success
                }
                for log in recent_logs
            ]
        }
    
    async def get_system_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get system security summary.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict[str, Any]: Security summary
        """
        if not self.db:
            return {}
        
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        # Get security events
        security_events = await self.get_security_events(
            start_date=start_date,
            limit=1000
        )
        
        # Analyze events
        critical_events = [event for event in security_events if event.severity == "CRITICAL"]
        high_events = [event for event in security_events if event.severity == "HIGH"]
        medium_events = [event for event in security_events if event.severity == "MEDIUM"]
        low_events = [event for event in security_events if event.severity == "LOW"]
        
        # Event types
        event_types = {}
        for event in security_events:
            event_type = event.event_type
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        # Status breakdown
        status_breakdown = {
            "OPEN": len([event for event in security_events if event.status == "OPEN"]),
            "INVESTIGATING": len([event for event in security_events if event.status == "INVESTIGATING"]),
            "RESOLVED": len([event for event in security_events if event.status == "RESOLVED"])
        }
        
        return {
            "period_hours": hours,
            "total_events": len(security_events),
            "severity_breakdown": {
                "critical": len(critical_events),
                "high": len(high_events),
                "medium": len(medium_events),
                "low": len(low_events)
            },
            "status_breakdown": status_breakdown,
            "event_types": event_types,
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "description": event.description,
                    "timestamp": event.created_at,
                    "status": event.status
                }
                for event in security_events[:10]
            ]
        }
    
    async def resolve_security_event(self, event_id: str, resolved_by: str,
                                    resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve security event.
        
        Args:
            event_id: Event ID
            resolved_by: User ID resolving the event
            resolution_notes: Resolution notes
            
        Returns:
            bool: Resolution success
        """
        if not self.db:
            return False
        
        # Get event
        result = await self.db.execute(
            select(SecurityEvent).where(SecurityEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        
        if not event:
            return False
        
        # Update event
        event.status = "RESOLVED"
        event.resolved_at = datetime.utcnow()
        event.resolved_by = resolved_by
        event.resolution_notes = resolution_notes
        event.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Log resolution
        await self.log_action(
            user_id=resolved_by,
            action=AuditAction.SYSTEM_CHANGE,
            resource_type="security_event",
            resource_id=event_id,
            details=f"Resolved security event: {event.event_type}",
            new_values={
                "status": "RESOLVED",
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes
            }
        )
        
        return True
    
    async def export_audit_logs(self, start_date: datetime, end_date: datetime,
                               format: str = "json") -> str:
        """
        Export audit logs for compliance.
        
        Args:
            start_date: Start date
            end_date: End date
            format: Export format (json, csv)
            
        Returns:
            str: Exported data
        """
        # Get logs
        logs = await self.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "json":
            return json.dumps([
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action.value,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.action_description,
                    "ip_address": str(log.ip_address) if log.ip_address else None,
                    "success": log.success,
                    "error_message": log.error_message,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ], indent=2)
        
        # CSV format would be implemented here
        return ""
    
    async def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Clean up old audit logs.
        
        Args:
            days: Age in days to keep
            
        Returns:
            int: Number of logs cleaned up
        """
        if not self.db:
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # This would implement actual cleanup logic
        # For now, return 0
        return 0
