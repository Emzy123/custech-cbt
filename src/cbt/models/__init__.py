"""
Database models for CBT system.
"""

from .base import BaseDocument
from .user import User, UserRoleAssignment
from .academic import AcademicSession, Semester, Department, Course, CourseDepartment
from .student import Student, StudentCourse
from .question import QuestionBank, Question, QuestionOption, QuestionAnswer
from .exam import Examination, ExamQuestion, ExamInstance, ExamAnswer
from .security import UserSession, BiometricTemplate, AuditLog, SecurityEvent

__all__ = [
    "BaseDocument",
    "User",
    "UserRoleAssignment",
    "AcademicSession",
    "Semester", 
    "Department",
    "Course",
    "CourseDepartment",
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
    "UserSession",
    "BiometricTemplate",
    "AuditLog",
    "SecurityEvent",
]
