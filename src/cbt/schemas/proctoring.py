"""
Proctoring system schemas for browser lockdown and monitoring.
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProctoringSessionStart(BaseModel):
    """Proctoring session start request."""
    examination_id: str
    student_id: str
    device_fingerprint: str
    ip_address: str
    browser_info: Optional[Dict[str, Any]] = None


class ProctoringSessionResponse(BaseModel):
    """Proctoring session response."""
    session_id: str
    examination_id: str
    student_id: str
    instance_id: str
    device_fingerprint: str
    ip_address: str
    started_at: datetime
    status: str
    focus_loss_count: int
    fullscreen_exits: int
    clipboard_events: int
    keyboard_violations: int
    security_events: List[Dict[str, Any]]
    last_heartbeat: datetime
    watermark_visible: bool
    
    class Config:
        from_attributes = True


class FocusLossEvent(BaseModel):
    """Focus loss event data."""
    duration: float
    reason: str  # "tab_switch", "window_minimize", "notification", "other"
    
    @validator('duration')
    def validate_duration(cls, v):
        if v < 0 or v > 300:  # Max 5 minutes
            raise ValueError('Duration must be between 0 and 300 seconds')
        return v


class FullscreenExitEvent(BaseModel):
    """Fullscreen exit event data."""
    reason: str  # "escape_key", "user_exit", "system_notification", "other"


class KeyboardViolationEvent(BaseModel):
    """Keyboard violation event data."""
    key_combination: str
    action: str  # "copy", "paste", "cut", "print", "save", "screenshot"
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["copy", "paste", "cut", "print", "save", "screenshot"]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {allowed_actions}')
        return v


class ClipboardEvent(BaseModel):
    """Clipboard event data."""
    event_type: str  # "copy", "paste", "cut"
    data_length: int
    
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ["copy", "paste", "cut"]
        if v not in allowed_types:
            raise ValueError(f'Event type must be one of: {allowed_types}')
        return v


class HeartbeatUpdate(BaseModel):
    """Heartbeat update data."""
    status_data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class ProctoringSummary(BaseModel):
    """Proctoring summary for examination."""
    examination_id: str
    total_active_sessions: int
    security_events: Dict[str, int]
    escalated_students: List[str]
    connection_issues: int
    average_session_duration: float
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ScreenRecordingDetection(BaseModel):
    """Screen recording detection result."""
    risk_level: str  # "none", "low", "medium", "high"
    risk_score: int
    indicators: List[str]
    detection_time: datetime
    
    class Config:
        from_attributes = True


class BrowserInfo(BaseModel):
    """Browser and system information."""
    user_agent: str
    screen_resolution: str
    color_depth: int
    timezone: str
    language: str
    platform: str
    cookie_enabled: bool
    do_not_track: Optional[bool] = None
    plugins: List[str]
    extensions: List[str]
    running_processes: List[str]
    display_count: int
    touch_support: bool
    webgl_supported: bool
    canvas_fingerprint: Optional[str] = None


class ProctoringEvent(BaseModel):
    """Generic proctoring event."""
    event_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    severity: str  # "low", "medium", "high", "critical"
    details: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProctoringAlert(BaseModel):
    """Proctoring alert for invigilator."""
    alert_id: str
    session_id: str
    student_id: str
    student_name: str
    examination_id: str
    alert_type: str
    severity: str
    message: str
    requires_action: bool
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InvigilatorAction(BaseModel):
    """Invigilator intervention action."""
    action_type: str  # "message", "pause", "terminate", "warn"
    target_session_id: str
    message: Optional[str] = None
    reason: Optional[str] = None
    
    @validator('action_type')
    def validate_action_type(cls, v):
        allowed_actions = ["message", "pause", "terminate", "warn"]
        if v not in allowed_actions:
            raise ValueError(f'Action type must be one of: {allowed_actions}')
        return v


class ProctoringConfiguration(BaseModel):
    """Proctoring configuration for examination."""
    examination_id: str
    require_fullscreen: bool = True
    require_webcam: bool = True
    require_microphone: bool = False
    allow_focus_loss: bool = False
    max_focus_loss_events: int = 3
    allow_keyboard_shortcuts: bool = False
    block_clipboard: bool = True
    watermark_enabled: bool = True
    screenshot_detection: bool = True
    ai_monitoring_enabled: bool = True
    escalation_threshold: int = 5
    auto_escalation: bool = True
    
    class Config:
        from_attributes = True


class ProctoringStatistics(BaseModel):
    """Proctoring statistics."""
    examination_id: str
    total_students: int
    active_sessions: int
    completed_sessions: int
    terminated_sessions: int
    average_duration: float
    total_events: int
    events_by_type: Dict[str, int]
    escalated_students: int
    alerts_resolved: int
    alerts_pending: int
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ProctoringReport(BaseModel):
    """Detailed proctoring report."""
    examination_id: str
    examination_title: str
    report_period: Dict[str, datetime]
    summary_statistics: ProctoringStatistics
    security_incidents: List[ProctoringEvent]
    escalated_cases: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    generated_by: str
    
    class Config:
        from_attributes = True


class ProctoringSessionStatus(BaseModel):
    """Current status of proctoring session."""
    session_id: str
    student_id: str
    student_name: str
    examination_id: str
    status: str  # "active", "paused", "terminated", "completed"
    duration: int  # seconds
    focus_loss_count: int
    fullscreen_exits: int
    security_score: int  # 0-100
    last_activity: datetime
    current_question: Optional[int] = None
    connection_status: str  # "connected", "disconnected", "reconnecting"
    
    class Config:
        from_attributes = True


class ProctoringDashboard(BaseModel):
    """Invigilator dashboard data."""
    examination_id: str
    active_sessions: List[ProctoringSessionStatus]
    alerts: List[ProctoringAlert]
    statistics: ProctoringStatistics
    system_status: Dict[str, Any]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class BiometricVerificationResult(BaseModel):
    """Biometric verification result for proctoring."""
    session_id: str
    verification_type: str  # "initial", "periodic"
    success: bool
    confidence_score: float
    timestamp: datetime
    verification_data: Dict[str, Any]
    requires_manual_review: bool = False
    
    class Config:
        from_attributes = True


class AudioMonitoringEvent(BaseModel):
    """Audio monitoring event."""
    session_id: str
    event_type: str  # "noise_spike", "conversation_detected", "keyword_detected"
    confidence: float
    audio_level: float
    duration: float
    timestamp: datetime
    flagged_words: List[str] = []
    
    class Config:
        from_attributes = True


class ProctoringIntervention(BaseModel):
    """Record of invigilator intervention."""
    intervention_id: str
    session_id: str
    student_id: str
    invigilator_id: str
    intervention_type: str
    reason: str
    message: Optional[str] = None
    timestamp: datetime
    resolved: bool = False
    resolution: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProctoringSessionEnd(BaseModel):
    """Proctoring session end data."""
    session_id: str
    end_reason: str
    duration_seconds: int
    focus_loss_count: int
    fullscreen_exits: int
    keyboard_violations: int
    clipboard_events: int
    total_security_events: int
    security_score: int
    escalated: bool
    terminated_by_invigilator: bool
    ended_at: datetime
    
    class Config:
        from_attributes = True
