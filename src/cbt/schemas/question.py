"""
Question bank management schemas.
"""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Self
from datetime import datetime

from ..models.question import QuestionType, QuestionDifficulty, CognitiveLevel, QuestionStatus


class QuestionOptionBase(BaseModel):
    """Base question option schema."""
    option_text: str
    is_correct: bool = False
    explanation: Optional[str] = None

    @field_validator("option_text")
    @classmethod
    def validate_option_text(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Option text must be at least 1 character long")
        return v.strip()


class QuestionOptionCreate(QuestionOptionBase):
    """Question option creation schema."""
    pass


class QuestionOptionUpdate(BaseModel):
    """Question option update schema."""
    option_text: Optional[str] = None
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None


class QuestionOptionResponse(QuestionOptionBase):
    """Question option response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    order: int
    created_at: datetime
    updated_at: datetime


class QuestionBase(BaseModel):
    """Base question schema."""
    question_text: str
    question_type: QuestionType
    difficulty: QuestionDifficulty
    cognitive_level: CognitiveLevel
    topic: str
    points_value: int
    explanation: Optional[str] = None
    reference: Optional[str] = None
    image_url: Optional[str] = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("Question text must be at least 10 characters long")
        return v.strip()

    @field_validator("points_value")
    @classmethod
    def validate_points_value(cls, v: int) -> int:
        if v <= 0 or v > 100:
            raise ValueError("Points value must be between 1 and 100")
        return v

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Topic must be at least 2 characters long")
        return v.strip()


class QuestionCreate(QuestionBase):
    """Question creation schema."""
    course_id: str
    options: List[QuestionOptionCreate]

    @model_validator(mode="after")
    def validate_options(self) -> Self:
        v = self.options
        question_type = self.question_type

        if question_type == QuestionType.MULTIPLE_CHOICE:
            if len(v) < 2:
                raise ValueError(
                    "Multiple choice questions must have at least 2 options"
                )
            if len(v) > 6:
                raise ValueError(
                    "Multiple choice questions cannot have more than 6 options"
                )

            correct_count = sum(1 for option in v if option.is_correct)
            if correct_count != 1:
                raise ValueError(
                    "Multiple choice questions must have exactly one correct answer"
                )

        elif question_type == QuestionType.TRUE_FALSE:
            if len(v) != 2:
                raise ValueError("True/False questions must have exactly 2 options")

            correct_count = sum(1 for option in v if option.is_correct)
            if correct_count != 1:
                raise ValueError(
                    "True/False questions must have exactly one correct answer"
                )

        elif question_type == QuestionType.SHORT_ANSWER:
            if len(v) > 0:
                raise ValueError(
                    "Short answer questions should not have predefined options"
                )

        option_texts = [option.option_text.lower().strip() for option in v]
        if len(option_texts) != len(set(option_texts)):
            raise ValueError("Question options must be unique")

        return self


class QuestionUpdate(BaseModel):
    """Question update schema."""
    question_text: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    cognitive_level: Optional[CognitiveLevel] = None
    topic: Optional[str] = None
    points_value: Optional[int] = None
    explanation: Optional[str] = None
    reference: Optional[str] = None
    image_url: Optional[str] = None
    options: Optional[List[QuestionOptionUpdate]] = None


class QuestionResponse(QuestionBase):
    """Question response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    question_type: QuestionType
    status: QuestionStatus
    version: int
    created_by: str
    reviewed_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Options (only included if question is approved and user has permission)
    options: Optional[List[QuestionOptionResponse]] = None
    
    @property
    def is_approved(self) -> bool:
        """Check if question is approved."""
        return self.status == QuestionStatus.APPROVED
    
    @property
    def is_draft(self) -> bool:
        """Check if question is in draft status."""
        return self.status == QuestionStatus.DRAFT


class QuestionSearch(BaseModel):
    """Question search parameters."""
    course_id: Optional[str] = None
    question_type: Optional[QuestionType] = None
    difficulty: Optional[QuestionDifficulty] = None
    cognitive_level: Optional[CognitiveLevel] = None
    topic: Optional[str] = None
    status: Optional[QuestionStatus] = None
    created_by: Optional[str] = None
    limit: int = 50
    cursor: Optional[str] = None


class QuestionReviewRequest(BaseModel):
    """Question review request schema."""
    action: str  # "approve" or "reject"
    review_comments: Optional[str] = None
    suggested_changes: Optional[List[str]] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ["approve", "reject"]:
            raise ValueError('Action must be either "approve" or "reject"')
        return v


class QuestionReviewResponse(BaseModel):
    """Question review response schema."""
    success: bool
    message: str
    question_id: str
    new_status: QuestionStatus
    reviewed_at: datetime
    reviewed_by: str


class QuestionImportRequest(BaseModel):
    """Question import request schema."""
    course_id: str
    validate_only: bool = False
    continue_on_error: bool = False
    default_difficulty: Optional[QuestionDifficulty] = None
    default_cognitive_level: Optional[CognitiveLevel] = None


class QuestionImportResponse(BaseModel):
    """Question import response schema."""
    import_id: str
    total_records: int
    successful_imports: int
    failed_imports: int
    validation_errors: List[Dict[str, Any]]
    import_errors: List[Dict[str, Any]]
    status: str  # "pending", "processing", "completed", "failed"
    created_at: datetime
    completed_at: Optional[datetime] = None


class QuestionBulkOperation(BaseModel):
    """Bulk question operation schema."""
    operation: str  # "delete", "approve", "reject", "update_status"
    question_ids: List[str]
    parameters: Optional[Dict[str, Any]] = None

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed_operations = ["delete", "approve", "reject", "update_status"]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {allowed_operations}")
        return v

    @field_validator("question_ids")
    @classmethod
    def validate_question_ids(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("At least one question ID must be provided")
        if len(v) > 100:
            raise ValueError(
                "Cannot process more than 100 questions in a single operation"
            )
        return v


class QuestionMetadata(BaseModel):
    """Question metadata schema."""
    topic: str
    description: Optional[str] = None
    color: Optional[str] = None  # For UI display

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("#"):
            raise ValueError("Color must be a valid hex color code starting with #")
        return v


class QuestionVersionResponse(BaseModel):
    """Question version response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    question_text: str
    status: QuestionStatus
    created_at: datetime
    created_by: str
    change_summary: Optional[str] = None


class QuestionStatisticsResponse(BaseModel):
    """Question statistics response schema."""
    total_questions: int
    approved_questions: int
    draft_questions: int
    pending_review: int
    rejected_questions: int
    
    by_difficulty: Dict[str, int]
    by_cognitive_level: Dict[str, int]
    by_topic: Dict[str, int]
    by_question_type: Dict[str, int]
    
    average_points: float
    questions_with_images: int
    questions_with_explanations: int


class QuestionValidationResponse(BaseModel):
    """Question validation response schema."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class QuestionExportRequest(BaseModel):
    """Question export request schema."""
    course_id: Optional[str] = None
    status: Optional[QuestionStatus] = None
    difficulty: Optional[QuestionDifficulty] = None
    topic: Optional[str] = None
    include_options: bool = True
    include_explanations: bool = False
    format: str = "csv"  # "csv", "json", "excel"

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in ["csv", "json", "excel"]:
            raise ValueError("Format must be one of: csv, json, excel")
        return v


class QuestionExportResponse(BaseModel):
    """Question export response schema."""
    export_id: str
    file_url: Optional[str] = None
    status: str  # "pending", "processing", "completed", "failed"
    total_questions: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class QuestionBatchReviewRequest(BaseModel):
    """Batch question review request schema."""
    question_ids: List[str]
    action: str  # "approve" or "reject"
    review_comments: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_batch_action(cls, v: str) -> str:
        if v not in ["approve", "reject"]:
            raise ValueError('Action must be either "approve" or "reject"')
        return v


class QuestionDuplicateRequest(BaseModel):
    """Question duplication request schema."""
    target_course_id: Optional[str] = None
    update_topic: Optional[str] = None
    update_difficulty: Optional[QuestionDifficulty] = None


class QuestionImageUploadResponse(BaseModel):
    """Question image upload response schema."""
    success: bool
    image_url: str
    file_name: str
    file_size: int
    watermark_applied: bool
    virus_scan_status: str  # "pending", "clean", "infected"


class QuestionTopicResponse(BaseModel):
    """Question topic response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    description: Optional[str]
    color: Optional[str]
    question_count: int
    created_at: datetime
