"""
Question bank and question models using Beanie (MongoDB).
"""

from typing import Optional, List
import enum
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


class DifficultyLevel(str, enum.Enum):
    """Question difficulty levels."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


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
    difficulty: DifficultyLevel
    points_value: int
    time_limit_seconds: Optional[int] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    version: int = 1
    question_bank_id: str
    created_by: str
    updated_by: Optional[str] = None

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
