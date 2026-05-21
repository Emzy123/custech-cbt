"""
Database models for CBT system.
"""

from .base import BaseDocument
from .user import User
from .academic import AcademicSession, Semester, Department, Course, CourseDepartment, LecturerCourse
from .student import Student, StudentCourse
from .question import Question
from .exam import Examination, ExamInstance, Result
from .security import (
    UserSession,
    AuditLog,
)

__all__ = [
    "BaseDocument",
    "User",
    "AcademicSession",
    "Semester",
    "Department",
    "Course",
    "CourseDepartment",
    "LecturerCourse",
    "Student",
    "StudentCourse",
    "Question",
    "Examination",
    "ExamInstance",
    "Result",
    "UserSession",
    "AuditLog",
]
