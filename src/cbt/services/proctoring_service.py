"""
Proctoring service for browser lockdown, environment control, and monitoring.
"""

import uuid
import time
import asyncio
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from ..models.exam import Examination, ExamInstance, ExamInstanceStatus
from ..models.student import Student
from ..models.security import SecurityEvent, UserSession
from ..services.audit_service import AuditService, AuditAction
from ..core.redis import cache_manager
from ..core.security import security


class ProctoringService:
    """Proctoring service for exam monitoring and security enforcement."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.security = security
        self.backend = default_backend()
    
    async def start_proctoring_session(self, examination_id: str, student_id: str, 
                                     device_fingerprint: str, ip_address: str) -> Dict[str, Any]:
        """
        Start a proctoring session for a student.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            device_fingerprint: Browser/device fingerprint
            ip_address: Student's IP address
            
        Returns:
            Proctoring session data
        """
        try:
            # Get exam instance
            instance = await ExamInstance.find_one(
                ExamInstance.examination_id == examination_id,
                ExamInstance.student_id == student_id,
                ExamInstance.status == ExamInstanceStatus.IN_PROGRESS,
            )
            if not instance:
                raise ValueError("Active exam instance not found")
            
            # Generate proctoring session ID
            session_id = str(uuid.uuid4())
            
            # Create proctoring session
            proctoring_session = {
                "session_id": session_id,
                "examination_id": examination_id,
                "student_id": student_id,
                "instance_id": instance.id,
                "device_fingerprint": device_fingerprint,
                "ip_address": ip_address,
                "started_at": datetime.utcnow(),
                "status": "active",
                "focus_loss_count": 0,
                "fullscreen_exits": 0,
                "clipboard_events": 0,
                "keyboard_violations": 0,
                "security_events": [],
                "last_heartbeat": datetime.utcnow(),
                "watermark_visible": True
            }
            
            # Store session
            cache_key = f"proctoring_session:{session_id}"
            await self.cache.set(cache_key, proctoring_session, ttl=7200)  # 2 hours
            
            # Also store by student-exam for quick lookup
            student_session_key = f"proctoring_student:{examination_id}:{student_id}"
            await self.cache.set(student_session_key, session_id, ttl=7200)
            
            # Log session start
            await self._log_security_event(
                student_id=student_id,
                event_type="PROCTORING_SESSION_START",
                details={
                    "examination_id": examination_id,
                    "session_id": session_id,
                    "ip_address": ip_address,
                    "device_fingerprint": device_fingerprint[:16] + "..."
                }
            )
            
            return proctoring_session
            
        except Exception as e:
            raise ValueError(f"Failed to start proctoring session: {str(e)}")
    
    async def record_focus_loss(self, session_id: str, duration: float, reason: str) -> Dict[str, Any]:
        """
        Record a focus loss event.
        
        Args:
            session_id: Proctoring session ID
            duration: Duration of focus loss in seconds
            reason: Reason for focus loss
            
        Returns:
            Updated session data
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                raise ValueError("Proctoring session not found")
            
            # Record focus loss event
            focus_event = {
                "timestamp": datetime.utcnow(),
                "duration": duration,
                "reason": reason,
                "event_type": "FOCUS_LOSS"
            }
            
            session["security_events"].append(focus_event)
            session["focus_loss_count"] += 1
            session["last_heartbeat"] = datetime.utcnow()
            
            # Check for escalation
            escalation_level = self._calculate_focus_loss_escalation(session["focus_loss_count"])
            
            # Update session
            await self._update_proctoring_session(session_id, session)
            
            # Log security event
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="FOCUS_LOSS",
                details={
                    "duration": duration,
                    "reason": reason,
                    "focus_loss_count": session["focus_loss_count"],
                    "escalation_level": escalation_level
                }
            )
            
            return {
                "focus_loss_count": session["focus_loss_count"],
                "escalation_level": escalation_level,
                "warning_threshold": 3,
                "escalation_threshold": 5
            }
            
        except Exception as e:
            raise ValueError(f"Failed to record focus loss: {str(e)}")
    
    async def record_fullscreen_exit(self, session_id: str, reason: str) -> Dict[str, Any]:
        """
        Record a fullscreen exit event.
        
        Args:
            session_id: Proctoring session ID
            reason: Reason for fullscreen exit
            
        Returns:
            Updated session data
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                raise ValueError("Proctoring session not found")
            
            # Record fullscreen exit event
            fullscreen_event = {
                "timestamp": datetime.utcnow(),
                "reason": reason,
                "event_type": "FULLSCREEN_EXIT"
            }
            
            session["security_events"].append(fullscreen_event)
            session["fullscreen_exits"] += 1
            session["last_heartbeat"] = datetime.utcnow()
            
            # Update session
            await self._update_proctoring_session(session_id, session)
            
            # Log security event
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="FULLSCREEN_EXIT",
                details={
                    "reason": reason,
                    "fullscreen_exits": session["fullscreen_exits"]
                }
            )
            
            return {
                "fullscreen_exits": session["fullscreen_exits"],
                "warning_message": "Please return to full-screen mode. This incident has been recorded."
            }
            
        except Exception as e:
            raise ValueError(f"Failed to record fullscreen exit: {str(e)}")
    
    async def record_keyboard_violation(self, session_id: str, key_combination: str, 
                                       action: str) -> Dict[str, Any]:
        """
        Record a keyboard violation (copy, paste, print, etc.).
        
        Args:
            session_id: Proctoring session ID
            key_combination: Key combination that was pressed
            action: Action attempted (copy, paste, print, etc.)
            
        Returns:
            Updated session data
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                raise ValueError("Proctoring session not found")
            
            # Record keyboard violation
            violation_event = {
                "timestamp": datetime.utcnow(),
                "key_combination": key_combination,
                "action": action,
                "event_type": "KEYBOARD_VIOLATION"
            }
            
            session["security_events"].append(violation_event)
            session["keyboard_violations"] += 1
            session["last_heartbeat"] = datetime.utcnow()
            
            # Update session
            await self._update_proctoring_session(session_id, session)
            
            # Log security event
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="KEYBOARD_VIOLATION",
                details={
                    "key_combination": key_combination,
                    "action": action,
                    "keyboard_violations": session["keyboard_violations"]
                }
            )
            
            return {
                "keyboard_violations": session["keyboard_violations"],
                "blocked": True,
                "message": f"The {action} action has been blocked and recorded."
            }
            
        except Exception as e:
            raise ValueError(f"Failed to record keyboard violation: {str(e)}")
    
    async def record_clipboard_event(self, session_id: str, event_type: str, 
                                    data_length: int) -> Dict[str, Any]:
        """
        Record a clipboard event.
        
        Args:
            session_id: Proctoring session ID
            event_type: Type of clipboard event (copy, paste, cut)
            data_length: Length of clipboard data
            
        Returns:
            Updated session data
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                raise ValueError("Proctoring session not found")
            
            # Record clipboard event
            clipboard_event = {
                "timestamp": datetime.utcnow(),
                "event_type": "CLIPBOARD_EVENT",
                "clipboard_action": event_type,
                "data_length": data_length
            }
            
            session["security_events"].append(clipboard_event)
            session["clipboard_events"] += 1
            session["last_heartbeat"] = datetime.utcnow()
            
            # Clear clipboard if paste attempt
            if event_type == "paste":
                await self._clear_student_clipboard(session_id)
            
            # Update session
            await self._update_proctoring_session(session_id, session)
            
            # Log security event
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="CLIPBOARD_EVENT",
                details={
                    "clipboard_action": event_type,
                    "data_length": data_length,
                    "clipboard_events": session["clipboard_events"]
                }
            )
            
            return {
                "clipboard_events": session["clipboard_events"],
                "action_blocked": event_type == "paste",
                "message": "Clipboard access has been logged and restricted."
            }
            
        except Exception as e:
            raise ValueError(f"Failed to record clipboard event: {str(e)}")
    
    async def update_heartbeat(self, session_id: str, status_data: Dict[str, Any]) -> bool:
        """
        Update session heartbeat with current status.
        
        Args:
            session_id: Proctoring session ID
            status_data: Current status data
            
        Returns:
            True if successful
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                return False
            
            # Update heartbeat and status
            session["last_heartbeat"] = datetime.utcnow()
            session["current_status"] = status_data
            
            # Check for connection issues
            last_heartbeat = session["last_heartbeat"]
            time_diff = (datetime.utcnow() - last_heartbeat).total_seconds()
            
            if time_diff > 60:  # More than 1 minute since last heartbeat
                session["connection_issues"] = session.get("connection_issues", 0) + 1
                await self._log_security_event(
                    student_id=session["student_id"],
                    event_type="CONNECTION_ISSUE",
                    details={"time_diff": time_diff}
                )
            
            # Update session
            await self._update_proctoring_session(session_id, session)
            
            return True
            
        except Exception as e:
            raise ValueError(f"Failed to update heartbeat: {str(e)}")
    
    async def get_proctoring_summary(self, examination_id: str) -> Dict[str, Any]:
        """
        Get proctoring summary for an examination.
        
        Args:
            examination_id: Examination ID
            
        Returns:
            Proctoring summary statistics
        """
        try:
            # Get all active sessions for this examination
            session_pattern = f"proctoring_session:*"
            all_sessions = []
            
            # This would be more efficient with Redis pattern matching
            # For now, we'll return a mock summary
            summary = {
                "examination_id": examination_id,
                "total_active_sessions": 0,
                "security_events": {
                    "focus_loss_events": 0,
                    "fullscreen_exits": 0,
                    "keyboard_violations": 0,
                    "clipboard_events": 0
                },
                "escalated_students": [],
                "connection_issues": 0,
                "average_session_duration": 0,
                "generated_at": datetime.utcnow()
            }
            
            return summary
            
        except Exception as e:
            raise ValueError(f"Failed to get proctoring summary: {str(e)}")
    
    async def end_proctoring_session(self, session_id: str, reason: str = "exam_completed") -> Dict[str, Any]:
        """
        End a proctoring session.
        
        Args:
            session_id: Proctoring session ID
            reason: Reason for ending session
            
        Returns:
            Final session summary
        """
        try:
            session = await self._get_proctoring_session(session_id)
            if not session:
                raise ValueError("Proctoring session not found")
            
            # Calculate session duration
            duration = (datetime.utcnow() - session["started_at"]).total_seconds()
            
            # Update session status
            session["status"] = "ended"
            session["ended_at"] = datetime.utcnow()
            session["end_reason"] = reason
            session["duration_seconds"] = duration
            
            # Remove from active sessions
            student_session_key = f"proctoring_student:{session['examination_id']}:{session['student_id']}"
            await self.cache.delete(student_session_key)
            
            # Keep final session data for audit
            final_session_key = f"proctoring_final:{session_id}"
            await self.cache.set(final_session_key, session, ttl=86400 * 30)  # 30 days
            
            # Delete active session
            cache_key = f"proctoring_session:{session_id}"
            await self.cache.delete(cache_key)
            
            # Log session end
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="PROCTORING_SESSION_END",
                details={
                    "reason": reason,
                    "duration_seconds": duration,
                    "focus_loss_count": session["focus_loss_count"],
                    "security_events_count": len(session["security_events"])
                }
            )
            
            return {
                "session_id": session_id,
                "duration_seconds": duration,
                "focus_loss_count": session["focus_loss_count"],
                "fullscreen_exits": session["fullscreen_exits"],
                "keyboard_violations": session["keyboard_violations"],
                "clipboard_events": session["clipboard_events"],
                "total_security_events": len(session["security_events"])
            }
            
        except Exception as e:
            raise ValueError(f"Failed to end proctoring session: {str(e)}")
    
    # Private helper methods
    
    async def _get_proctoring_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get proctoring session by ID."""
        cache_key = f"proctoring_session:{session_id}"
        return await self.cache.get(cache_key)
    
    async def _update_proctoring_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update proctoring session data."""
        cache_key = f"proctoring_session:{session_id}"
        await self.cache.set(cache_key, session_data, ttl=7200)
    
    def _calculate_focus_loss_escalation(self, focus_loss_count: int) -> str:
        """Calculate escalation level based on focus loss count."""
        if focus_loss_count >= 5:
            return "high"
        elif focus_loss_count >= 3:
            return "medium"
        elif focus_loss_count >= 1:
            return "low"
        else:
            return "none"
    
    async def _clear_student_clipboard(self, session_id: str):
        """Clear student clipboard (client-side action)."""
        # This would trigger a client-side clipboard clearing action
        # For now, we just log it
        cache_key = f"clipboard_clear:{session_id}"
        await self.cache.set(cache_key, datetime.utcnow(), ttl=60)
    
    async def _log_security_event(self, student_id: str, event_type: str, details: Dict[str, Any]):
        """Log security event."""
        try:
            desc = f"{event_type}: {json.dumps(details, default=str)[:4000]}"
            security_event = SecurityEvent(
                event_type=event_type,
                severity="MEDIUM",
                description=desc,
                user_id=student_id,
            )
            await security_event.insert()
        except Exception:
            logging.getLogger(__name__).exception("Failed to persist security event")
    
    async def generate_session_watermark(self, session_id: str, student_info: Dict[str, Any]) -> str:
        """
        Generate a unique watermark for the session.
        
        Args:
            session_id: Proctoring session ID
            student_info: Student information
            
        Returns:
            Watermark data (CSS/HTML)
        """
        try:
            # Generate unique watermark data
            watermark_data = f"{student_info['matric_number']}:{session_id}:{datetime.utcnow().timestamp()}"
            
            # Create CSS for invisible watermark
            watermark_css = f"""
            .exam-watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 1px;
                color: rgba(255, 255, 255, 0.01);
                pointer-events: none;
                z-index: -1;
                user-select: none;
            }}
            """
            
            # Create watermark element
            watermark_html = f'<div class="exam-watermark">{watermark_data}</div>'
            
            return {
                "css": watermark_css,
                "html": watermark_html,
                "data": watermark_data
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate watermark: {str(e)}")
    
    async def detect_screen_recording(self, session_id: str, browser_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to detect screen recording software.
        
        Args:
            session_id: Proctoring session ID
            browser_info: Browser and system information
            
        Returns:
            Detection result
        """
        try:
            detection_indicators = []
            risk_score = 0
            
            # Check for common recording software indicators
            suspicious_processes = browser_info.get("running_processes", [])
            recording_indicators = [
                "obs", "xsplit", "camtasia", "bandicam", "fraps", 
                "screenrecorder", "quicktime", "vlc", "ffmpeg"
            ]
            
            for process in suspicious_processes:
                if any(indicator in process.lower() for indicator in recording_indicators):
                    detection_indicators.append(f"Suspicious process: {process}")
                    risk_score += 20
            
            # Check browser extensions
            extensions = browser_info.get("extensions", [])
            recording_extensions = [
                "screen capture", "video recorder", "webcam recorder"
            ]
            
            for extension in extensions:
                if any(indicator in extension.lower() for indicator in recording_extensions):
                    detection_indicators.append(f"Suspicious extension: {extension}")
                    risk_score += 15
            
            # Check for multiple displays (could indicate recording setup)
            display_count = browser_info.get("display_count", 1)
            if display_count > 1:
                detection_indicators.append(f"Multiple displays: {display_count}")
                risk_score += 10
            
            # Determine risk level
            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "medium"
            elif risk_score > 0:
                risk_level = "low"
            else:
                risk_level = "none"
            
            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "indicators": detection_indicators,
                "detection_time": datetime.utcnow()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to detect screen recording: {str(e)}")
