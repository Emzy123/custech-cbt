"""
Question model using Beanie (MongoDB).
"""

from typing import Optional
from datetime import datetime, timezone
from beanie import Document
from pydantic import Field

from .base import BaseDocument
import enum


class QuestionType(str, enum.Enum):
    """Question types."""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"
    FILL_BLANK = "FILL_BLANK"
    MATCHING = "MATCHING"


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty levels."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class CognitiveLevel(str, enum.Enum):
    """Bloom's taxonomy cognitive levels."""
    REMEMBERING = "REMEMBERING"
    UNDERSTANDING = "UNDERSTANDING"
    APPLYING = "APPLYING"
    ANALYZING = "ANALYZING"
    EVALUATING = "EVALUATING"
    CREATING = "CREATING"


class QuestionStatus(str, enum.Enum):
    """Question lifecycle status."""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"



class Question(BaseDocument):
    """Individual question with content and flat options."""
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str  # "A", "B", "C", "D"
    course_code: str = "CSC131"
    created_by: str
    updated_by: Optional[str] = None

    class Settings:
        name = "questions"
