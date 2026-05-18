"""
Question bank and question models using Beanie (MongoDB).
"""

from typing import Optional, List
import enum
from datetime import datetime
from beanie import Document
from pydantic import Field

from .base import BaseDocument


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


class QuestionBank(BaseDocument):
    """Container for organizing questions."""
    title: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    course_id: Optional[str] = None
    level: Optional[int] = None
    is_public: bool = False
    created_by: str

    class Settings:
        name = "question_banks"


class Question(BaseDocument):
    """Individual question with content and metadata."""
    question_text: str
    question_type: QuestionType
    difficulty: QuestionDifficulty
    points_value: int
    time_limit_seconds: Optional[int] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    version: int = 1
    question_bank_id: Optional[str] = None
    course_id: str
    topic: str
    cognitive_level: CognitiveLevel
    status: QuestionStatus = QuestionStatus.DRAFT
    created_by: str
    updated_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    supersedes_question_id: Optional[str] = None
    reference: Optional[str] = None
    image_url: Optional[str] = None

    # Optional at-rest encryption (used by question security service)
    encrypted_question_text: Optional[str] = None
    encryption_key_id: Optional[str] = None
    encrypted_at: Optional[datetime] = None
    encrypted_options: Optional[str] = None
    options_encryption_key_id: Optional[str] = None
    options_encrypted_at: Optional[datetime] = None
    question_text_hash: Optional[str] = None
    options_hash: Optional[str] = None

    @property
    def has_options(self) -> bool:
        return self.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]

    @property
    def has_text_answer(self) -> bool:
        return self.question_type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]

    class Settings:
        name = "questions"


class QuestionOption(BaseDocument):
    """Options for multiple choice questions."""
    question_id: str
    option_text: str
    is_correct: bool = False
    option_order: int
    explanation: Optional[str] = None

    class Settings:
        name = "question_options"


class QuestionAnswer(BaseDocument):
    """Correct answer for questions (for non-MCQ types)."""
    question_id: str
    answer_text: str
    is_correct: bool = True
    explanation: Optional[str] = None

    class Settings:
        name = "question_answers"
