"""
Database models for CBT system.
"""

from .base import BaseDocument
from .user import User, UserRoleAssignment
from .academic import AcademicSession, Semester, Department, Course, CourseDepartment, LecturerCourse
from .student import Student, StudentCourse
from .question import QuestionBank, Question, QuestionOption, QuestionAnswer
from .exam import Examination, ExamQuestion, ExamInstance, ExamAnswer
from .venue import Venue, ExamVenueAssignment
from .biometric import BiometricTemplate
from .security import (
    UserSession,
    AuditLog,
    SecurityEvent,
    SecurityScan,
    Vulnerability,
)

__all__ = [
    "BaseDocument",
    "User",
    "UserRoleAssignment",
    "AcademicSession",
    "Semester",
    "Department",
    "Course",
    "CourseDepartment",
    "LecturerCourse",
    "Student",
    "StudentCourse",
    "QuestionBank",
    "Question",
    "QuestionOption",
    "QuestionAnswer",
    "Examination",
    "ExamQuestion",
    "ExamInstance",
    "ExamAnswer",
    "Venue",
    "ExamVenueAssignment",
    "UserSession",
    "BiometricTemplate",
    "AuditLog",
    "SecurityEvent",
    "SecurityScan",
    "Vulnerability",
]
