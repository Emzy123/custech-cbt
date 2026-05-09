"""
Invigilator monitoring dashboard service for real-time exam proctoring.
"""

import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.exam import Examination, ExamInstance, ExamInstanceStatus
from ..models.student import Student
from ..models.security import SecurityEvent
from ..services.proctoring_service import ProctoringService
from ..services.webcam_proctoring_service import WebcamProctoringService
from ..core.redis import cache_manager


class InvigilatorDashboardService:
    """Invigilator dashboard service for real-time monitoring."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.proctoring_service = ProctoringService(db)
        self.webcam_service = WebcamProctoringService(db)
    
    async def get_dashboard_data(self, examination_id: str, invigilator_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for an examination.
        
        Args:
            examination_id: Examination ID
            invigilator_id: Invigilator user ID
            
        Returns:
            Dashboard data with student grid, alerts, and statistics
        """
        try:
            # Get examination details
            exam_result = await self.db.execute(
                select(Examination).where(Examination.id == examination_id)
            )
            exam = exam_result.scalar_one_or_none()
            if not exam:
                raise ValueError("Examination not found")
            
            # Get active exam instances
            instances_result = await self.db.execute(
                select(ExamInstance, Student)
                .join(Student, ExamInstance.student_id == Student.id)
                .where(
                    and_(
                        ExamInstance.examination_id == examination_id,
                        ExamInstance.status == ExamInstanceStatus.IN_PROGRESS
                    )
                )
            )
            instances = instances_result.all()
            
            # Get student session data
            student_sessions = []
            for instance, student in instances:
                session_data = await self._get_student_session_data(
                    examination_id, student.id, instance.id
                )
                student_sessions.append(session_data)
            
            # Get alerts
            alerts = await self._get_active_alerts(examination_id)
            
            # Calculate statistics
            statistics = await self._calculate_examination_statistics(
                examination_id, student_sessions, alerts
            )
            
            # Build dashboard
            dashboard = {
                "examination_id": examination_id,
                "examination_title": exam.title,
                "examination_date": exam.exam_date,
                "start_time": exam.start_time,
                "end_time": exam.start_time + timedelta(minutes=exam.duration_minutes),
                "invigilator_id": invigilator_id,
                "student_sessions": student_sessions,
                "alerts": alerts,
                "statistics": statistics,
                "last_updated": datetime.utcnow()
            }
            
            # Cache dashboard data
            cache_key = f"dashboard:{examination_id}:{invigilator_id}"
            await self.cache.set(cache_key, dashboard, ttl=60)  # 1 minute cache
            
            return dashboard
            
        except Exception as e:
            raise ValueError(f"Failed to get dashboard data: {str(e)}")
    
    async def get_student_detail(self, examination_id: str, student_id: str, 
                               invigilator_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific student.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            invigilator_id: Invigilator user ID
            
        Returns:
            Detailed student information
        """
        try:
            # Get student and instance
            result = await self.db.execute(
                select(ExamInstance, Student)
                .join(Student, ExamInstance.student_id == Student.id)
                .where(
                    and_(
                        ExamInstance.examination_id == examination_id,
                        ExamInstance.student_id == student_id,
                        ExamInstance.status == ExamInstanceStatus.IN_PROGRESS
                    )
                )
            )
            instance_student = result.first()
            if not instance_student:
                raise ValueError("Student not found in active examination")
            
            instance, student = instance_student
            
            # Get comprehensive session data
            session_data = await self._get_student_session_data(
                examination_id, student_id, instance.id
            )
            
            # Get detailed proctoring events
            proctoring_events = await self._get_student_proctoring_events(
                examination_id, student_id
            )
            
            # Get webcam snapshots
            webcam_snapshots = await self._get_student_webcam_snapshots(
                examination_id, student_id
            )
            
            # Get security events
            security_events = await self._get_student_security_events(student_id)
            
            # Calculate risk assessment
            risk_assessment = await self._calculate_student_risk_assessment(
                session_data, proctoring_events, security_events
            )
            
            return {
                "student_info": {
                    "id": student.id,
                    "matric_number": student.matric_number,
                    "full_name": student.full_name,
                    "email": student.email,
                    "department": student.department,
                    "level": student.level
                },
                "exam_instance": {
                    "id": instance.id,
                    "start_time": instance.start_time,
                    "time_remaining": self._calculate_time_remaining(instance),
                    "answered_questions": instance.get("answered_questions", 0),
                    "total_questions": instance.get("total_questions", 0),
                    "status": instance.status.value
                },
                "proctoring_session": session_data,
                "proctoring_events": proctoring_events,
                "webcam_snapshots": webcam_snapshots,
                "security_events": security_events,
                "risk_assessment": risk_assessment,
                "available_actions": await self._get_available_actions(
                    examination_id, student_id, invigilator_id
                )
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get student detail: {str(e)}")
    
    async def send_student_message(self, examination_id: str, student_id: str, 
                                 message: str, invigilator_id: str) -> Dict[str, Any]:
        """
        Send a message to a student.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            message: Message content
            invigilator_id: Invigilator user ID
            
        Returns:
            Message delivery result
        """
        try:
            # Create message
            message_data = {
                "id": str(uuid.uuid4()),
                "examination_id": examination_id,
                "student_id": student_id,
                "invigilator_id": invigilator_id,
                "message": message,
                "timestamp": datetime.utcnow(),
                "message_type": "invigilator_message",
                "delivered": False,
                "read": False
            }
            
            # Store message in cache for student to retrieve
            message_cache_key = f"student_messages:{examination_id}:{student_id}"
            existing_messages = await self.cache.get(message_cache_key) or []
            existing_messages.append(message_data)
            await self.cache.set(message_cache_key, existing_messages, ttl=7200)
            
            # Also store for invigilator history
            history_cache_key = f"invigilator_messages:{examination_id}:{invigilator_id}"
            history_messages = await self.cache.get(history_cache_key) or []
            history_messages.append(message_data)
            await self.cache.set(history_cache_key, history_messages, ttl=86400)
            
            # Log message
            await self._log_invigilator_action(
                invigilator_id, examination_id, student_id, "message_sent",
                {"message": message}
            )
            
            return {
                "success": True,
                "message_id": message_data["id"],
                "timestamp": message_data["timestamp"]
            }
            
        except Exception as e:
            raise ValueError(f"Failed to send student message: {str(e)}")
    
    async def pause_student_exam(self, examination_id: str, student_id: str, 
                              reason: str, invigilator_id: str) -> Dict[str, Any]:
        """
        Pause a student's exam.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            reason: Reason for pausing
            invigilator_id: Invigilator user ID
            
        Returns:
            Pause result
        """
        try:
            # Get student session
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            
            if proctoring_session_id:
                # Update proctoring session
                proctoring_service = ProctoringService(self.db)
                session = await proctoring_service._get_proctoring_session(proctoring_session_id)
                if session:
                    session["status"] = "paused"
                    session["paused_at"] = datetime.utcnow()
                    session["paused_by"] = invigilator_id
                    session["pause_reason"] = reason
                    await proctoring_service._update_proctoring_session(
                        proctoring_session_id, session
                    )
            
            # Create pause notification
            notification = {
                "id": str(uuid.uuid4()),
                "type": "exam_paused",
                "student_id": student_id,
                "examination_id": examination_id,
                "invigilator_id": invigilator_id,
                "reason": reason,
                "timestamp": datetime.utcnow(),
                "requires_acknowledgment": True
            }
            
            # Store notification
            notification_cache_key = f"student_notifications:{examination_id}:{student_id}"
            existing_notifications = await self.cache.get(notification_cache_key) or []
            existing_notifications.append(notification)
            await self.cache.set(notification_cache_key, existing_notifications, ttl=7200)
            
            # Log action
            await self._log_invigilator_action(
                invigilator_id, examination_id, student_id, "exam_paused",
                {"reason": reason}
            )
            
            return {
                "success": True,
                "paused_at": notification["timestamp"],
                "reason": reason
            }
            
        except Exception as e:
            raise ValueError(f"Failed to pause student exam: {str(e)}")
    
    async def resume_student_exam(self, examination_id: str, student_id: str, 
                               invigilator_id: str) -> Dict[str, Any]:
        """
        Resume a paused student's exam.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            invigilator_id: Invigilator user ID
            
        Returns:
            Resume result
        """
        try:
            # Get student session
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            
            if proctoring_session_id:
                # Update proctoring session
                proctoring_service = ProctoringService(self.db)
                session = await proctoring_service._get_proctoring_session(proctoring_session_id)
                if session and session.get("status") == "paused":
                    session["status"] = "active"
                    session["resumed_at"] = datetime.utcnow()
                    session["resumed_by"] = invigilator_id
                    await proctoring_service._update_proctoring_session(
                        proctoring_session_id, session
                    )
            
            # Create resume notification
            notification = {
                "id": str(uuid.uuid4()),
                "type": "exam_resumed",
                "student_id": student_id,
                "examination_id": examination_id,
                "invigilator_id": invigilator_id,
                "timestamp": datetime.utcnow(),
                "requires_acknowledgment": False
            }
            
            # Store notification
            notification_cache_key = f"student_notifications:{examination_id}:{student_id}"
            existing_notifications = await self.cache.get(notification_cache_key) or []
            existing_notifications.append(notification)
            await self.cache.set(notification_cache_key, existing_notifications, ttl=7200)
            
            # Log action
            await self._log_invigilator_action(
                invigilator_id, examination_id, student_id, "exam_resumed",
                {}
            )
            
            return {
                "success": True,
                "resumed_at": notification["timestamp"]
            }
            
        except Exception as e:
            raise ValueError(f"Failed to resume student exam: {str(e)}")
    
    async def terminate_student_exam(self, examination_id: str, student_id: str, 
                                   reason: str, invigilator_id: str) -> Dict[str, Any]:
        """
        Terminate a student's exam.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            reason: Reason for termination
            invigilator_id: Invigilator user ID
            
        Returns:
            Termination result
        """
        try:
            # Get exam instance
            instance_result = await self.db.execute(
                select(ExamInstance).where(
                    and_(
                        ExamInstance.examination_id == examination_id,
                        ExamInstance.student_id == student_id,
                        ExamInstance.status == ExamInstanceStatus.IN_PROGRESS
                    )
                )
            )
            instance = instance_result.scalar_one_or_none()
            if not instance:
                raise ValueError("Active exam instance not found")
            
            # Update instance status
            instance.status = ExamInstanceStatus.TERMINATED
            instance.end_time = datetime.utcnow()
            await self.db.commit()
            
            # End proctoring sessions
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            if proctoring_session_id:
                proctoring_service = ProctoringService(self.db)
                await proctoring_service.end_proctoring_session(
                    proctoring_session_id, f"terminated_by_invigilator: {reason}"
                )
            
            webcam_session_key = f"webcam_student:{examination_id}:{student_id}"
            webcam_session_id = await self.cache.get(webcam_session_key)
            if webcam_session_id:
                webcam_service = WebcamProctoringService(self.db)
                await webcam_service.end_webcam_session(
                    webcam_session_id, f"terminated_by_invigilator: {reason}"
                )
            
            # Create termination notification
            notification = {
                "id": str(uuid.uuid4()),
                "type": "exam_terminated",
                "student_id": student_id,
                "examination_id": examination_id,
                "invigilator_id": invigilator_id,
                "reason": reason,
                "timestamp": datetime.utcnow(),
                "requires_acknowledgment": True
            }
            
            # Store notification
            notification_cache_key = f"student_notifications:{examination_id}:{student_id}"
            existing_notifications = await self.cache.get(notification_cache_key) or []
            existing_notifications.append(notification)
            await self.cache.set(notification_cache_key, existing_notifications, ttl=7200)
            
            # Log action
            await self._log_invigilator_action(
                invigilator_id, examination_id, student_id, "exam_terminated",
                {"reason": reason}
            )
            
            return {
                "success": True,
                "terminated_at": notification["timestamp"],
                "reason": reason,
                "final_status": "TERMINATED"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to terminate student exam: {str(e)}")
    
    async def acknowledge_alert(self, alert_id: str, invigilator_id: str) -> Dict[str, Any]:
        """
        Acknowledge a proctoring alert.
        
        Args:
            alert_id: Alert ID
            invigilator_id: Invigilator user ID
            
        Returns:
            Acknowledgment result
        """
        try:
            # Get alert from cache (simplified)
            # In production, this would query a database
            
            # Update alert acknowledgment
            acknowledgment = {
                "alert_id": alert_id,
                "acknowledged_by": invigilator_id,
                "acknowledged_at": datetime.utcnow()
            }
            
            # Store acknowledgment
            ack_cache_key = f"alert_acknowledgment:{alert_id}"
            await self.cache.set(ack_cache_key, acknowledgment, ttl=86400)
            
            return {
                "success": True,
                "acknowledged_at": acknowledgment["acknowledged_at"]
            }
            
        except Exception as e:
            raise ValueError(f"Failed to acknowledge alert: {str(e)}")
    
    # Private helper methods
    
    async def _get_student_session_data(self, examination_id: str, student_id: str, 
                                       instance_id: str) -> Dict[str, Any]:
        """Get comprehensive student session data."""
        try:
            # Get proctoring session
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            proctoring_session = None
            
            if proctoring_session_id:
                proctoring_service = ProctoringService(self.db)
                proctoring_session = await proctoring_service._get_proctoring_session(
                    proctoring_session_id
                )
            
            # Get webcam session
            webcam_session_key = f"webcam_student:{examination_id}:{student_id}"
            webcam_session_id = await self.cache.get(webcam_session_key)
            webcam_session = None
            
            if webcam_session_id:
                webcam_service = WebcamProctoringService(self.db)
                webcam_session = await webcam_service._get_webcam_session(webcam_session_id)
            
            # Calculate overall status
            status = "active"
            if proctoring_session and proctoring_session.get("status") == "paused":
                status = "paused"
            elif proctoring_session and proctoring_session.get("status") == "ended":
                status = "ended"
            
            # Calculate risk score
            risk_score = 0
            if proctoring_session:
                risk_score += proctoring_session.get("focus_loss_count", 0) * 5
                risk_score += proctoring_session.get("fullscreen_exits", 0) * 10
                risk_score += proctoring_session.get("keyboard_violations", 0) * 15
                risk_score += proctoring_session.get("clipboard_events", 0) * 5
            
            if webcam_session:
                risk_score += webcam_session.get("anomaly_count", 0) * 10
                risk_score += webcam_session.get("phone_detections", 0) * 25
                risk_score += webcam_session.get("multiple_face_detections", 0) * 20
            
            risk_score = min(risk_score, 100)
            
            return {
                "student_id": student_id,
                "instance_id": instance_id,
                "status": status,
                "proctoring_session": proctoring_session,
                "webcam_session": webcam_session,
                "risk_score": risk_score,
                "last_activity": datetime.utcnow(),
                "security_score": max(0, 100 - risk_score)
            }
            
        except Exception as e:
            return {
                "student_id": student_id,
                "instance_id": instance_id,
                "status": "unknown",
                "risk_score": 0,
                "security_score": 100,
                "error": str(e)
            }
    
    async def _get_active_alerts(self, examination_id: str) -> List[Dict[str, Any]]:
        """Get active alerts for examination."""
        try:
            # Get proctoring alerts
            proctoring_alerts = await self.proctoring_service.get_alerts(examination_id)
            
            # Get webcam alerts
            webcam_alerts = await self.webcam_service.get_alerts(examination_id)
            
            # Combine and sort by severity and timestamp
            all_alerts = []
            
            for alert in proctoring_alerts:
                all_alerts.append({
                    "id": str(uuid.uuid4()),
                    "type": "proctoring",
                    "severity": alert.get("severity", "medium"),
                    "message": alert.get("message", "Proctoring alert"),
                    "student_id": alert.get("student_id"),
                    "timestamp": alert.get("created_at", datetime.utcnow()),
                    "acknowledged": False
                })
            
            for alert in webcam_alerts:
                all_alerts.append({
                    "id": str(uuid.uuid4()),
                    "type": "webcam",
                    "severity": alert.get("severity", "medium"),
                    "message": alert.get("anomaly", {}).get("description", "Webcam alert"),
                    "student_id": alert.get("student_id"),
                    "timestamp": alert.get("timestamp", datetime.utcnow()),
                    "acknowledged": False
                })
            
            # Sort by severity (high first) then timestamp (newest first)
            severity_order = {"high": 3, "medium": 2, "low": 1}
            all_alerts.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["timestamp"]), reverse=True)
            
            return all_alerts[:50]  # Limit to 50 most recent alerts
            
        except Exception as e:
            return []
    
    async def _calculate_examination_statistics(self, examination_id: str, 
                                             student_sessions: List[Dict[str, Any]], 
                                             alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate examination statistics."""
        try:
            total_students = len(student_sessions)
            active_students = len([s for s in student_sessions if s.get("status") == "active"])
            paused_students = len([s for s in student_sessions if s.get("status") == "paused"])
            
            # Risk distribution
            high_risk = len([s for s in student_sessions if s.get("risk_score", 0) > 70])
            medium_risk = len([s for s in student_sessions if 40 < s.get("risk_score", 0) <= 70])
            low_risk = len([s for s in student_sessions if s.get("risk_score", 0) <= 40])
            
            # Alert statistics
            total_alerts = len(alerts)
            high_severity_alerts = len([a for a in alerts if a.get("severity") == "high"])
            unacknowledged_alerts = len([a for a in alerts if not a.get("acknowledged", False)])
            
            # Average scores
            avg_risk_score = sum(s.get("risk_score", 0) for s in student_sessions) / total_students if total_students > 0 else 0
            avg_security_score = sum(s.get("security_score", 100) for s in student_sessions) / total_students if total_students > 0 else 0
            
            return {
                "total_students": total_students,
                "active_students": active_students,
                "paused_students": paused_students,
                "risk_distribution": {
                    "high": high_risk,
                    "medium": medium_risk,
                    "low": low_risk
                },
                "alert_statistics": {
                    "total_alerts": total_alerts,
                    "high_severity_alerts": high_severity_alerts,
                    "unacknowledged_alerts": unacknowledged_alerts
                },
                "average_scores": {
                    "risk_score": round(avg_risk_score, 2),
                    "security_score": round(avg_security_score, 2)
                }
            }
            
        except Exception as e:
            return {
                "total_students": 0,
                "active_students": 0,
                "paused_students": 0,
                "error": str(e)
            }
    
    async def _get_student_proctoring_events(self, examination_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Get proctoring events for student."""
        try:
            # Get proctoring session
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            
            if proctoring_session_id:
                proctoring_service = ProctoringService(self.db)
                session = await proctoring_service._get_proctoring_session(proctoring_session_id)
                if session:
                    return session.get("security_events", [])
            
            return []
            
        except Exception as e:
            return []
    
    async def _get_student_webcam_snapshots(self, examination_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Get webcam snapshots for student."""
        try:
            # Get webcam session
            webcam_session_key = f"webcam_student:{examination_id}:{student_id}"
            webcam_session_id = await self.cache.get(webcam_session_key)
            
            if webcam_session_id:
                webcam_service = WebcamProctoringService(self.db)
                session = await webcam_service._get_webcam_session(webcam_session_id)
                if session:
                    return session.get("snapshots", [])
            
            return []
            
        except Exception as e:
            return []
    
    async def _get_student_security_events(self, student_id: str) -> List[Dict[str, Any]]:
        """Get security events for student."""
        try:
            # Query security events for student
            result = await self.db.execute(
                select(SecurityEvent)
                .where(SecurityEvent.user_id == student_id)
                .order_by(SecurityEvent.created_at.desc())
                .limit(20)
            )
            events = result.scalars().all()
            
            return [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "details": event.details,
                    "severity": event.severity,
                    "created_at": event.created_at
                }
                for event in events
            ]
            
        except Exception as e:
            return []
    
    async def _calculate_student_risk_assessment(self, session_data: Dict[str, Any], 
                                                proctoring_events: List[Dict[str, Any]], 
                                                security_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive risk assessment for student."""
        try:
            risk_factors = []
            risk_score = session_data.get("risk_score", 0)
            
            # Analyze proctoring events
            focus_loss_events = len([e for e in proctoring_events if e.get("event_type") == "FOCUS_LOSS"])
            if focus_loss_events > 3:
                risk_factors.append({
                    "type": "excessive_focus_loss",
                    "severity": "medium",
                    "count": focus_loss_events
                })
            
            # Analyze security events
            high_severity_events = len([e for e in security_events if e.get("severity") == "high"])
            if high_severity_events > 0:
                risk_factors.append({
                    "type": "high_severity_violations",
                    "severity": "high",
                    "count": high_severity_events
                })
            
            # Determine overall risk level
            if risk_score > 80:
                risk_level = "critical"
            elif risk_score > 60:
                risk_level = "high"
            elif risk_score > 40:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "requires_intervention": risk_level in ["high", "critical"],
                "assessment_timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "error": str(e)
            }
    
    async def _get_available_actions(self, examination_id: str, student_id: str, invigilator_id: str) -> List[str]:
        """Get available actions for a student."""
        try:
            # Get student session status
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            proctoring_session_id = await self.cache.get(student_session_key)
            
            if proctoring_session_id:
                proctoring_service = ProctoringService(self.db)
                session = await proctoring_service._get_proctoring_session(proctoring_session_id)
                if session:
                    status = session.get("status", "active")
                    
                    if status == "active":
                        return ["message", "pause", "terminate"]
                    elif status == "paused":
                        return ["message", "resume", "terminate"]
            
            return []
            
        except Exception as e:
            return []
    
    def _calculate_time_remaining(self, instance: ExamInstance) -> Dict[str, Any]:
        """Calculate time remaining for exam instance."""
        try:
            if instance.end_time:
                remaining = instance.end_time - datetime.utcnow()
                if remaining.total_seconds() > 0:
                    return {
                        "minutes": int(remaining.total_seconds() / 60),
                        "seconds": remaining.total_seconds() % 60,
                        "expired": False
                    }
                else:
                    return {
                        "minutes": 0,
                        "seconds": 0,
                        "expired": True
                    }
            else:
                return {
                    "minutes": 0,
                    "seconds": 0,
                    "expired": False
                }
        except Exception:
            return {"minutes": 0, "seconds": 0, "expired": False}
    
    async def _log_invigilator_action(self, invigilator_id: str, examination_id: str, 
                                    student_id: str, action: str, details: Dict[str, Any]):
        """Log invigilator action."""
        try:
            # Create audit log entry
            audit_data = {
                "invigilator_id": invigilator_id,
                "examination_id": examination_id,
                "student_id": student_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            
            # Store in cache for audit trail
            audit_cache_key = f"invigilator_audit:{examination_id}"
            existing_audits = await self.cache.get(audit_cache_key) or []
            existing_audits.append(audit_data)
            await self.cache.set(audit_cache_key, existing_audits, ttl=86400 * 7)  # 7 days
            
        except Exception as e:
            # Log error but don't fail the action
            pass
