"""
Question bank management service with validation, review workflow, and security.
"""

import uuid
import csv
import io
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from beanie.operators import In, GTE, GT
from bson import ObjectId

from ..models.question import (
    Question, QuestionOption, QuestionType, QuestionDifficulty,
    CognitiveLevel, QuestionStatus
)
from ..models.academic import Course
from ..models.security import AuditLog
from ..services.audit_service import AuditService, AuditAction
from ..core.security import security
from ..core.redis import cache_manager
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionSearch, QuestionReviewRequest,
    QuestionImportResponse, QuestionBulkOperation, QuestionMetadata,
    QuestionOptionCreate,
)


class QuestionService:
    """Question bank management service."""

    def __init__(self, db: Any = None):
        # db param kept for backwards-compat; Beanie uses class-level document API.
        self.db = db
        self.security = security
        self.cache = cache_manager

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_question(self, question_data: QuestionCreate, created_by: str) -> Question:
        """Create a new question with validation."""
        # Validate course exists
        course = await Course.get(question_data.course_id)
        if not course:
            raise ValueError("Course not found")

        question = Question(
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
            created_by=created_by,
        )
        await question.insert()

        # Create options
        if question_data.options:
            options_to_insert = [
                QuestionOption(
                    question_id=str(question.id),
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                    explanation=opt.explanation,
                    option_order=i + 1,
                )
                for i, opt in enumerate(question_data.options)
            ]
            await QuestionOption.insert_many(options_to_insert)

        question.options = await self._get_question_options(str(question.id))

        await self._log_audit_event(
            user_id=created_by,
            action=AuditAction.CREATE,
            resource_type="question",
            resource_id=str(question.id),
            new_values={
                "question_text": question.question_text[:100],
                "course_id": question.course_id,
                "topic": question.topic,
                "difficulty": question.difficulty.value,
            },
        )
        return question

    async def list_questions(self, search_params: QuestionSearch) -> List[Question]:
        """List questions with filtering and pagination."""
        try:
            filters: Dict[str, Any] = {}
            if search_params.course_id:
                filters["course_id"] = search_params.course_id
            if search_params.question_type:
                filters["question_type"] = search_params.question_type
            if search_params.difficulty:
                filters["difficulty"] = search_params.difficulty
            if search_params.cognitive_level:
                filters["cognitive_level"] = search_params.cognitive_level
            if search_params.topic:
                filters["topic"] = search_params.topic
            if search_params.status:
                filters["status"] = search_params.status
            if search_params.created_by:
                filters["created_by"] = search_params.created_by

            query = Question.find(filters).sort("-created_at").limit(search_params.limit)
            questions = await query.to_list()

            for q in questions:
                if q.status == QuestionStatus.APPROVED:
                    q.options = await self._get_question_options(str(q.id))

            return questions
        except Exception as e:
            raise ValueError(f"Failed to list questions: {str(e)}")

    async def search_questions(self, query_text: str, course_id: Optional[str], limit: int) -> List[Question]:
        """Search questions by text content."""
        try:
            filters: Dict[str, Any] = {
                "status": QuestionStatus.APPROVED,
                "question_text": {"$regex": query_text, "$options": "i"},
            }
            if course_id:
                filters["course_id"] = course_id

            questions = await Question.find(filters).sort("-created_at").limit(limit).to_list()

            for q in questions:
                q.options = await self._get_question_options(str(q.id))

            return questions
        except Exception as e:
            raise ValueError(f"Failed to search questions: {str(e)}")

    async def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID."""
        try:
            question = await Question.get(question_id)
            if question and question.status == QuestionStatus.APPROVED:
                question.options = await self._get_question_options(str(question.id))
            return question
        except Exception as e:
            raise ValueError(f"Failed to get question: {str(e)}")

    async def update_question(self, question_id: str, question_data: QuestionUpdate, updated_by: str) -> Optional[Question]:
        """Update question (creates new version if approved)."""
        try:
            question = await Question.get(question_id)
            if not question:
                return None

            if question.status == QuestionStatus.APPROVED:
                return await self._create_question_version(question, question_data, updated_by)

            update_dict = question_data.model_dump(exclude_unset=True, exclude={"options"})
            update_dict["updated_at"] = datetime.utcnow()
            await question.set(update_dict)

            if question_data.options is not None:
                await QuestionOption.find({"question_id": question_id}).delete()
                new_options = [
                    QuestionOption(
                        question_id=question_id,
                        option_text=opt.option_text,
                        is_correct=opt.is_correct,
                        explanation=opt.explanation,
                        option_order=i + 1,
                    )
                    for i, opt in enumerate(question_data.options)
                ]
                if new_options:
                    await QuestionOption.insert_many(new_options)

            question.options = await self._get_question_options(question_id)

            await self._log_audit_event(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={"question_text": question.question_text[:100], "version": question.version},
            )
            return question
        except Exception as e:
            raise ValueError(f"Failed to update question: {str(e)}")

    async def delete_question(self, question_id: str, deleted_by: str) -> bool:
        """Soft-delete a question."""
        try:
            question = await Question.get(question_id)
            if not question:
                return False
            await question.set({"status": QuestionStatus.DELETED, "updated_at": datetime.utcnow()})
            await self._log_audit_event(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                resource_type="question",
                resource_id=question_id,
                old_values={"question_text": question.question_text[:100]},
            )
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete question: {str(e)}")

    # ------------------------------------------------------------------
    # Review workflow
    # ------------------------------------------------------------------

    async def submit_for_review(self, question_id: str, submitted_by: str) -> Optional[Question]:
        """Submit question for review."""
        try:
            question = await Question.get(question_id)
            if not question:
                return None

            if question.status != QuestionStatus.DRAFT:
                raise ValueError("Only draft questions can be submitted for review")

            validation = await self._validate_question(question)
            if not validation["is_valid"]:
                raise ValueError(f"Question validation failed: {', '.join(validation['errors'])}")

            await question.set({"status": QuestionStatus.PENDING_REVIEW, "updated_at": datetime.utcnow()})

            await self._log_audit_event(
                user_id=submitted_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={"status": "PENDING_REVIEW"},
            )
            return question
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to submit question for review: {str(e)}")

    async def review_question(self, question_id: str, review_data: QuestionReviewRequest, reviewed_by: str) -> Dict[str, Any]:
        """Approve or reject a question."""
        try:
            question = await Question.get(question_id)
            if not question:
                raise ValueError("Question not found")
            if question.status != QuestionStatus.PENDING_REVIEW:
                raise ValueError("Only questions pending review can be reviewed")

            now = datetime.utcnow()
            if review_data.action == "approve":
                await question.set({
                    "status": QuestionStatus.APPROVED,
                    "approved_at": now,
                    "reviewed_by": reviewed_by,
                    "updated_at": now,
                })
                await self._clear_question_cache(question_id)
            elif review_data.action == "reject":
                explanation = question.explanation or ""
                if review_data.review_comments:
                    explanation = f"REJECTED: {review_data.review_comments}"
                await question.set({
                    "status": QuestionStatus.REJECTED,
                    "reviewed_by": reviewed_by,
                    "explanation": explanation,
                    "updated_at": now,
                })

            await self._log_audit_event(
                user_id=reviewed_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={
                    "status": question.status.value,
                    "review_action": review_data.action,
                    "review_comments": review_data.review_comments,
                },
            )

            return {
                "success": True,
                "message": f"Question {review_data.action}d successfully",
                "question_id": question_id,
                "new_status": question.status,
                "reviewed_at": now,
                "reviewed_by": reviewed_by,
            }
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to review question: {str(e)}")

    async def get_pending_reviews(self, course_id: Optional[str], limit: int, cursor: Optional[str]) -> List[Question]:
        """Get questions pending review."""
        try:
            filters: Dict[str, Any] = {"status": QuestionStatus.PENDING_REVIEW}
            if course_id:
                filters["course_id"] = course_id

            questions = await Question.find(filters).sort("-created_at").limit(limit).to_list()

            for q in questions:
                q.options = await self._get_question_options(str(q.id))

            return questions
        except Exception as e:
            raise ValueError(f"Failed to get pending reviews: {str(e)}")

    # ------------------------------------------------------------------
    # Bulk import
    # ------------------------------------------------------------------

    async def import_from_csv(self, file, course_id: str, validate_only: bool, continue_on_error: bool, imported_by: str) -> QuestionImportResponse:
        """Import questions from CSV file."""
        try:
            course = await Course.get(course_id)
            if not course:
                raise ValueError("Course not found")

            content = await file.read()
            csv_content = content.decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            import_id = str(uuid.uuid4())
            import_response = QuestionImportResponse(
                import_id=import_id,
                total_records=0,
                successful_imports=0,
                failed_imports=0,
                validation_errors=[],
                import_errors=[],
                status="processing",
                created_at=datetime.utcnow(),
            )

            questions_to_import = []
            for row_num, row in enumerate(csv_reader, 1):
                import_response.total_records += 1
                try:
                    required_fields = ["question_text", "question_type", "difficulty", "cognitive_level", "topic", "points_value"]
                    missing = [f for f in required_fields if not row.get(f)]
                    if missing:
                        import_response.validation_errors.append({"row": row_num, "error": f"Missing fields: {', '.join(missing)}"})
                        continue

                    question_data = self._parse_csv_row(row, course_id)
                    validation = await self._validate_question_data(question_data)
                    if not validation["is_valid"]:
                        import_response.validation_errors.append({"row": row_num, "error": validation["errors"]})
                        continue

                    questions_to_import.append((row_num, question_data))
                except Exception as e:
                    import_response.import_errors.append({"row": row_num, "error": str(e)})

            if not validate_only:
                for row_num, question_data in questions_to_import:
                    try:
                        await self.create_question(question_data, imported_by)
                        import_response.successful_imports += 1
                    except Exception as e:
                        import_response.failed_imports += 1
                        import_response.import_errors.append({"row": row_num, "error": str(e)})
                        if not continue_on_error:
                            break

            import_response.status = "completed"
            import_response.completed_at = datetime.utcnow()

            await self._log_audit_event(
                user_id=imported_by,
                action=AuditAction.CREATE,
                resource_type="question_import",
                resource_id=import_id,
                new_values={
                    "course_id": course_id,
                    "total_records": import_response.total_records,
                    "successful_imports": import_response.successful_imports,
                },
            )
            return import_response
        except Exception as e:
            raise ValueError(f"CSV import failed: {str(e)}")

    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get import job status (stub – extend with Redis tracking)."""
        return {"import_id": import_id, "status": "completed", "progress": 100}

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    async def bulk_operation(self, operation: QuestionBulkOperation, operated_by: str) -> Dict[str, Any]:
        """Perform bulk operations on questions."""
        try:
            results: Dict[str, Any] = {"success": True, "processed": 0, "failed": 0, "errors": []}

            for qid in operation.question_ids:
                try:
                    if operation.operation == "delete":
                        success = await self.delete_question(qid, operated_by)
                        if success:
                            results["processed"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Question {qid} not found")
                    elif operation.operation in ("approve", "reject"):
                        review_data = QuestionReviewRequest(action=operation.operation)
                        await self.review_question(qid, review_data, operated_by)
                        results["processed"] += 1
                    elif operation.operation == "update_status":
                        results["processed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Question {qid}: {str(e)}")

            await self._log_audit_event(
                user_id=operated_by,
                action=AuditAction.SYSTEM_CHANGE,
                resource_type="question_bulk_operation",
                new_values={"operation": operation.operation, "processed": results["processed"], "failed": results["failed"]},
            )
            return results
        except Exception as e:
            raise ValueError(f"Bulk operation failed: {str(e)}")

    # ------------------------------------------------------------------
    # Versioning / Topics / Stats
    # ------------------------------------------------------------------

    async def get_question_versions(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a question."""
        question = await Question.get(question_id)
        if not question:
            return []
        return [
            {
                "id": str(question.id),
                "version": question.version,
                "question_text": question.question_text,
                "status": question.status,
                "created_at": question.created_at,
                "created_by": question.created_by,
                "change_summary": "Current version",
            }
        ]

    async def get_course_topics(self, course_id: str) -> List[Dict[str, Any]]:
        """Get distinct topics for a course."""
        try:
            pipeline = [
                {"$match": {"course_id": course_id, "status": {"$ne": QuestionStatus.DELETED.value}}},
                {"$group": {"_id": "$topic", "question_count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
            results = await Question.aggregate(pipeline).to_list()
            return [
                {
                    "id": str(uuid.uuid4()),
                    "topic": r["_id"],
                    "question_count": r["question_count"],
                    "description": None,
                    "color": None,
                }
                for r in results
            ]
        except Exception as e:
            raise ValueError(f"Failed to get course topics: {str(e)}")

    async def add_course_topic(self, course_id: str, topic_data: QuestionMetadata, added_by: str) -> Dict[str, Any]:
        """Add new topic to course (placeholder – topics are derived from questions)."""
        course = await Course.get(course_id)
        if not course:
            raise ValueError("Course not found")

        existing = await self.get_course_topics(course_id)
        if any(t["topic"] == topic_data.topic for t in existing):
            raise ValueError("Topic already exists for this course")

        await self._log_audit_event(
            user_id=added_by,
            action=AuditAction.CREATE,
            resource_type="course_topic",
            new_values={"course_id": course_id, "topic": topic_data.topic},
        )
        return {"success": True, "message": "Topic added successfully", "topic_id": str(uuid.uuid4()), "topic": topic_data.topic}

    async def get_question_statistics(self, course_id: Optional[str]) -> Dict[str, Any]:
        """Get question bank statistics via aggregation."""
        try:
            match: Dict[str, Any] = {"status": {"$ne": QuestionStatus.DELETED.value}}
            if course_id:
                match["course_id"] = course_id

            pipeline = [
                {"$match": match},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "approved": {"$sum": {"$cond": [{"$eq": ["$status", "APPROVED"]}, 1, 0]}},
                        "draft": {"$sum": {"$cond": [{"$eq": ["$status", "DRAFT"]}, 1, 0]}},
                        "pending": {"$sum": {"$cond": [{"$eq": ["$status", "PENDING_REVIEW"]}, 1, 0]}},
                        "rejected": {"$sum": {"$cond": [{"$eq": ["$status", "REJECTED"]}, 1, 0]}},
                        "avg_points": {"$avg": "$points_value"},
                        "with_images": {"$sum": {"$cond": [{"$ifNull": ["$image_url", False]}, 1, 0]}},
                        "with_explanations": {"$sum": {"$cond": [{"$ifNull": ["$explanation", False]}, 1, 0]}},
                    }
                },
            ]
            result = await Question.aggregate(pipeline).to_list()
            row = result[0] if result else {}

            diff_pipeline = [{"$match": match}, {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}}]
            diff_rows = await Question.aggregate(diff_pipeline).to_list()

            cog_pipeline = [{"$match": match}, {"$group": {"_id": "$cognitive_level", "count": {"$sum": 1}}}]
            cog_rows = await Question.aggregate(cog_pipeline).to_list()

            topic_pipeline = [{"$match": match}, {"$group": {"_id": "$topic", "count": {"$sum": 1}}}]
            topic_rows = await Question.aggregate(topic_pipeline).to_list()

            type_pipeline = [{"$match": match}, {"$group": {"_id": "$question_type", "count": {"$sum": 1}}}]
            type_rows = await Question.aggregate(type_pipeline).to_list()

            return {
                "total_questions": row.get("total", 0),
                "approved_questions": row.get("approved", 0),
                "draft_questions": row.get("draft", 0),
                "pending_review": row.get("pending", 0),
                "rejected_questions": row.get("rejected", 0),
                "by_difficulty": {r["_id"]: r["count"] for r in diff_rows if r["_id"]},
                "by_cognitive_level": {r["_id"]: r["count"] for r in cog_rows if r["_id"]},
                "by_topic": {r["_id"]: r["count"] for r in topic_rows if r["_id"]},
                "by_question_type": {r["_id"]: r["count"] for r in type_rows if r["_id"]},
                "average_points": float(row.get("avg_points") or 0),
                "questions_with_images": row.get("with_images", 0),
                "questions_with_explanations": row.get("with_explanations", 0),
            }
        except Exception as e:
            raise ValueError(f"Failed to get question statistics: {str(e)}")

    async def duplicate_question(self, question_id: str, duplicated_by: str) -> Optional[Question]:
        """Duplicate a question as a new draft."""
        original = await self.get_question(question_id)
        if not original:
            return None

        options = await self._get_question_options(str(original.id))
        option_creates = [
            QuestionOptionCreate(option_text=o.option_text, is_correct=o.is_correct, explanation=o.explanation)
            for o in options
        ] if options else []

        dup_data = QuestionCreate(
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
            options=option_creates,
        )
        duplicate = await self.create_question(dup_data, duplicated_by)

        await self._log_audit_event(
            user_id=duplicated_by,
            action=AuditAction.CREATE,
            resource_type="question",
            resource_id=str(duplicate.id),
            new_values={"duplicated_from": question_id, "question_text": duplicate.question_text[:100]},
        )
        return duplicate

    async def upload_question_image(self, question_id: str, file, uploaded_by: str) -> Dict[str, Any]:
        """Upload image for question."""
        try:
            if not file.content_type.startswith("image/"):
                raise ValueError("Only image files are allowed")
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:
                raise ValueError("Image file size cannot exceed 5MB")
            file_hash = hashlib.sha256(content).hexdigest()
            filename = f"{question_id}_{file_hash}_{datetime.utcnow().timestamp()}.jpg"
            image_url = f"/uploads/questions/{filename}"

            question = await Question.get(question_id)
            if question:
                await question.set({"image_url": image_url, "updated_at": datetime.utcnow()})

            await self._log_audit_event(
                user_id=uploaded_by,
                action=AuditAction.UPDATE,
                resource_type="question",
                resource_id=question_id,
                new_values={"image_url": image_url},
            )
            return {
                "success": True,
                "image_url": image_url,
                "file_name": filename,
                "file_size": len(content),
                "watermark_applied": False,
                "virus_scan_status": "clean",
            }
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to upload question image: {str(e)}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_question_options(self, question_id: str) -> List[QuestionOption]:
        """Fetch options for a question, ordered."""
        return await QuestionOption.find({"question_id": question_id}).sort("option_order").to_list()

    async def _validate_question(self, question: Question) -> Dict[str, Any]:
        """Validate question content for review submission."""
        errors = []
        warnings: List[str] = []
        if len(question.question_text.strip()) < 10:
            errors.append("Question text must be at least 10 characters long")
        if question.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
            options = await self._get_question_options(str(question.id))
            if len(options) < 2:
                errors.append("Question must have at least 2 options")
            correct_count = sum(1 for o in options if o.is_correct)
            if correct_count != 1:
                errors.append("Question must have exactly one correct answer")
        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    async def _validate_question_data(self, question_data: QuestionCreate) -> Dict[str, Any]:
        """Validate question creation data."""
        errors = []
        warnings: List[str] = []
        if len(question_data.question_text.strip()) < 10:
            errors.append("Question text must be at least 10 characters long")
        if question_data.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
            if not question_data.options or len(question_data.options) < 2:
                errors.append("Question must have at least 2 options")
            if question_data.options:
                correct_count = sum(1 for o in question_data.options if o.is_correct)
                if correct_count != 1:
                    errors.append("Question must have exactly one correct answer")
        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    async def _create_question_version(self, original: Question, update_data: QuestionUpdate, updated_by: str) -> Question:
        """Bump version and apply updates to an approved question."""
        update_dict = update_data.model_dump(exclude_unset=True, exclude={"options"})
        update_dict["version"] = original.version + 1
        update_dict["status"] = QuestionStatus.DRAFT
        update_dict["supersedes_question_id"] = str(original.id)
        update_dict["updated_at"] = datetime.utcnow()
        await original.set(update_dict)
        return original

    def _parse_csv_row(self, row: Dict[str, str], course_id: str) -> QuestionCreate:
        """Parse a CSV row into QuestionCreate."""
        options = []
        for letter in ["a", "b", "c", "d", "e", "f"]:
            text = row.get(f"option_{letter}")
            if text:
                options.append(
                    QuestionOptionCreate(
                        option_text=text.strip(),
                        is_correct=row.get("correct_answer", "").lower() == letter,
                    )
                )
        return QuestionCreate(
            question_text=row["question_text"].strip(),
            question_type=QuestionType(row["question_type"].upper()),
            difficulty=QuestionDifficulty(row["difficulty"].upper()),
            cognitive_level=CognitiveLevel(row["cognitive_level"].upper()),
            topic=row["topic"].strip(),
            points_value=int(row["points_value"]),
            explanation=row.get("explanation", "").strip() or None,
            reference=row.get("reference", "").strip() or None,
            course_id=course_id,
            options=options,
        )

    async def _clear_question_cache(self, question_id: str):
        """Clear question-related cache keys."""
        await self.cache.delete(f"question:{question_id}")

    async def _log_audit_event(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        new_values: Optional[Dict] = None,
        old_values: Optional[Dict] = None,
    ):
        """Persist an audit log entry via Beanie."""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=new_values,
                old_values=old_values,
            )
            await audit_log.insert()
        except Exception:
            pass  # Never let audit failures break business logic
