"""
Question bank management API endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File

from ..models.question import Question, QuestionType, QuestionDifficulty, CognitiveLevel, QuestionStatus
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionSearch,
    QuestionReviewRequest, QuestionReviewResponse, QuestionImportRequest,
    QuestionImportResponse, QuestionBulkOperation, QuestionMetadata
)
from ..services.question_service import QuestionService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("question.create"))])
async def create_question(
    question_data: QuestionCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionResponse:
    """Create a new question."""
    try:
        question_service = QuestionService(db)
        question = await question_service.create_question(question_data, current_user.id)
        return QuestionResponse.from_orm(question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create question"
        )


@router.get("/", response_model=List[QuestionResponse], dependencies=[Depends(require_permission("question.read"))])
async def list_questions(
    course_id: Optional[str] = Query(None),
    question_type: Optional[QuestionType] = Query(None),
    difficulty: Optional[QuestionDifficulty] = Query(None),
    cognitive_level: Optional[CognitiveLevel] = Query(None),
    topic: Optional[str] = Query(None),
    q_status: Optional[QuestionStatus] = Query(None, alias="status"),
    created_by: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[QuestionResponse]:
    """List questions with filtering and pagination."""
    try:
        question_service = QuestionService(db)
        search_params = QuestionSearch(
            course_id=course_id,
            question_type=question_type,
            difficulty=difficulty,
            cognitive_level=cognitive_level,
            topic=topic,
            status=q_status,
            created_by=created_by,
            limit=limit,
            cursor=cursor
        )
        
        questions = await question_service.list_questions(search_params)
        return [QuestionResponse.from_orm(question) for question in questions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list questions"
        )


@router.get("/search", response_model=List[QuestionResponse], dependencies=[Depends(require_permission("question.read"))])
async def search_questions(
    query: str = Query(..., min_length=2),
    course_id: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[QuestionResponse]:
    """Search questions by text."""
    try:
        question_service = QuestionService(db)
        questions = await question_service.search_questions(query, course_id, limit)
        return [QuestionResponse.from_orm(question) for question in questions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search questions"
        )


@router.get("/{question_id}", response_model=QuestionResponse, dependencies=[Depends(require_permission("question.read"))])
async def get_question(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionResponse:
    """Get question by ID."""
    try:
        question_service = QuestionService(db)
        question = await question_service.get_question(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return QuestionResponse.from_orm(question)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question"
        )


@router.put("/{question_id}", response_model=QuestionResponse, dependencies=[Depends(require_permission("question.update"))])
async def update_question(
    question_id: str,
    question_data: QuestionUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionResponse:
    """Update question (creates new version)."""
    try:
        question_service = QuestionService(db)
        question = await question_service.update_question(question_id, question_data, current_user.id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return QuestionResponse.from_orm(question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update question"
        )


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("question.delete"))])
async def delete_question(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete question (soft delete)."""
    try:
        question_service = QuestionService(db)
        success = await question_service.delete_question(question_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete question"
        )


@router.post("/{question_id}/submit-for-review", dependencies=[Depends(require_permission("question.update"))])
async def submit_question_for_review(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionResponse:
    """Submit question for review."""
    try:
        question_service = QuestionService(db)
        question = await question_service.submit_for_review(question_id, current_user.id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return QuestionResponse.from_orm(question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit question for review"
        )


@router.post("/{question_id}/review", response_model=QuestionReviewResponse, dependencies=[Depends(require_permission("question.review"))])
async def review_question(
    question_id: str,
    review_data: QuestionReviewRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionReviewResponse:
    """Review and approve/reject question."""
    try:
        question_service = QuestionService(db)
        result = await question_service.review_question(question_id, review_data, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review question"
        )


@router.get("/review/pending", response_model=List[QuestionResponse], dependencies=[Depends(require_permission("question.review"))])
async def get_pending_reviews(
    course_id: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    cursor: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[QuestionResponse]:
    """Get questions pending review."""
    try:
        question_service = QuestionService(db)
        questions = await question_service.get_pending_reviews(course_id, limit, cursor)
        return [QuestionResponse.from_orm(question) for question in questions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending reviews"
        )


@router.post("/import", response_model=QuestionImportResponse, dependencies=[Depends(require_permission("question.import"))])
async def import_questions_from_csv(
    file: UploadFile = File(...),
    course_id: str = Query(...),
    validate_only: bool = Query(False),
    continue_on_error: bool = Query(False),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionImportResponse:
    """Import questions from CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        question_service = QuestionService(db)
        result = await question_service.import_from_csv(
            file, course_id, validate_only, continue_on_error, current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV import failed: {str(e)}"
        )


@router.get("/import/{import_id}/status", dependencies=[Depends(require_permission("question.read"))])
async def get_import_status(
    import_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get import job status."""
    try:
        question_service = QuestionService(db)
        import_status = await question_service.get_import_status(import_id)
        if not import_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        return import_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get import status"
        )


@router.post("/bulk", response_model=dict, dependencies=[Depends(require_permission("question.update"))])
async def bulk_question_operation(
    operation: QuestionBulkOperation,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Perform bulk operations on questions."""
    try:
        question_service = QuestionService(db)
        result = await question_service.bulk_operation(operation, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk operation failed"
        )


@router.get("/{question_id}/versions", dependencies=[Depends(require_permission("question.read"))])
async def get_question_versions(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all versions of a question."""
    try:
        question_service = QuestionService(db)
        versions = await question_service.get_question_versions(question_id)
        return versions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question versions"
        )


@router.get("/metadata/topics", dependencies=[Depends(require_permission("question.read"))])
async def get_course_topics(
    course_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get available topics for a course."""
    try:
        question_service = QuestionService(db)
        topics = await question_service.get_course_topics(course_id)
        return topics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course topics"
        )


@router.post("/metadata/topics", dependencies=[Depends(require_permission("course.update"))])
async def add_course_topic(
    course_id: str,
    topic_data: QuestionMetadata,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Add new topic to course."""
    try:
        question_service = QuestionService(db)
        result = await question_service.add_course_topic(course_id, topic_data, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add course topic"
        )


@router.get("/statistics", dependencies=[Depends(require_permission("question.read"))])
async def get_question_statistics(
    course_id: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get question bank statistics."""
    try:
        question_service = QuestionService(db)
        stats = await question_service.get_question_statistics(course_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question statistics"
        )


@router.post("/{question_id}/duplicate", dependencies=[Depends(require_permission("question.create"))])
async def duplicate_question(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionResponse:
    """Duplicate a question."""
    try:
        question_service = QuestionService(db)
        question = await question_service.duplicate_question(question_id, current_user.id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return QuestionResponse.from_orm(question)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate question"
        )


@router.post("/{question_id}/upload-image", dependencies=[Depends(require_permission("question.update"))])
async def upload_question_image(
    question_id: str,
    file: UploadFile = File(...),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload image for question."""
    try:
        question_service = QuestionService(db)
        result = await question_service.upload_question_image(question_id, file, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload question image"
        )
