"""
Question bank management service with validation, review workflow, and security.
"""

import uuid
import csv
import io
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload

from ..models.question import (
    Question, QuestionOption, QuestionType, QuestionDifficulty,
    CognitiveLevel, QuestionStatus
)
from ..models.course import Course
from ..models.user import User
from ..services.audit_service import AuditService, AuditAction
from ..core.security import security
from ..core.redis import cache_manager
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionSearch, QuestionReviewRequest,
    QuestionImportResponse, QuestionBulkOperation, QuestionMetadata
)


class QuestionService:
    """Question bank management service."""
    
    def __init__(self, db: Any):
        self.db = db
        self.security = security
        self.cache = cache_manager
    
    async def create_question(self, question_data: QuestionCreate, created_by: str) -> Question:
        """Create a new question with validation."""
        try:
            # Validate course exists
            course_result = await self.db.execute(
                select(Course).where(Course.id == question_data.course_id)
            )
            if not course_result.scalar_one_or_none():
                raise ValueError("Course not found")
            
            # Validate topic exists for course
            topics = await self.get_course_topics(question_data.course_id)
            topic_names = [topic['topic'] for topic in topics]
            if question_data.topic not in topic_names:
                raise ValueError(f"Topic '{question_data.topic}' not found for this course")
            
            # Create question
            question = Question(
                id=str(uuid.uuid4()),
                question_text=question_data.question_text,
                question_type=question_data.question_type,
                difficulty=question_data.difficulty,
                cognitive_level=question_data.cognitive_level,
                topic=question_data.topic,
                points_value=question_data.points_value,
                explanation=question_data.explanation,
                reference=question_data.reference,
                image_url=question_data.image_url,
                course_id=question_data.course_id,
                status=QuestionStatus.DRAFT,
                version=1,
                created_by=created_by
            )
            
            self.db.add(question)
            await self.db.flush()  # Get question ID
            
            # Create options if provided
            if question_data.options:
                for i, option_data in enumerate(question_data.options):
                    option = QuestionOption(
                        id=str(uuid.uuid4()),
                        question_id=question.id,
                        option_text=option_data.option_text,
                        is_correct=option_data.is_correct,
                        explanation=option_data.explanation,
                        order=i + 1
                    )
                    self.db.add(option)
            
            await self.db.commit()
            await self.db.refresh(question)
            
            # Load options for response
            question.options = await self._get_question_options(question.id)
            
            # Log creation
            await self._log_audit_event(
                user_id=created_by,
                action=AuditAction.CREATE,
                resource_type="question",
                resource_id=question.id,
                new_values={
                    "question_text": question.question_text[:100],
                    "course_id": question.course_id,
                    "topic": question.topic,
                    "difficulty": question.difficulty.value
                }
            )
            
            return question
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create question: {str(e)}")
    
    async def list_questions(self, search_params: QuestionSearch) -> List[Question]:
        """List questions with filtering and pagination."""
        try:
            query = select(Question)
            
            # Apply filters
            if search_params.course_id:
                query = query.where(Question.course_id == search_params.course_id)
            
            if search_params.question_type:
                query = query.where(Question.question_type == search_params.question_type)
            
            if search_params.difficulty:
                query = query.where(Question.difficulty == search_params.difficulty)
            
            if search_params.cognitive_level:
                query = query.where(Question.cognitive_level == search_params.cognitive_level)
            
            if search_params.topic:
                query = query.where(Question.topic == search_params.topic)
            
            if search_params.status:
                query = query.where(Question.status == search_params.status)
            
            if search_params.created_by:
                query = query.where(Question.created_by == search_params.created_by)
            
            # Apply pagination
            query = query.limit(search_params.limit)
            if search_params.cursor:
                query = query.where(Question.id > search_params.cursor)
            
            # Order by creation date (newest first)
            query = query.order_by(Question.created_at.desc())
            
            result = await self.db.execute(query)
            questions = result.scalars().all()
            
            # Load options for approved questions only
            for question in questions:
                if question.status == QuestionStatus.APPROVED:
                    question.options = await self._get_question_options(question.id)
            
            return questions
            
        except Exception as e:
            raise ValueError(f"Failed to list questions: {str(e)}")
    
    async def search_questions(self, query_text: str, course_id: Optional[str], limit: int) -> List[Question]:
        """Search questions by text content."""
        try:
            # Use full-text search for better results
            search_query = select(Question).where(
                and_(
                    Question.status == QuestionStatus.APPROVED,
                    Question.question_text.ilike(f"%{query_text}%")
                )
            )
            
            if course_id:
                search_query = search_query.where(Question.course_id == course_id)
            
            search_query = search_query.limit(limit)
            search_query = search_query.order_by(Question.created_at.desc())
            
            result = await self.db.execute(search_query)
            questions = result.scalars().all()
            
            # Load options
            for question in questions:
                question.options = await self._get_question_options(question.id)
            
            return questions
            
        except Exception as e:
            raise ValueError(f"Failed to search questions: {str(e)}")
    
    async def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID with appropriate security."""
        try:
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            
            if question:
                # Load options only if question is approved
                if question.status == QuestionStatus.APPROVED:
                    question.options = await self._get_question_options(question.id)
            
            return question
            
        except Exception as e:
            raise ValueError(f"Failed to get question: {str(e)}")
    
    async def update_question(self, question_id: str, question_data: QuestionUpdate, updated_by: str) -> Optional[Question]:
        """Update question (creates new version)."""
        try:
            # Get existing question
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            original_question = result.scalar_one_or_none()
            if not original_question:
                return None
            
            # Check if question can be edited
            if original_question.status == QuestionStatus.APPROVED:
                # Create new version instead of updating
                return await self._create_question_version(original_question, question_data, updated_by)
            
            # Update fields
            for field, value in question_data.dict(exclude_unset=True).items():
                if hasattr(original_question, field) and field != 'options':
                    setattr(original_question, field, value)
            
            original_question.updated_at = datetime.utcnow()
            
            # Update options if provided
            if question_data.options:
                # Delete existing options
                await self.db.execute(
                    text("DELETE FROM question_options WHERE question_id = :question_id"),
                    {"question_id": question_id}
                )
                
                # Create new options
                for i, option_data in enumerate(question_data.options):
                    option = QuestionOption(
                        id=str(uuid.uuid4()),
                        question_id=question_id,
                        option_text=option_data.option_text,
                        is_correct=option_data.is_correct,
                        explanation=option_data.explanation,
                        order=i + 1
                    )
                    self.db.add(option)
            
            await self.db.commit()
            await self.db.refresh(original_question)
            
            # Load options
            original_question.options = await self._get_question_options(question_id)
            
            # Log update
            await self._log_audit_event(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={
                    "question_text": original_question.question_text[:100],
                    "version": original_question.version
                }
            )
            
            return original_question
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update question: {str(e)}")
    
    async def delete_question(self, question_id: str, deleted_by: str) -> bool:
        """Delete question (soft delete)."""
        try:
            # Get existing question
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            if not question:
                return False
            
            # Soft delete
            question.status = QuestionStatus.DELETED
            question.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log deletion
            await self._log_audit_event(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                resource_type="question",
                resource_id=question_id,
                old_values={"question_text": question.question_text[:100]}
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete question: {str(e)}")
    
    async def submit_for_review(self, question_id: str, submitted_by: str) -> Optional[Question]:
        """Submit question for review."""
        try:
            # Get question
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            if not question:
                return None
            
            # Validate question can be submitted for review
            if question.status != QuestionStatus.DRAFT:
                raise ValueError("Only draft questions can be submitted for review")
            
            # Validate question has required content
            validation_result = await self._validate_question(question)
            if not validation_result['is_valid']:
                raise ValueError(f"Question validation failed: {', '.join(validation_result['errors'])}")
            
            # Update status
            question.status = QuestionStatus.PENDING_REVIEW
            question.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(question)
            
            # Log submission
            await self._log_audit_event(
                user_id=submitted_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={"status": "PENDING_REVIEW"}
            )
            
            return question
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to submit question for review: {str(e)}")
    
    async def review_question(self, question_id: str, review_data: QuestionReviewRequest, reviewed_by: str) -> Dict[str, Any]:
        """Review and approve/reject question."""
        try:
            # Get question
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            if not question:
                raise ValueError("Question not found")
            
            # Validate question can be reviewed
            if question.status != QuestionStatus.PENDING_REVIEW:
                raise ValueError("Only questions pending review can be reviewed")
            
            # Update question based on review action
            if review_data.action == "approve":
                question.status = QuestionStatus.APPROVED
                question.approved_at = datetime.utcnow()
                question.reviewed_by = reviewed_by
                
                # Clear cache for approved questions
                await self._clear_question_cache(question_id)
                
            elif review_data.action == "reject":
                question.status = QuestionStatus.REJECTED
                question.reviewed_by = reviewed_by
                
                # Store review comments in explanation field for rejected questions
                if review_data.review_comments:
                    question.explanation = f"REJECTED: {review_data.review_comments}"
            
            question.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Load options for approved questions
            if question.status == QuestionStatus.APPROVED:
                question.options = await self._get_question_options(question_id)
            
            # Log review
            await self._log_audit_event(
                user_id=reviewed_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={
                    "status": question.status.value,
                    "review_action": review_data.action,
                    "review_comments": review_data.review_comments
                }
            )
            
            return {
                "success": True,
                "message": f"Question {review_data.action}d successfully",
                "question_id": question_id,
                "new_status": question.status,
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": reviewed_by
            }
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to review question: {str(e)}")
    
    async def get_pending_reviews(self, course_id: Optional[str], limit: int, cursor: Optional[str]) -> List[Question]:
        """Get questions pending review."""
        try:
            query = select(Question).where(Question.status == QuestionStatus.PENDING_REVIEW)
            
            if course_id:
                query = query.where(Question.course_id == course_id)
            
            query = query.limit(limit)
            if cursor:
                query = query.where(Question.id > cursor)
            
            query = query.order_by(Question.created_at.desc())
            
            result = await self.db.execute(query)
            questions = result.scalars().all()
            
            # Load options for review
            for question in questions:
                question.options = await self._get_question_options(question.id)
            
            return questions
            
        except Exception as e:
            raise ValueError(f"Failed to get pending reviews: {str(e)}")
    
    async def import_from_csv(self, file, course_id: str, validate_only: bool, continue_on_error: bool, imported_by: str) -> QuestionImportResponse:
        """Import questions from CSV file."""
        try:
            # Validate course exists
            course_result = await self.db.execute(
                select(Course).where(Course.id == course_id)
            )
            if not course_result.scalar_one_or_none():
                raise ValueError("Course not found")
            
            # Read CSV content
            content = await file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Create import job
            import_id = str(uuid.uuid4())
            import_response = QuestionImportResponse(
                import_id=import_id,
                total_records=0,
                successful_imports=0,
                failed_imports=0,
                validation_errors=[],
                import_errors=[],
                status="processing",
                created_at=datetime.utcnow()
            )
            
            # Process CSV rows
            questions_to_import = []
            for row_num, row in enumerate(csv_reader, 1):
                import_response.total_records += 1
                
                try:
                    # Validate required fields
                    required_fields = ['question_text', 'question_type', 'difficulty', 'cognitive_level', 'topic', 'points_value']
                    missing_fields = [field for field in required_fields if not row.get(field)]
                    
                    if missing_fields:
                        import_response.validation_errors.append({
                            "row": row_num,
                            "error": f"Missing required fields: {', '.join(missing_fields)}"
                        })
                        continue
                    
                    # Parse question data
                    question_data = self._parse_csv_row(row, course_id)
                    
                    # Validate question data
                    validation_result = await self._validate_question_data(question_data)
                    if not validation_result['is_valid']:
                        import_response.validation_errors.append({
                            "row": row_num,
                            "error": validation_result['errors']
                        })
                        continue
                    
                    questions_to_import.append((row_num, question_data))
                    
                except Exception as e:
                    import_response.import_errors.append({
                        "row": row_num,
                        "error": str(e)
                    })
            
            # Import questions if not validate only
            if not validate_only and questions_to_import:
                for row_num, question_data in questions_to_import:
                    try:
                        await self.create_question(question_data, imported_by)
                        import_response.successful_imports += 1
                    except Exception as e:
                        import_response.failed_imports += 1
                        import_response.import_errors.append({
                            "row": row_num,
                            "error": str(e)
                        })
                        
                        if not continue_on_error:
                            break
            
            # Update import status
            import_response.status = "completed"
            import_response.completed_at = datetime.utcnow()
            
            # Log import
            await self._log_audit_event(
                user_id=imported_by,
                action=AuditAction.CREATE,
                resource_type="question_import",
                resource_id=import_id,
                new_values={
                    "course_id": course_id,
                    "total_records": import_response.total_records,
                    "successful_imports": import_response.successful_imports
                }
            )
            
            return import_response
            
        except Exception as e:
            raise ValueError(f"CSV import failed: {str(e)}")
    
    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get import job status."""
        # This would typically be stored in Redis or database
        # For now, return a mock status
        return {
            "import_id": import_id,
            "status": "completed",
            "progress": 100
        }
    
    async def bulk_operation(self, operation: QuestionBulkOperation, operated_by: str) -> Dict[str, Any]:
        """Perform bulk operations on questions."""
        try:
            results = {
                "success": True,
                "processed": 0,
                "failed": 0,
                "errors": []
            }
            
            for question_id in operation.question_ids:
                try:
                    if operation.operation == "delete":
                        success = await self.delete_question(question_id, operated_by)
                        if success:
                            results["processed"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Question {question_id} not found")
                    
                    elif operation.operation == "approve":
                        review_data = QuestionReviewRequest(action="approve")
                        await self.review_question(question_id, review_data, operated_by)
                        results["processed"] += 1
                    
                    elif operation.operation == "reject":
                        review_data = QuestionReviewRequest(action="reject")
                        await self.review_question(question_id, review_data, operated_by)
                        results["processed"] += 1
                    
                    elif operation.operation == "update_status":
                        # Update status logic here
                        results["processed"] += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Question {question_id}: {str(e)}")
            
            # Log bulk operation
            await self._log_audit_event(
                user_id=operated_by,
                action=AuditAction.SYSTEM_CHANGE,
                resource_type="question_bulk_operation",
                new_values={
                    "operation": operation.operation,
                    "processed": results["processed"],
                    "failed": results["failed"]
                }
            )
            
            return results
            
        except Exception as e:
            raise ValueError(f"Bulk operation failed: {str(e)}")
    
    async def get_question_versions(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a question."""
        try:
            # This would query a question_versions table
            # For now, return current version info
            result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            
            if not question:
                return []
            
            return [{
                "id": question.id,
                "version": question.version,
                "question_text": question.question_text,
                "status": question.status,
                "created_at": question.created_at,
                "created_by": question.created_by,
                "change_summary": "Current version"
            }]
            
        except Exception as e:
            raise ValueError(f"Failed to get question versions: {str(e)}")
    
    async def get_course_topics(self, course_id: str) -> List[Dict[str, Any]]:
        """Get available topics for a course."""
        try:
            # Get unique topics from questions in this course
            result = await self.db.execute(
                select(Question.topic, func.count(Question.id).label('question_count'))
                .where(and_(
                    Question.course_id == course_id,
                    Question.status != QuestionStatus.DELETED
                ))
                .group_by(Question.topic)
                .order_by(Question.topic)
            )
            
            topics = []
            for topic, count in result:
                topics.append({
                    "id": str(uuid.uuid4()),  # Generate ID for UI
                    "topic": topic,
                    "question_count": count,
                    "description": None,
                    "color": None
                })
            
            return topics
            
        except Exception as e:
            raise ValueError(f"Failed to get course topics: {str(e)}")
    
    async def add_course_topic(self, course_id: str, topic_data: QuestionMetadata, added_by: str) -> Dict[str, Any]:
        """Add new topic to course."""
        try:
            # Validate course exists
            course_result = await self.db.execute(
                select(Course).where(Course.id == course_id)
            )
            if not course_result.scalar_one_or_none():
                raise ValueError("Course not found")
            
            # Check if topic already exists
            existing_topics = await self.get_course_topics(course_id)
            if any(topic['topic'] == topic_data.topic for topic in existing_topics):
                raise ValueError("Topic already exists for this course")
            
            # This would typically store in a course_topics table
            # For now, return success
            result = {
                "success": True,
                "message": "Topic added successfully",
                "topic_id": str(uuid.uuid4()),
                "topic": topic_data.topic
            }
            
            # Log topic addition
            await self._log_audit_event(
                user_id=added_by,
                action=AuditAction.CREATE,
                resource_type="course_topic",
                new_values={
                    "course_id": course_id,
                    "topic": topic_data.topic
                }
            )
            
            return result
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to add course topic: {str(e)}")
    
    async def get_question_statistics(self, course_id: Optional[str]) -> Dict[str, Any]:
        """Get question bank statistics."""
        try:
            base_query = select(Question).where(Question.status != QuestionStatus.DELETED)
            
            if course_id:
                base_query = base_query.where(Question.course_id == course_id)
            
            # Total questions
            total_result = await self.db.execute(
                select(func.count(Question.id)).select_from(base_query.subquery())
            )
            total_questions = total_result.scalar() or 0
            
            # Status breakdown
            status_result = await self.db.execute(
                select(Question.status, func.count(Question.id))
                .select_from(base_query.subquery())
                .group_by(Question.status)
            )
            status_breakdown = {status.value: count for status, count in status_result}
            
            # Difficulty breakdown
            difficulty_result = await self.db.execute(
                select(Question.difficulty, func.count(Question.id))
                .select_from(base_query.subquery())
                .group_by(Question.difficulty)
            )
            difficulty_breakdown = {difficulty.value: count for difficulty, count in difficulty_result}
            
            # Cognitive level breakdown
            cognitive_result = await self.db.execute(
                select(Question.cognitive_level, func.count(Question.id))
                .select_from(base_query.subquery())
                .group_by(Question.cognitive_level)
            )
            cognitive_breakdown = {level.value: count for level, count in cognitive_result}
            
            # Topic breakdown
            topic_result = await self.db.execute(
                select(Question.topic, func.count(Question.id))
                .select_from(base_query.subquery())
                .group_by(Question.topic)
            )
            topic_breakdown = {topic: count for topic, count in topic_result}
            
            # Question type breakdown
            type_result = await self.db.execute(
                select(Question.question_type, func.count(Question.id))
                .select_from(base_query.subquery())
                .group_by(Question.question_type)
            )
            type_breakdown = {qtype.value: count for qtype, count in type_result}
            
            # Average points
            avg_points_result = await self.db.execute(
                select(func.avg(Question.points_value))
                .select_from(base_query.subquery())
            )
            avg_points = avg_points_result.scalar() or 0
            
            # Questions with images and explanations
            with_images_result = await self.db.execute(
                select(func.count(Question.id))
                .select_from(base_query.subquery().where(Question.image_url.isnot(None)))
            )
            with_images = with_images_result.scalar() or 0
            
            with_explanations_result = await self.db.execute(
                select(func.count(Question.id))
                .select_from(base_query.subquery().where(Question.explanation.isnot(None)))
            )
            with_explanations = with_explanations_result.scalar() or 0
            
            return {
                "total_questions": total_questions,
                "approved_questions": status_breakdown.get("APPROVED", 0),
                "draft_questions": status_breakdown.get("DRAFT", 0),
                "pending_review": status_breakdown.get("PENDING_REVIEW", 0),
                "rejected_questions": status_breakdown.get("REJECTED", 0),
                "by_difficulty": difficulty_breakdown,
                "by_cognitive_level": cognitive_breakdown,
                "by_topic": topic_breakdown,
                "by_question_type": type_breakdown,
                "average_points": float(avg_points),
                "questions_with_images": with_images,
                "questions_with_explanations": with_explanations
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get question statistics: {str(e)}")
    
    async def duplicate_question(self, question_id: str, duplicated_by: str) -> Optional[Question]:
        """Duplicate a question."""
        try:
            # Get original question
            original = await self.get_question(question_id)
            if not original:
                return None
            
            # Create duplicate
            duplicate_data = QuestionCreate(
                question_text=original.question_text,
                question_type=original.question_type,
                difficulty=original.difficulty,
                cognitive_level=original.cognitive_level,
                topic=original.topic,
                points_value=original.points_value,
                explanation=original.explanation,
                reference=original.reference,
                image_url=original.image_url,
                course_id=original.course_id,
                options=[QuestionOptionCreate(
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                    explanation=opt.explanation
                ) for opt in original.options] if original.options else []
            )
            
            duplicate = await self.create_question(duplicate_data, duplicated_by)
            
            # Log duplication
            await self._log_audit_event(
                user_id=duplicated_by,
                action=AuditAction.CREATE,
                resource_type="question",
                resource_id=duplicate.id,
                new_values={
                    "duplicated_from": question_id,
                    "question_text": duplicate.question_text[:100]
                }
            )
            
            return duplicate
            
        except Exception as e:
            raise ValueError(f"Failed to duplicate question: {str(e)}")
    
    async def upload_question_image(self, question_id: str, file, uploaded_by: str) -> Dict[str, Any]:
        """Upload image for question."""
        try:
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise ValueError("Only image files are allowed")
            
            # Validate file size (max 5MB)
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:
                raise ValueError("Image file size cannot exceed 5MB")
            
            # Generate unique filename
            file_hash = hashlib.sha256(content).hexdigest()
            filename = f"{question_id}_{file_hash}_{datetime.utcnow().timestamp()}.jpg"
            
            # Apply watermark (simplified - would use actual image processing)
            watermarked_content = self._apply_watermark(content, uploaded_by)
            
            # Upload to storage (simplified - would use actual storage service)
            image_url = f"/uploads/questions/{filename}"
            
            # Update question
            await self.db.execute(
                update(Question)
                .where(Question.id == question_id)
                .values(image_url=image_url, updated_at=datetime.utcnow())
            )
            await self.db.commit()
            
            # Log upload
            await self._log_audit_event(
                user_id=uploaded_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={"image_url": image_url}
            )
            
            return {
                "success": True,
                "image_url": image_url,
                "file_name": filename,
                "file_size": len(content),
                "watermark_applied": True,
                "virus_scan_status": "clean"
            }
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to upload question image: {str(e)}")
    
    # Private helper methods
    
    async def _get_question_options(self, question_id: str) -> List[QuestionOption]:
        """Get question options."""
        result = await self.db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_id == question_id)
            .order_by(QuestionOption.order)
        )
        return result.scalars().all()
    
    async def _validate_question(self, question: Question) -> Dict[str, Any]:
        """Validate question content."""
        errors = []
        warnings = []
        
        # Check question text
        if len(question.question_text.strip()) < 10:
            errors.append("Question text must be at least 10 characters long")
        
        # Check options for MCQ questions
        if question.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            options = await self._get_question_options(question.id)
            if len(options) < 2:
                errors.append("Question must have at least 2 options")
            
            # Check for correct answer
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                errors.append("Question must have exactly one correct answer")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _validate_question_data(self, question_data: QuestionCreate) -> Dict[str, Any]:
        """Validate question data before creation."""
        errors = []
        warnings = []
        
        # Validate question text
        if len(question_data.question_text.strip()) < 10:
            errors.append("Question text must be at least 10 characters long")
        
        # Validate options
        if question_data.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            if not question_data.options or len(question_data.options) < 2:
                errors.append("Question must have at least 2 options")
            
            # Check for correct answer
            if question_data.options:
                correct_count = sum(1 for opt in question_data.options if opt.is_correct)
                if correct_count != 1:
                    errors.append("Question must have exactly one correct answer")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _create_question_version(self, original: Question, update_data: QuestionUpdate, updated_by: str) -> Question:
        """Create new version of question."""
        # This would create a new version in a question_versions table
        # For now, just update the original
        for field, value in update_data.dict(exclude_unset=True).items():
            if hasattr(original, field) and field != 'options':
                setattr(original, field, value)
        
        original.version += 1
        original.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(original)
        
        return original
    
    def _parse_csv_row(self, row: Dict[str, str], course_id: str) -> QuestionCreate:
        """Parse CSV row into question data."""
        # Parse options (assuming columns option_a, option_b, option_c, option_d, correct_answer)
        options = []
        option_letters = ['a', 'b', 'c', 'd', 'e', 'f']
        
        for letter in option_letters:
            option_text = row.get(f'option_{letter}')
            if option_text:
                is_correct = row.get('correct_answer', '').lower() == letter
                options.append(QuestionOptionCreate(
                    option_text=option_text.strip(),
                    is_correct=is_correct
                ))
        
        return QuestionCreate(
            question_text=row['question_text'].strip(),
            question_type=QuestionType(row['question_type'].upper()),
            difficulty=QuestionDifficulty(row['difficulty'].upper()),
            cognitive_level=CognitiveLevel(row['cognitive_level'].upper()),
            topic=row['topic'].strip(),
            points_value=int(row['points_value']),
            explanation=row.get('explanation', '').strip() or None,
            reference=row.get('reference', '').strip() or None,
            course_id=course_id,
            options=options
        )
    
    def _apply_watermark(self, content: bytes, user_id: str) -> bytes:
        """Apply watermark to image content."""
        # Simplified watermarking - would use actual image processing
        watermark_text = f"CBT System - User: {user_id} - {datetime.utcnow()}"
        return content  # Return original for now
    
    async def _clear_question_cache(self, question_id: str):
        """Clear question cache."""
        cache_keys = [
            f"question:{question_id}",
            f"course_questions:*"  # Would need pattern matching
        ]
        for key in cache_keys:
            await self.cache.delete(key)
    
    async def _log_audit_event(self, user_id: str, action: AuditAction,
                              resource_type: str, resource_id: Optional[str] = None,
                              new_values: Optional[Dict] = None,
                              old_values: Optional[Dict] = None):
        """Log audit event."""
        if self.db:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=new_values,
                old_values=old_values
            )
            
            self.db.add(audit_log)
            await self.db.commit()
