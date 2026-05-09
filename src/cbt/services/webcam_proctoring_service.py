"""
Webcam proctoring service with AI-assisted anomaly detection.
"""

import uuid
import base64
import asyncio
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from ..models.exam import Examination, ExamInstance, ExamInstanceStatus
from ..models.student import Student
from ..models.security import SecurityEvent
from ..services.audit_service import AuditService, AuditAction
from ..core.redis import cache_manager
from ..core.security import security


class WebcamProctoringService:
    """Webcam proctoring service with AI anomaly detection."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.security = security
    
    async def start_webcam_session(self, examination_id: str, student_id: str, 
                                  device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start webcam proctoring session for a student.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            device_info: Webcam and device information
            
        Returns:
            Webcam session data
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
            
            # Generate webcam session ID
            session_id = str(uuid.uuid4())
            
            # Create webcam session
            webcam_session = {
                "session_id": session_id,
                "examination_id": examination_id,
                "student_id": student_id,
                "instance_id": instance.id,
                "device_info": device_info,
                "started_at": datetime.utcnow(),
                "status": "active",
                "capture_count": 0,
                "anomaly_count": 0,
                "face_detection_failures": 0,
                "multiple_face_detections": 0,
                "no_face_detections": 0,
                "phone_detections": 0,
                "gaze_deviations": 0,
                "last_capture": None,
                "next_capture_time": self._calculate_next_capture_time(),
                "verification_confidence": 0.0,
                "snapshots": [],
                "anomalies": []
            }
            
            # Store session
            cache_key = f"webcam_session:{session_id}"
            await self.cache.set(cache_key, webcam_session, ttl=7200)  # 2 hours
            
            # Also store by student-exam for quick lookup
            student_session_key = f"webcam_student:{examination_id}:{student_id}"
            await self.cache.set(student_session_key, session_id, ttl=7200)
            
            # Log session start
            await self._log_security_event(
                student_id=student_id,
                event_type="WEBCAM_SESSION_START",
                details={
                    "examination_id": examination_id,
                    "session_id": session_id,
                    "device_info": device_info
                }
            )
            
            return webcam_session
            
        except Exception as e:
            raise ValueError(f"Failed to start webcam session: {str(e)}")
    
    async def capture_snapshot(self, session_id: str, image_data: str, 
                             timestamp: datetime) -> Dict[str, Any]:
        """
        Capture and analyze webcam snapshot.
        
        Args:
            session_id: Webcam session ID
            image_data: Base64 encoded image data
            timestamp: Capture timestamp
            
        Returns:
            Analysis results
        """
        try:
            session = await self._get_webcam_session(session_id)
            if not session:
                raise ValueError("Webcam session not found")
            
            # Check if it's time for capture
            current_time = datetime.utcnow()
            if current_time < session.get("next_capture_time", current_time):
                return {"message": "Too early for capture", "next_capture": session["next_capture_time"]}
            
            # Decode image
            try:
                image_bytes = base64.b64decode(image_data.split(',')[1])  # Remove data:image/jpeg;base64, prefix
            except Exception:
                raise ValueError("Invalid image data format")
            
            # Analyze image
            analysis_result = await self._analyze_snapshot(image_bytes, session)
            
            # Store snapshot
            snapshot_data = {
                "timestamp": timestamp,
                "analysis": analysis_result,
                "image_size": len(image_bytes),
                "capture_number": session["capture_count"] + 1
            }
            
            session["snapshots"].append(snapshot_data)
            session["capture_count"] += 1
            session["last_capture"] = timestamp
            session["next_capture_time"] = self._calculate_next_capture_time()
            
            # Update anomaly counts
            if analysis_result.get("anomalies"):
                session["anomaly_count"] += len(analysis_result["anomalies"])
                session["anomalies"].extend([
                    {
                        "timestamp": timestamp,
                        "anomalies": analysis_result["anomalies"],
                        "confidence": analysis_result.get("overall_confidence", 0.0)
                    }
                ])
            
            # Update specific counts
            if analysis_result.get("face_detected"):
                if analysis_result.get("face_count", 0) == 0:
                    session["no_face_detections"] += 1
                elif analysis_result.get("face_count", 0) > 1:
                    session["multiple_face_detections"] += 1
            else:
                session["face_detection_failures"] += 1
            
            if analysis_result.get("phone_detected"):
                session["phone_detections"] += 1
            
            if analysis_result.get("gaze_deviation"):
                session["gaze_deviations"] += 1
            
            # Update session
            await self._update_webcam_session(session_id, session)
            
            # Check for alerts
            alerts = await self._check_for_alerts(session, analysis_result)
            
            # Log significant events
            if analysis_result.get("anomalies"):
                await self._log_security_event(
                    student_id=session["student_id"],
                    event_type="WEBCAM_ANOMALY_DETECTED",
                    details={
                        "session_id": session_id,
                        "anomalies": analysis_result["anomalies"],
                        "confidence": analysis_result.get("overall_confidence", 0.0)
                    }
                )
            
            return {
                "capture_number": session["capture_count"],
                "analysis": analysis_result,
                "alerts": alerts,
                "next_capture_time": session["next_capture_time"]
            }
            
        except Exception as e:
            raise ValueError(f"Failed to capture snapshot: {str(e)}")
    
    async def verify_identity(self, session_id: str, image_data: str, 
                           reference_photo_data: str) -> Dict[str, Any]:
        """
        Verify student identity using facial recognition.
        
        Args:
            session_id: Webcam session ID
            image_data: Current image data
            reference_photo_data: Reference photo data
            
        Returns:
            Verification result
        """
        try:
            session = await self._get_webcam_session(session_id)
            if not session:
                raise ValueError("Webcam session not found")
            
            # Decode images
            try:
                current_image = base64.b64decode(image_data.split(',')[1])
                reference_image = base64.b64decode(reference_photo_data.split(',')[1])
            except Exception:
                raise ValueError("Invalid image data format")
            
            # Perform facial recognition
            verification_result = await self._perform_facial_recognition(
                current_image, reference_image
            )
            
            # Update verification confidence
            session["verification_confidence"] = verification_result.get("confidence", 0.0)
            
            # Store verification result
            verification_data = {
                "timestamp": datetime.utcnow(),
                "confidence": verification_result.get("confidence", 0.0),
                "verified": verification_result.get("verified", False),
                "requires_manual_review": verification_result.get("confidence", 0.0) < 0.8
            }
            
            session.setdefault("identity_verifications", []).append(verification_data)
            await self._update_webcam_session(session_id, session)
            
            # Log verification
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="IDENTITY_VERIFICATION",
                details={
                    "session_id": session_id,
                    "confidence": verification_result.get("confidence", 0.0),
                    "verified": verification_result.get("verified", False),
                    "requires_manual_review": verification_data["requires_manual_review"]
                }
            )
            
            return verification_result
            
        except Exception as e:
            raise ValueError(f"Failed to verify identity: {str(e)}")
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get webcam session summary.
        
        Args:
            session_id: Webcam session ID
            
        Returns:
            Session summary
        """
        try:
            session = await self._get_webcam_session(session_id)
            if not session:
                raise ValueError("Webcam session not found")
            
            # Calculate statistics
            duration = (datetime.utcnow() - session["started_at"]).total_seconds()
            capture_rate = session["capture_count"] / (duration / 60) if duration > 0 else 0  # captures per minute
            
            # Analyze anomalies
            anomaly_types = {}
            for anomaly_event in session.get("anomalies", []):
                for anomaly in anomaly_event.get("anomalies", []):
                    anomaly_type = anomaly.get("type", "unknown")
                    anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1
            
            summary = {
                "session_id": session_id,
                "student_id": session["student_id"],
                "duration_minutes": duration / 60,
                "total_captures": session["capture_count"],
                "capture_rate_per_minute": capture_rate,
                "anomaly_count": session["anomaly_count"],
                "anomaly_types": anomaly_types,
                "face_detection_failures": session["face_detection_failures"],
                "multiple_face_detections": session["multiple_face_detections"],
                "no_face_detections": session["no_face_detections"],
                "phone_detections": session["phone_detections"],
                "gaze_deviations": session["gaze_deviations"],
                "verification_confidence": session["verification_confidence"],
                "identity_verifications": len(session.get("identity_verifications", [])),
                "risk_score": self._calculate_risk_score(session),
                "requires_review": self._requires_manual_review(session)
            }
            
            return summary
            
        except Exception as e:
            raise ValueError(f"Failed to get session summary: {str(e)}")
    
    async def end_webcam_session(self, session_id: str, reason: str = "exam_completed") -> Dict[str, Any]:
        """
        End webcam proctoring session.
        
        Args:
            session_id: Webcam session ID
            reason: Reason for ending session
            
        Returns:
            Final session summary
        """
        try:
            session = await self._get_webcam_session(session_id)
            if not session:
                raise ValueError("Webcam session not found")
            
            # Get final summary
            summary = await self.get_session_summary(session_id)
            
            # Update session status
            session["status"] = "ended"
            session["ended_at"] = datetime.utcnow()
            session["end_reason"] = reason
            session["final_summary"] = summary
            
            # Remove from active sessions
            student_session_key = f"webcam_student:{session['examination_id']}:{session['student_id']}"
            await self.cache.delete(student_session_key)
            
            # Keep final session data for audit
            final_session_key = f"webcam_final:{session_id}"
            await self.cache.set(final_session_key, session, ttl=86400 * 30)  # 30 days
            
            # Delete active session
            cache_key = f"webcam_session:{session_id}"
            await self.cache.delete(cache_key)
            
            # Log session end
            await self._log_security_event(
                student_id=session["student_id"],
                event_type="WEBCAM_SESSION_END",
                details={
                    "reason": reason,
                    "total_captures": session["capture_count"],
                    "anomaly_count": session["anomaly_count"],
                    "risk_score": summary["risk_score"]
                }
            )
            
            return summary
            
        except Exception as e:
            raise ValueError(f"Failed to end webcam session: {str(e)}")
    
    # Private helper methods
    
    async def _get_webcam_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get webcam session by ID."""
        cache_key = f"webcam_session:{session_id}"
        return await self.cache.get(cache_key)
    
    async def _update_webcam_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update webcam session data."""
        cache_key = f"webcam_session:{session_id}"
        await self.cache.set(cache_key, session_data, ttl=7200)
    
    def _calculate_next_capture_time(self) -> datetime:
        """Calculate next capture time (random interval between 3-7 minutes)."""
        import random
        interval_minutes = random.randint(3, 7)
        return datetime.utcnow() + timedelta(minutes=interval_minutes)
    
    async def _analyze_snapshot(self, image_bytes: bytes, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze webcam snapshot for anomalies.
        
        This is a simplified implementation. In production, this would use
        actual computer vision models (OpenCV, TensorFlow, etc.).
        """
        try:
            # Simulate analysis results
            # In production, this would use real AI models
            
            analysis = {
                "face_detected": True,
                "face_count": 1,
                "face_confidence": 0.95,
                "face_location": {"x": 320, "y": 240, "width": 100, "height": 120},
                "multiple_faces": False,
                "no_face": False,
                "phone_detected": False,
                "phone_confidence": 0.0,
                "phone_location": None,
                "gaze_deviation": False,
                "gaze_angle": 0.0,
                "gaze_confidence": 0.0,
                "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "lighting_condition": "good",
                "image_quality": "high",
                "anomalies": [],
                "overall_confidence": 0.95
            }
            
            # Simulate random anomalies for demonstration
            import random
            anomaly_chance = random.random()
            
            if anomaly_chance < 0.05:  # 5% chance of anomaly
                anomaly_types = [
                    {"type": "multiple_faces", "confidence": 0.8, "description": "Multiple faces detected"},
                    {"type": "no_face", "confidence": 0.9, "description": "No face detected"},
                    {"type": "phone_detected", "confidence": 0.7, "description": "Phone or device detected"},
                    {"type": "gaze_deviation", "confidence": 0.6, "description": "Gaze deviation from screen"},
                    {"type": "poor_lighting", "confidence": 0.5, "description": "Poor lighting conditions"}
                ]
                
                selected_anomaly = random.choice(anomaly_types)
                analysis["anomalies"] = [selected_anomaly]
                analysis["overall_confidence"] = 1.0 - selected_anomaly["confidence"]
                
                # Update analysis based on anomaly type
                if selected_anomaly["type"] == "multiple_faces":
                    analysis["multiple_faces"] = True
                    analysis["face_count"] = 2
                elif selected_anomaly["type"] == "no_face":
                    analysis["face_detected"] = False
                    analysis["no_face"] = True
                    analysis["face_count"] = 0
                elif selected_anomaly["type"] == "phone_detected":
                    analysis["phone_detected"] = True
                    analysis["phone_confidence"] = selected_anomaly["confidence"]
                elif selected_anomaly["type"] == "gaze_deviation":
                    analysis["gaze_deviation"] = True
                    analysis["gaze_angle"] = random.uniform(-30, 30)
                elif selected_anomaly["type"] == "poor_lighting":
                    analysis["lighting_condition"] = "poor"
            
            return analysis
            
        except Exception as e:
            # Return safe default if analysis fails
            return {
                "face_detected": False,
                "face_count": 0,
                "face_confidence": 0.0,
                "anomalies": [{"type": "analysis_error", "confidence": 1.0, "description": "Analysis failed"}],
                "overall_confidence": 0.0
            }
    
    async def _perform_facial_recognition(self, current_image: bytes, 
                                        reference_image: bytes) -> Dict[str, Any]:
        """
        Perform facial recognition between current and reference images.
        
        This is a simplified implementation. In production, this would use
        actual facial recognition models (FaceNet, ArcFace, etc.).
        """
        try:
            # Simulate facial recognition
            # In production, this would use real facial recognition models
            
            # For demonstration, return a high confidence match
            confidence = 0.92  # Simulated high confidence
            verified = confidence > 0.8
            
            return {
                "verified": verified,
                "confidence": confidence,
                "match_score": confidence,
                "requires_manual_review": not verified,
                "facial_landmarks": {
                    "left_eye": [150, 120],
                    "right_eye": [250, 120],
                    "nose": [200, 160],
                    "mouth": [200, 200]
                },
                "embedding_similarity": confidence
            }
            
        except Exception as e:
            return {
                "verified": False,
                "confidence": 0.0,
                "error": str(e),
                "requires_manual_review": True
            }
    
    async def _check_for_alerts(self, session: Dict[str, Any], 
                             analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if analysis results should trigger alerts."""
        alerts = []
        
        # Check for high-confidence anomalies
        for anomaly in analysis.get("anomalies", []):
            if anomaly.get("confidence", 0.0) > 0.7:
                alert = {
                    "type": "high_confidence_anomaly",
                    "severity": "high" if anomaly["confidence"] > 0.8 else "medium",
                    "anomaly": anomaly,
                    "timestamp": datetime.utcnow(),
                    "session_id": session["session_id"],
                    "student_id": session["student_id"]
                }
                alerts.append(alert)
        
        # Check for consecutive issues
        if session.get("face_detection_failures", 0) >= 3:
            alerts.append({
                "type": "consecutive_face_detection_failures",
                "severity": "high",
                "count": session["face_detection_failures"],
                "timestamp": datetime.utcnow(),
                "session_id": session["session_id"],
                "student_id": session["student_id"]
            })
        
        if session.get("multiple_face_detections", 0) >= 2:
            alerts.append({
                "type": "multiple_face_detections",
                "severity": "high",
                "count": session["multiple_face_detections"],
                "timestamp": datetime.utcnow(),
                "session_id": session["session_id"],
                "student_id": session["student_id"]
            })
        
        # Store alerts in cache for invigilator dashboard
        if alerts:
            alert_cache_key = f"webcam_alerts:{session['examination_id']}"
            existing_alerts = await self.cache.get(alert_cache_key) or []
            existing_alerts.extend(alerts)
            await self.cache.set(alert_cache_key, existing_alerts, ttl=7200)
        
        return alerts
    
    def _calculate_risk_score(self, session: Dict[str, Any]) -> float:
        """Calculate overall risk score for the session."""
        try:
            # Base score starts at 0
            risk_score = 0.0
            
            # Add points for various anomalies
            risk_score += session.get("face_detection_failures", 0) * 10
            risk_score += session.get("multiple_face_detections", 0) * 25
            risk_score += session.get("no_face_detections", 0) * 15
            risk_score += session.get("phone_detections", 0) * 30
            risk_score += session.get("gaze_deviations", 0) * 5
            
            # Consider verification confidence
            verification_confidence = session.get("verification_confidence", 1.0)
            if verification_confidence < 0.8:
                risk_score += (0.8 - verification_confidence) * 20
            
            # Cap at 100
            risk_score = min(risk_score, 100.0)
            
            return risk_score
            
        except Exception:
            return 0.0
    
    def _requires_manual_review(self, session: Dict[str, Any]) -> bool:
        """Determine if session requires manual review."""
        risk_score = self._calculate_risk_score(session)
        
        # Require review for high risk score or specific conditions
        high_risk = risk_score > 50
        low_verification = session.get("verification_confidence", 1.0) < 0.7
        multiple_faces = session.get("multiple_face_detections", 0) > 0
        phone_detected = session.get("phone_detections", 0) > 0
        
        return high_risk or low_verification or multiple_faces or phone_detected
    
    async def _log_security_event(self, student_id: str, event_type: str, 
                                details: Dict[str, Any]):
        """Log security event."""
        if self.db:
            security_event = SecurityEvent(
                id=str(uuid.uuid4()),
                user_id=student_id,
                event_type=event_type,
                details=details,
                severity="medium",
                created_at=datetime.utcnow()
            )
            
            self.db.add(security_event)
            await self.db.commit()
    
    async def get_active_sessions(self, examination_id: str) -> List[Dict[str, Any]]:
        """Get all active webcam sessions for an examination."""
        try:
            # This would typically query a database or use Redis patterns
            # For now, return empty list
            return []
        except Exception as e:
            raise ValueError(f"Failed to get active sessions: {str(e)}")
    
    async def get_alerts(self, examination_id: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get webcam proctoring alerts for an examination."""
        try:
            alert_cache_key = f"webcam_alerts:{examination_id}"
            alerts = await self.cache.get(alert_cache_key) or []
            
            if severity:
                alerts = [alert for alert in alerts if alert.get("severity") == severity]
            
            return alerts
        except Exception as e:
            raise ValueError(f"Failed to get alerts: {str(e)}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a webcam proctoring alert."""
        try:
            # This would typically update the alert in database
            # For now, just return success
            return True
        except Exception as e:
            raise ValueError(f"Failed to acknowledge alert: {str(e)}")
