"""
Examination service for exam management, grading, and monitoring.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload

from ..models.exam import (
    Examination, ExamStatus, ExamInstance, ExamInstanceStatus,
    ExamQuestion, ExamAnswer
)
from ..models.question import Question, QuestionOption
from ..models.student import Student
from ..models.academic import Course
from ..services.audit_service import AuditService, AuditAction
from ..core.security import security
from ..schemas.exam import ExamStartResponse, ExamSubmissionResponse, ExamReviewResponse

class ExamService:
    """Examination management service."""
    
    def __init__(self, db: Any):
        self.db = db
        self.security = security
    
    async def create_examination(self, exam_data, created_by: str) -> Examination:
        """Create a new examination."""
        try:
            # Validate course exists
            course_result = await self.db.execute(
                select(Course).where(Course.id == exam_data.course_id)
            )
            if not course_result.scalar_one_or_none():
                raise ValueError("Course not found")
            
            # Create examination
            exam = Examination(
                id=str(uuid.uuid4()),
                title=exam_data.title,
                description=exam_data.description,
                exam_date=exam_data.exam_date,
                start_time=exam_data.start_time,
                duration_minutes=exam_data.duration_minutes,
                total_points=exam_data.total_points,
                pass_points=exam_data.pass_points,
                randomize_questions=exam_data.randomize_questions,
                randomize_options=exam_data.randomize_options,
                allow_review=exam_data.allow_review,
                show_results_immediately=exam_data.show_results_immediately,
                max_attempts=exam_data.max_attempts,
                status=ExamStatus.DRAFT,
                course_id=exam_data.course_id,
                academic_session_id=exam_data.academic_session_id,
                semester_id=exam_data.semester_id,
                created_by=created_by
            )
            
            self.db.add(exam)
            await self.db.commit()
            await self.db.refresh(exam)
            
            # Add questions to exam
            if exam_data.question_ids:
                await self._add_questions_to_exam(exam.id, exam_data.question_ids, exam_data.question_order)
            
            # Log creation
            await self._log_audit_event(
                user_id=created_by,
                action=AuditAction.CREATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"title": exam.title, "course_id": exam.course_id}
            )
            
            return exam
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create examination: {str(e)}")
    
    async def list_examinations(self, course_id: Optional[str] = None,
                               academic_session_id: Optional[str] = None,
                               status: Optional[ExamStatus] = None,
                               limit: int = 50, cursor: Optional[str] = None) -> List[Examination]:
        """List examinations with filtering."""
        try:
            query = select(Examination)
            
            # Apply filters
            if course_id:
                query = query.where(Examination.course_id == course_id)
            
            if academic_session_id:
                query = query.where(Examination.academic_session_id == academic_session_id)
            
            if status:
                query = query.where(Examination.status == status)
            
            # Apply pagination
            query = query.limit(limit)
            if cursor:
                query = query.where(Examination.id > cursor)
            
            # Order by creation date (newest first)
            query = query.order_by(Examination.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to list examinations: {str(e)}")
    
    async def get_examination(self, exam_id: str) -> Optional[Examination]:
        """Get examination by ID."""
        try:
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"Failed to get examination: {str(e)}")
    
    async def update_examination(self, exam_id: str, exam_data, updated_by: str) -> Optional[Examination]:
        """Update examination."""
        try:
            # Get existing exam
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if not exam:
                return None
            
            # Update fields
            old_values = exam.to_dict()
            
            for field, value in exam_data.dict(exclude_unset=True).items():
                if hasattr(exam, field):
                    setattr(exam, field, value)
            
            exam.updated_at = datetime.utcnow()
            exam.updated_by = updated_by
            
            await self.db.commit()
            await self.db.refresh(exam)
            
            # Log update
            await self._log_audit_event(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                old_values=old_values,
                new_values=exam.to_dict()
            )
            
            return exam
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update examination: {str(e)}")
    
    async def delete_examination(self, exam_id: str, deleted_by: str) -> bool:
        """Delete examination (soft delete)."""
        try:
            # Get existing exam
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if not exam:
                return False
            
            # Soft delete
            exam.is_active = False
            exam.updated_at = datetime.utcnow()
            exam.updated_by = deleted_by
            
            await self.db.commit()
            
            # Log deletion
            await self._log_audit_event(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                resource_type="examination",
                resource_id=exam.id,
                old_values={"title": exam.title, "course_id": exam.course_id}
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete examination: {str(e)}")
    
    async def schedule_examination(self, exam_id: str, schedule_data, scheduled_by: str) -> Optional[Examination]:
        """Schedule examination for specific date and time."""
        try:
            # Get existing exam
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if not exam:
                return None
            
            # Update scheduling
            exam.exam_date = schedule_data.get('exam_date', exam.exam_date)
            exam.start_time = schedule_data.get('start_time', exam.start_time)
            exam.duration_minutes = schedule_data.get('duration_minutes', exam.duration_minutes)
            exam.status = ExamStatus.SCHEDULED
            exam.updated_at = datetime.utcnow()
            exam.updated_by = scheduled_by
            
            await self.db.commit()
            await self.db.refresh(exam)
            
            # Log scheduling
            await self._log_audit_event(
                user_id=scheduled_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={
                    "status": "SCHEDULED",
                    "exam_date": exam.exam_date,
                    "start_time": exam.start_time
                }
            )
            
            return exam
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to schedule examination: {str(e)}")
    
    async def publish_examination(self, exam_id: str, published_by: str) -> Optional[Examination]:
        """Publish examination for students."""
        try:
            # Get existing exam
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if not exam:
                return None
            
            # Check if exam is ready to publish
            if exam.status != ExamStatus.SCHEDULED:
                raise ValueError("Examination must be scheduled before publishing")
            
            # Update status
            exam.status = ExamStatus.ACTIVE
            exam.updated_at = datetime.utcnow()
            exam.updated_by = published_by
            
            await self.db.commit()
            await self.db.refresh(exam)
            
            # Log publishing
            await self._log_audit_event(
                user_id=published_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"status": "ACTIVE"}
            )
            
            return exam
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to publish examination: {str(e)}")
    
    async def cancel_examination(self, exam_id: str, reason: str, cancelled_by: str) -> Optional[Examination]:
        """Cancel examination."""
        try:
            # Get existing exam
            result = await self.db.execute(
                select(Examination).where(Examination.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if not exam:
                return None
            
            # Update status
            exam.status = ExamStatus.CANCELLED
            exam.updated_at = datetime.utcnow()
            exam.updated_by = cancelled_by
            
            await self.db.commit()
            await self.db.refresh(exam)
            
            # Log cancellation
            await self._log_audit_event(
                user_id=cancelled_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"status": "CANCELLED", "reason": reason}
            )
            
            return exam
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to cancel examination: {str(e)}")
    
    async def list_exam_instances(self, exam_id: str, status: Optional[ExamInstanceStatus] = None,
                                limit: int = 50, cursor: Optional[str] = None) -> List[ExamInstance]:
        """List exam instances for an examination."""
        try:
            query = select(ExamInstance).where(ExamInstance.examination_id == exam_id)
            
            if status:
                query = query.where(ExamInstance.status == status)
            
            query = query.limit(limit)
            if cursor:
                query = query.where(ExamInstance.id > cursor)
            
            query = query.order_by(ExamInstance.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to list exam instances: {str(e)}")
    
    async def get_exam_instance(self, instance_id: str) -> Optional[ExamInstance]:
        """Get exam instance by ID."""
        try:
            result = await self.db.execute(
                select(ExamInstance).where(ExamInstance.id == instance_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"Failed to get exam instance: {str(e)}")
    
    async def start_exam(self, exam_id: str, student_id: str, started_by: str) -> ExamStartResponse:
        """Start exam for student."""
        try:
            # Get exam
            exam = await self.get_examination(exam_id)
            if not exam:
                return ExamStartResponse(
                    success=False,
                    message="Examination not found"
                )
            
            # Check if exam is active
            if exam.status != ExamStatus.ACTIVE:
                return ExamStartResponse(
                    success=False,
                    message=f"Examination is not active (status: {exam.status.value})"
                )
            
            # Check if exam time is valid
            now = datetime.utcnow()
            exam_start = exam.start_time
            exam_end = exam.start_time + timedelta(minutes=exam.duration_minutes)
            
            if now < exam_start:
                return ExamStartResponse(
                    success=False,
                    message="Examination has not started yet"
                )
            
            if now > exam_end:
                return ExamStartResponse(
                    success=False,
                    message="Examination has ended"
                )
            
            # Check if student has existing instance
            existing_result = await self.db.execute(
                select(ExamInstance).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.student_id == student_id,
                        ExamInstance.status.in_([ExamInstanceStatus.NOT_STARTED, ExamInstanceStatus.IN_PROGRESS])
                    )
                )
            )
            existing_instance = existing_result.scalar_one_or_none()
            if existing_instance:
                return ExamStartResponse(
                    success=False,
                    message="Student already has an active exam instance"
                )
            
            # Check if student has exceeded max attempts
            attempts_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.student_id == student_id,
                        ExamInstance.status == ExamInstanceStatus.SUBMITTED
                    )
                )
            )
            attempts_count = attempts_result.scalar() or 0
            if attempts_count >= exam.max_attempts:
                return ExamStartResponse(
                    success=False,
                    message=f"Maximum attempts ({exam.max_attempts}) exceeded"
                )
            
            # Create exam instance
            instance = ExamInstance(
                id=str(uuid.uuid4()),
                examination_id=exam_id,
                student_id=student_id,
                start_time=now,
                status=ExamInstanceStatus.NOT_STARTED,
                total_points_possible=exam.total_points
            )
            
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)
            
            # Get exam questions
            questions = await self._get_exam_questions(exam_id)
            
            # Log exam start
            await self._log_audit_event(
                user_id=student_id,
                action=AuditAction.EXAM_START,
                resource_type="exam_instance",
                resource_id=instance.id,
                new_values={"examination_id": exam_id, "start_time": now}
            )
            
            return ExamStartResponse(
                success=True,
                message="Exam started successfully",
                instance_id=instance.id,
                start_time=instance.start_time,
                end_time=exam_end,
                duration_minutes=exam.duration_minutes,
                question_count=len(questions),
                total_points=exam.total_points,
                biometric_required=False  # Would be determined by exam settings
            )
            
        except Exception as e:
            await self.db.rollback()
            return ExamStartResponse(
                success=False,
                message=f"Failed to start exam: {str(e)}"
            )
    
    async def submit_exam(self, instance_id: str, submission_data, submitted_by: str) -> ExamSubmissionResponse:
        """Submit exam answers."""
        try:
            # Get instance
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                return ExamSubmissionResponse(
                    success=False,
                    message="Exam instance not found"
                )
            
            # Check if instance can be submitted
            if instance.status != ExamInstanceStatus.IN_PROGRESS:
                return ExamSubmissionResponse(
                    success=False,
                    message=f"Exam cannot be submitted (status: {instance.status.value})"
                )
            
            # Get exam
            exam = await self.get_examination(instance.examination_id)
            if not exam:
                return ExamSubmissionResponse(
                    success=False,
                    message="Examination not found"
                )
            
            # Calculate score
            total_points_earned = 0
            processed_answers = 0
            
            for answer_data in submission_data.answers:
                # Validate and process each answer
                question_id = answer_data.get('question_id')
                selected_option_id = answer_data.get('selected_option_id')
                answer_text = answer_data.get('answer_text')
                
                # Get question and correct answer
                question_result = await self.db.execute(
                    select(Question).where(Question.id == question_id)
                )
                question = question_result.scalar_one_or_none()
                
                if not question:
                    continue
                
                # Calculate points for this answer
                points_earned = await self._calculate_answer_points(
                    question, selected_option_id, answer_text
                )
                
                total_points_earned += points_earned
                processed_answers += 1
            
            # Update instance
            instance.end_time = submission_data.submission_time
            instance.status = ExamInstanceStatus.SUBMITTED
            instance.total_points_earned = total_points_earned
            instance.percentage_score = (total_points_earned / instance.total_points_possible) * 100 if instance.total_points_possible > 0 else 0
            
            # Calculate grade
            instance.grade = self._calculate_grade(instance.percentage_score)
            
            await self.db.commit()
            
            # Log submission
            await self._log_audit_event(
                user_id=instance.student_id,
                action=AuditAction.EXAM_SUBMIT,
                resource_type="exam_instance",
                resource_id=instance.id,
                new_values={
                    "total_points_earned": total_points_earned,
                    "percentage_score": instance.percentage_score,
                    "grade": instance.grade
                }
            )
            
            return ExamSubmissionResponse(
                success=True,
                message="Exam submitted successfully",
                instance_id=instance.id,
                submission_time=instance.end_time,
                total_answers=processed_answers,
                points_earned=total_points_earned,
                percentage_score=instance.percentage_score,
                grade=instance.grade
            )
            
        except Exception as e:
            await self.db.rollback()
            return ExamSubmissionResponse(
                success=False,
                message=f"Failed to submit exam: {str(e)}"
            )
    
    async def review_exam(self, instance_id: str, reviewed_by: str) -> Optional[ExamReviewResponse]:
        """Review submitted exam."""
        try:
            # Get instance with exam and student
            result = await self.db.execute(
                select(ExamInstance)
                .options(selectinload(ExamInstance.examination), selectinload(ExamInstance.student))
                .where(ExamInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            
            if not instance or instance.status != ExamInstanceStatus.SUBMITTED:
                return None
            
            # Get exam answers
            answers_result = await self.db.execute(
                select(ExamAnswer)
                .options(selectinload(ExamAnswer.question).selectinload(ExamAnswer.selected_option))
                .where(ExamAnswer.exam_instance_id == instance_id)
            )
            answers = answers_result.scalars().all()
            
            # Process answers
            correct_answers = 0
            incorrect_answers = 0
            unanswered = 0
            processed_answers = []
            
            for answer in answers:
                if answer.selected_option_id or answer.answer_text:
                    is_correct = await self._is_answer_correct(answer)
                    if is_correct:
                        correct_answers += 1
                    else:
                        incorrect_answers += 1
                else:
                    unanswered += 1
                
                processed_answers.append({
                    "question_id": answer.question_id,
                    "question_text": answer.question.question_text if answer.question else "",
                    "selected_option_id": answer.selected_option_id,
                    "answer_text": answer.answer_text,
                    "is_correct": is_correct if answer.selected_option_id or answer.answer_text else None,
                    "points_earned": answer.points_earned,
                    "time_spent": answer.time_spent_seconds
                })
            
            return ExamReviewResponse(
                instance_id=instance.id,
                exam_title=instance.examination.title if instance.examination else "",
                student_name=instance.student.full_name if instance.student else "",
                start_time=instance.start_time,
                end_time=instance.end_time,
                duration_taken=instance.duration_taken,
                total_points=instance.total_points_possible,
                points_earned=instance.total_points_earned,
                percentage_score=instance.percentage_score or 0,
                grade=instance.grade or "",
                passed=instance.is_passed,
                answers=processed_answers,
                correct_answers=correct_answers,
                incorrect_answers=incorrect_answers,
                unanswered=unanswered,
                time_per_question=[]  # Would calculate from answer data
            )
            
        except Exception as e:
            raise ValueError(f"Failed to review exam: {str(e)}")
    
    async def get_exam_statistics(self, exam_id: str) -> Dict[str, Any]:
        """Get examination statistics."""
        try:
            # Get exam
            exam = await self.get_examination(exam_id)
            if not exam:
                raise ValueError("Examination not found")
            
            # Get instance statistics
            total_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(ExamInstance.examination_id == exam_id)
            )
            total_instances = total_result.scalar() or 0
            
            completed_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.status == ExamInstanceStatus.SUBMITTED
                    )
                )
            )
            completed_instances = completed_result.scalar() or 0
            
            in_progress_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.status == ExamInstanceStatus.IN_PROGRESS
                    )
                )
            )
            in_progress_instances = in_progress_result.scalar() or 0
            
            not_started_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.status == ExamInstanceStatus.NOT_STARTED
                    )
                )
            )
            not_started_instances = not_started_result.scalar() or 0
            
            # Calculate statistics
            avg_score_result = await self.db.execute(
                select(func.avg(ExamInstance.percentage_score)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.percentage_score.isnot(None)
                    )
                )
            )
            average_score = avg_score_result.scalar() or 0
            
            highest_score_result = await self.db.execute(
                select(func.max(ExamInstance.percentage_score)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.percentage_score.isnot(None)
                    )
                )
            )
            highest_score = highest_score_result.scalar() or 0
            
            lowest_score_result = await self.db.execute(
                select(func.min(ExamInstance.percentage_score)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.percentage_score.isnot(None)
                    )
                )
            )
            lowest_score = lowest_score_result.scalar() or 0
            
            pass_rate = (completed_instances / total_instances * 100) if total_instances > 0 else 0
            
            completion_rate = (completed_instances / total_instances * 100) if total_instances > 0 else 0
            
            return {
                "exam_id": exam_id,
                "exam_title": exam.title,
                "total_instances": total_instances,
                "completed_instances": completed_instances,
                "in_progress_instances": in_progress_instances,
                "not_started_instances": not_started_instances,
                "average_score": average_score,
                "highest_score": highest_score,
                "lowest_score": lowest_score,
                "pass_rate": pass_rate,
                "completion_rate": completion_rate,
                "score_distribution": {},  # Would be calculated from actual scores
                "time_distribution": {}  # Would be calculated from actual durations
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get exam statistics: {str(e)}")
    
    async def get_exam_results(self, exam_id: str, format: str = "summary") -> Dict[str, Any]:
        """Get examination results."""
        try:
            if format == "summary":
                return await self.get_exam_statistics(exam_id)
            elif format == "detailed":
                return await self._get_detailed_results(exam_id)
            else:
                raise ValueError(f"Invalid format: {format}")
        except Exception as e:
            raise ValueError(f"Failed to get exam results: {str(e)}")
    
    async def grade_exam(self, exam_id: str, graded_by: str) -> Dict[str, Any]:
        """Grade all submitted exam instances."""
        try:
            # Get exam
            exam = await self.get_examination(exam_id)
            if not exam:
                raise ValueError("Examination not found")
            
            # Get submitted instances
            instances_result = await self.db.execute(
                select(ExamInstance).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.status == ExamInstanceStatus.SUBMITTED
                    )
                )
            )
            instances = instances_result.scalars().all()
            
            graded_count = 0
            grading_errors = []
            
            for instance in instances:
                try:
                    # Grade individual instance
                    await self._grade_instance(instance)
                    graded_count += 1
                except Exception as e:
                    grading_errors.append(f"Instance {instance.id}: {str(e)}")
            
            # Calculate statistics
            avg_score_result = await self.db.execute(
                select(func.avg(ExamInstance.percentage_score)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.percentage_score.isnot(None)
                    )
                )
            )
            average_score = avg_score_result.scalar() or 0
            
            pass_rate_result = await self.db.execute(
                select(func.count(ExamInstance.id)).where(
                    and_(
                        ExamInstance.examination_id == exam_id,
                        ExamInstance.grade.isnot(None)
                    )
                )
            )
            passed_count = pass_rate_result.scalar() or 0
            pass_rate = (passed_count / len(instances) * 100) if instances else 0
            
            return {
                "success": len(grading_errors) == 0,
                "message": f"Graded {graded_count} instances" if len(grading_errors) == 0 else f"Graded {graded_count} instances with {len(grading_errors)} errors",
                "total_graded": graded_count,
                "grading_errors": grading_errors,
                "average_score": average_score,
                "pass_rate": pass_rate,
                "grade_distribution": {}  # Would be calculated from actual grades
            }
            
        except Exception as e:
            raise ValueError(f"Failed to grade exam: {str(e)}")
    
    async def publish_results(self, exam_id: str, published_by: str) -> Dict[str, Any]:
        """Publish examination results."""
        try:
            # Get exam
            exam = await self.get_examination(exam_id)
            if not exam:
                raise ValueError("Examination not found")
            
            # Update exam to show results
            if not exam.show_results_immediately:
                exam.show_results_immediately = True
                exam.updated_at = datetime.utcnow()
                exam.updated_by = published_by
                await self.db.commit()
            
            # Log publication
            await self._log_audit_event(
                user_id=published_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam_id,
                new_values={"show_results_immediately": True}
            )
            
            return {
                "success": True,
                "message": "Results published successfully",
                "exam_id": exam_id
            }
            
        except Exception as e:
            raise ValueError(f"Failed to publish results: {str(e)}")
    
    # Private helper methods
    
    async def _add_questions_to_exam(self, exam_id: str, question_ids: List[str], question_order: Optional[List[str]]):
        """Add questions to examination."""
        for i, question_id in enumerate(question_ids):
            order = question_order.index(question_id) + 1 if question_order else i + 1
            
            exam_question = ExamQuestion(
                id=str(uuid.uuid4()),
                examination_id=exam_id,
                question_id=question_id,
                question_order=order
            )
            
            self.db.add(exam_question)
        
        await self.db.commit()
    
    async def _get_exam_questions(self, exam_id: str) -> List[Question]:
        """Get questions for examination."""
        result = await self.db.execute(
            select(Question)
            .join(ExamQuestion, Question.id == ExamQuestion.question_id)
            .where(ExamQuestion.examination_id == exam_id)
            .order_by(ExamQuestion.question_order)
        )
        return result.scalars().all()
    
    async def _calculate_answer_points(self, question, selected_option_id: str, answer_text: str) -> int:
        """Calculate points earned for answer."""
        # Get correct answer
        if question.question_type.value == "MULTIPLE_CHOICE":
            # For MCQ, check if selected option is correct
            result = await self.db.execute(
                select(QuestionOption).where(
                    and_(
                        QuestionOption.question_id == question.id,
                        QuestionOption.is_correct == True
                    )
                )
            )
            correct_option = result.scalar_one_or_none()
            
            if correct_option and selected_option_id == correct_option.id:
                return question.points_value
            return 0
        else:
            # For text answers, this would require AI/manual grading
            # For now, return 0 (would be updated during grading)
            return 0
    
    async def _is_answer_correct(self, answer) -> bool:
        """Check if answer is correct."""
        if answer.selected_option_id:
            # Check MCQ answer
            result = await self.db.execute(
                select(QuestionOption.is_correct).where(
                    QuestionOption.id == answer.selected_option_id
                )
            )
            is_correct = result.scalar()
            return bool(is_correct)
        else:
            # Text answer correctness would be determined during grading
            return None
    
    def _calculate_grade(self, percentage_score: float) -> str:
        """Calculate grade based on percentage score."""
        if percentage_score >= 70:
            return "A"
        elif percentage_score >= 60:
            return "B"
        elif percentage_score >= 50:
            return "C"
        elif percentage_score >= 45:
            return "D"
        else:
            return "F"
    
    async def _grade_instance(self, instance: ExamInstance):
        """Grade individual exam instance."""
        # This would implement detailed grading logic
        # For now, just calculate based on existing points
        if instance.total_points_possible > 0:
            instance.percentage_score = (instance.total_points_earned / instance.total_points_possible) * 100
            instance.grade = self._calculate_grade(instance.percentage_score)
        
        await self.db.commit()
    
    async def _get_detailed_results(self, exam_id: str) -> Dict[str, Any]:
        """Get detailed exam results."""
        # This would return detailed results for all instances
        # For now, return basic structure
        return {"exam_id": exam_id, "results": []}
    
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
