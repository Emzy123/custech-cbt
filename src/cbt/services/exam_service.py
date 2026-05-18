"""Examination service for exam management using Beanie."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from ..models.exam import (
    Examination, ExamStatus, ExamInstance, ExamInstanceStatus, ExamQuestion, ExamAnswer
)
from ..models.question import Question, QuestionOption
from ..models.student import Student
from ..services.audit_service import AuditAction
from ..schemas.exam import ExamStartResponse, ExamSubmissionResponse, ExamReviewResponse
from ..models.security import AuditLog


class ExamService:
    """Examination management service."""

    def __init__(self, db: Any):
        self.db = db
    
    async def create_examination(self, exam_data, created_by: str) -> Examination:
        """Create a new examination."""
        try:
            exam = Examination(
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
            
            await exam.insert()

            if exam_data.question_ids:
                await self._add_questions_to_exam(exam.id, exam_data.question_ids, exam_data.question_order)
            await self._log_audit_event(
                user_id=created_by,
                action=AuditAction.CREATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"title": exam.title, "course_id": exam.course_id}
            )
            return exam
        except Exception as e:
            raise ValueError(f"Failed to create examination: {str(e)}")
    
    async def list_examinations(self, course_id: Optional[str] = None,
                               academic_session_id: Optional[str] = None,
                               status: Optional[ExamStatus] = None,
                               limit: int = 50, cursor: Optional[str] = None) -> List[Examination]:
        """List examinations with filtering."""
        try:
            query = Examination.find(Examination.is_active == True)
            if course_id:
                query = query.find(Examination.course_id == course_id)
            if academic_session_id:
                query = query.find(Examination.academic_session_id == academic_session_id)
            if status:
                query = query.find(Examination.status == status)
            exams = await query.sort("-created_at").limit(limit).to_list()
            if cursor:
                exams = [e for e in exams if e.id > cursor]
            return exams
        except Exception as e:
            raise ValueError(f"Failed to list examinations: {str(e)}")
    
    async def get_examination(self, exam_id: str) -> Optional[Examination]:
        """Get examination by ID."""
        try:
            return await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
        except Exception as e:
            raise ValueError(f"Failed to get examination: {str(e)}")
    
    async def update_examination(self, exam_id: str, exam_data, updated_by: str) -> Optional[Examination]:
        """Update examination."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None

            old_values = exam.model_dump()
            for field, value in exam_data.dict(exclude_unset=True).items():
                if hasattr(exam, field):
                    setattr(exam, field, value)

            exam.updated_at = datetime.now(timezone.utc)
            exam.updated_by = updated_by
            await exam.save()
            await self._log_audit_event(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                old_values=old_values,
                new_values=exam.model_dump()
            )
            return exam
        except Exception as e:
            raise ValueError(f"Failed to update examination: {str(e)}")
    
    async def delete_examination(self, exam_id: str, deleted_by: str) -> bool:
        """Delete examination (soft delete)."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return False
            exam.is_active = False
            exam.updated_at = datetime.now(timezone.utc)
            exam.updated_by = deleted_by
            await exam.save()
            await self._log_audit_event(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                resource_type="examination",
                resource_id=exam.id,
                old_values={"title": exam.title, "course_id": exam.course_id}
            )
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete examination: {str(e)}")
    
    async def schedule_examination(self, exam_id: str, schedule_data, scheduled_by: str) -> Optional[Examination]:
        """Schedule examination for specific date and time."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            exam.exam_date = schedule_data.get('exam_date', exam.exam_date)
            exam.start_time = schedule_data.get('start_time', exam.start_time)
            exam.duration_minutes = schedule_data.get('duration_minutes', exam.duration_minutes)
            exam.status = ExamStatus.SCHEDULED
            exam.updated_at = datetime.now(timezone.utc)
            exam.updated_by = scheduled_by
            await exam.save()
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
            raise ValueError(f"Failed to schedule examination: {str(e)}")
    
    async def publish_examination(self, exam_id: str, published_by: str) -> Optional[Examination]:
        """Publish examination for students."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            if exam.status != ExamStatus.SCHEDULED:
                raise ValueError("Examination must be scheduled before publishing")
            exam.status = ExamStatus.ACTIVE
            exam.updated_at = datetime.now(timezone.utc)
            exam.updated_by = published_by
            await exam.save()
            await self._log_audit_event(
                user_id=published_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"status": "ACTIVE"}
            )
            return exam
        except Exception as e:
            raise ValueError(f"Failed to publish examination: {str(e)}")
    
    async def cancel_examination(self, exam_id: str, reason: str, cancelled_by: str) -> Optional[Examination]:
        """Cancel examination."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            exam.status = ExamStatus.CANCELLED
            exam.updated_at = datetime.now(timezone.utc)
            exam.updated_by = cancelled_by
            await exam.save()
            await self._log_audit_event(
                user_id=cancelled_by,
                action=AuditAction.UPDATE,
                resource_type="examination",
                resource_id=exam.id,
                new_values={"status": "CANCELLED", "reason": reason}
            )
            return exam
        except Exception as e:
            raise ValueError(f"Failed to cancel examination: {str(e)}")
    
    async def list_exam_instances(self, exam_id: str, status: Optional[ExamInstanceStatus] = None,
                                limit: int = 50, cursor: Optional[str] = None) -> List[ExamInstance]:
        """List exam instances for an examination."""
        try:
            query = ExamInstance.find(ExamInstance.examination_id == exam_id, ExamInstance.is_active == True)
            if status:
                query = query.find(ExamInstance.status == status)
            instances = await query.sort("-created_at").limit(limit).to_list()
            if cursor:
                instances = [i for i in instances if i.id > cursor]
            return instances
        except Exception as e:
            raise ValueError(f"Failed to list exam instances: {str(e)}")
    
    async def get_exam_instance(self, instance_id: str) -> Optional[ExamInstance]:
        """Get exam instance by ID."""
        try:
            return await ExamInstance.find_one(ExamInstance.id == instance_id, ExamInstance.is_active == True)
        except Exception as e:
            raise ValueError(f"Failed to get exam instance: {str(e)}")
    
    async def start_exam(self, exam_id: str, student_id: str, started_by: str) -> ExamStartResponse:
        """Start exam for student."""
        try:
            exam = await self.get_examination(exam_id)
            if not exam:
                return ExamStartResponse(
                    success=False,
                    message="Examination not found",
                    instance_id="",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                    duration_minutes=0,
                    question_count=0,
                    total_points=0,
                    biometric_required=False,
                )

            if exam.status != ExamStatus.ACTIVE:
                return ExamStartResponse(
                    success=False,
                    message=f"Examination is not active (status: {exam.status.value})",
                    instance_id="",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                    duration_minutes=0,
                    question_count=0,
                    total_points=0,
                    biometric_required=False,
                )

            now = datetime.now(timezone.utc)
            exam_start = exam.start_time if isinstance(exam.start_time, datetime) else datetime.now(timezone.utc)
            exam_end = exam_start + timedelta(minutes=exam.duration_minutes)
            if now < exam_start:
                return ExamStartResponse(
                    success=False,
                    message="Examination has not started yet",
                    instance_id="",
                    start_time=exam_start,
                    end_time=exam_end,
                    duration_minutes=exam.duration_minutes,
                    question_count=0,
                    total_points=exam.total_points,
                    biometric_required=False,
                )
            if now > exam_end:
                return ExamStartResponse(
                    success=False,
                    message="Examination has ended",
                    instance_id="",
                    start_time=exam_start,
                    end_time=exam_end,
                    duration_minutes=exam.duration_minutes,
                    question_count=0,
                    total_points=exam.total_points,
                    biometric_required=False,
                )

            existing_instance = await ExamInstance.find_one(
                ExamInstance.examination_id == exam_id,
                ExamInstance.student_id == student_id,
                {"status": {"$in": [ExamInstanceStatus.NOT_STARTED, ExamInstanceStatus.IN_PROGRESS]}},
            )
            if existing_instance:
                return ExamStartResponse(
                    success=False,
                    message="Student already has an active exam instance",
                    instance_id=existing_instance.id,
                    start_time=existing_instance.start_time or now,
                    end_time=exam_end,
                    duration_minutes=exam.duration_minutes,
                    question_count=0,
                    total_points=exam.total_points,
                    biometric_required=False,
                )

            attempts_count = await ExamInstance.find(
                ExamInstance.examination_id == exam_id,
                ExamInstance.student_id == student_id,
                ExamInstance.status == ExamInstanceStatus.SUBMITTED,
            ).count()
            if attempts_count >= exam.max_attempts:
                return ExamStartResponse(
                    success=False,
                    message=f"Maximum attempts ({exam.max_attempts}) exceeded",
                    instance_id="",
                    start_time=now,
                    end_time=exam_end,
                    duration_minutes=exam.duration_minutes,
                    question_count=0,
                    total_points=exam.total_points,
                    biometric_required=False,
                )

            server_seed = str(uuid.uuid4())
            instance = ExamInstance(
                examination_id=exam_id,
                student_id=student_id,
                start_time=now,
                status=ExamInstanceStatus.IN_PROGRESS,
                total_points_possible=exam.total_points,
                server_seed=server_seed,
                rules_accepted=True,
            )
            await instance.insert()
            questions = await self._get_exam_questions(exam_id)
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
            return ExamStartResponse(
                success=False,
                message=f"Failed to start exam: {str(e)}",
                instance_id="",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration_minutes=0,
                question_count=0,
                total_points=0,
                biometric_required=False,
            )
    
    async def get_paper(self, instance_id: str) -> Dict[str, Any]:
        """Get randomized question paper for instance."""
        instance = await self.get_exam_instance(instance_id)
        if not instance or instance.status != ExamInstanceStatus.IN_PROGRESS:
            raise ValueError("Invalid or inactive exam instance")
            
        exam = await self.get_examination(instance.examination_id)
        questions = await self._get_exam_questions(instance.examination_id)
        
        import random
        rng = random.Random(instance.server_seed)
        
        paper_questions = []
        for i, q in enumerate(questions):
            options = await QuestionOption.find(QuestionOption.question_id == q.id).to_list()
            
            if exam.randomize_options:
                rng.shuffle(options)
                
            paper_options = []
            for j, opt in enumerate(options):
                label = chr(65 + j) # A, B, C, D
                paper_options.append({
                    "id": opt.id,
                    "label": label,
                    "text": opt.option_text
                })
                
            paper_questions.append({
                "sequence": i + 1,
                "id": q.id,
                "stem": q.question_text,
                "options": paper_options
            })
            
        if exam.randomize_questions:
            rng.shuffle(paper_questions)
            for i, q in enumerate(paper_questions):
                q["sequence"] = i + 1
                
        return {
            "attempt_id": instance_id,
            "exam": {
                "id": exam.id,
                "course_code": exam.course_id,
                "course_title": exam.title,
                "duration_minutes": exam.duration_minutes
            },
            "questions": paper_questions
        }

    async def save_answer(self, instance_id: str, answer_data) -> Dict[str, Any]:
        """Autosave answer."""
        instance = await self.get_exam_instance(instance_id)
        if not instance or instance.status != ExamInstanceStatus.IN_PROGRESS:
            raise ValueError("Invalid or inactive exam instance")
            
        exam_answer = await ExamAnswer.find_one(
            ExamAnswer.exam_instance_id == instance_id,
            ExamAnswer.question_id == answer_data.question_id
        )
        if not exam_answer:
            exam_answer = ExamAnswer(exam_instance_id=instance_id, question_id=answer_data.question_id)
            
        exam_answer.selected_option_id = answer_data.selected_option_id
        exam_answer.answer_text = answer_data.answer_text
        exam_answer.is_marked_for_review = answer_data.is_flagged
        await exam_answer.save()
        
        return {"success": True, "message": "Answer saved"}

    async def sync_clock(self, instance_id: str) -> Dict[str, Any]:
        """Sync clock with server."""
        instance = await self.get_exam_instance(instance_id)
        if not instance:
            raise ValueError("Instance not found")
            
        exam = await self.get_examination(instance.examination_id)
        now = datetime.now(timezone.utc)
        exam_end = (instance.start_time or now) + timedelta(minutes=exam.duration_minutes + instance.time_extension_minutes)
        
        if now > exam_end and instance.status == ExamInstanceStatus.IN_PROGRESS:
            await self.timeout_exam(instance_id, "system")
            
        return {
            "attempt_id": instance_id,
            "status": instance.status.lower(),
            "server_now": now.isoformat(),
            "ends_at": exam_end.isoformat() if instance.status == ExamInstanceStatus.IN_PROGRESS else None,
            "paused": False,
            "submitted_at": instance.end_time.isoformat() if instance.end_time else None
        }

    async def log_proctoring_event(self, instance_id: str, event_data) -> Dict[str, Any]:
        """Log proctoring event."""
        instance = await self.get_exam_instance(instance_id)
        if not instance:
            raise ValueError("Instance not found")
            
        if event_data.event_type == "focus_lost":
            instance.proctoring_strikes += 1
            await instance.save()
            
        # In a real app, we would store this in an ExamEvent collection
        # For now, just log to audit
        await self._log_audit_event(
            user_id=instance.student_id,
            action=AuditAction.UPDATE,
            resource_type="exam_instance",
            resource_id=instance_id,
            new_values={"event_type": event_data.event_type, "strikes": instance.proctoring_strikes}
        )
        return {"success": True, "strikes": instance.proctoring_strikes}
    
    async def submit_exam(self, instance_id: str, submission_data, submitted_by: str) -> ExamSubmissionResponse:
        """Submit exam answers."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                return ExamSubmissionResponse(
                    success=False,
                    message="Exam instance not found",
                    instance_id=instance_id,
                    submission_time=submission_data.submission_time,
                    total_answers=0,
                    points_earned=0,
                    percentage_score=None,
                    grade=None,
                )
            if instance.status != ExamInstanceStatus.IN_PROGRESS:
                return ExamSubmissionResponse(
                    success=False,
                    message=f"Exam cannot be submitted (status: {instance.status.value})",
                    instance_id=instance.id,
                    submission_time=submission_data.submission_time,
                    total_answers=0,
                    points_earned=instance.total_points_earned,
                    percentage_score=instance.percentage_score,
                    grade=instance.grade,
                )

            exam = await self.get_examination(instance.examination_id)
            if not exam:
                return ExamSubmissionResponse(
                    success=False,
                    message="Examination not found",
                    instance_id=instance.id,
                    submission_time=submission_data.submission_time,
                    total_answers=0,
                    points_earned=0,
                    percentage_score=None,
                    grade=None,
                )

            total_points_earned = 0
            processed_answers = 0

            for answer_data in submission_data.answers:
                question_id = answer_data.get('question_id')
                selected_option_id = answer_data.get('selected_option_id')
                answer_text = answer_data.get('answer_text')
                question = await Question.find_one(Question.id == question_id)
                if not question:
                    continue

                points_earned = await self._calculate_answer_points(
                    question, selected_option_id, answer_text
                )
                total_points_earned += points_earned
                processed_answers += 1

                exam_answer = await ExamAnswer.find_one(
                    ExamAnswer.exam_instance_id == instance.id,
                    ExamAnswer.question_id == question_id
                )
                if not exam_answer:
                    exam_answer = ExamAnswer(exam_instance_id=instance.id, question_id=question_id)
                exam_answer.selected_option_id = selected_option_id
                exam_answer.answer_text = answer_text
                exam_answer.points_earned = points_earned
                exam_answer.is_correct = points_earned > 0
                await exam_answer.save()

            instance.end_time = submission_data.submission_time
            instance.status = ExamInstanceStatus.SUBMITTED
            instance.total_points_earned = total_points_earned
            instance.percentage_score = (total_points_earned / instance.total_points_possible) * 100 if instance.total_points_possible > 0 else 0
            instance.grade = self._calculate_grade(instance.percentage_score)
            await instance.save()
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
            return ExamSubmissionResponse(
                success=False,
                message=f"Failed to submit exam: {str(e)}",
                instance_id=instance_id,
                submission_time=submission_data.submission_time,
                total_answers=0,
                points_earned=0,
                percentage_score=None,
                grade=None,
            )
    
    async def review_exam(self, instance_id: str, reviewed_by: str) -> Optional[ExamReviewResponse]:
        """Review submitted exam."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance or instance.status != ExamInstanceStatus.SUBMITTED:
                return None
            exam = await self.get_examination(instance.examination_id)
            student = await Student.find_one(Student.id == instance.student_id)
            answers = await ExamAnswer.find(ExamAnswer.exam_instance_id == instance_id).to_list()

            correct_answers = 0
            incorrect_answers = 0
            unanswered = 0
            processed_answers = []

            for answer in answers:
                if answer.selected_option_id or answer.answer_text:
                    is_correct = bool(answer.is_correct)
                    if is_correct:
                        correct_answers += 1
                    else:
                        incorrect_answers += 1
                else:
                    unanswered += 1
                question = await Question.find_one(Question.id == answer.question_id)
                processed_answers.append({
                    "question_id": answer.question_id,
                    "question_text": question.question_text if question else "",
                    "selected_option_id": answer.selected_option_id,
                    "answer_text": answer.answer_text,
                    "is_correct": is_correct if answer.selected_option_id or answer.answer_text else None,
                    "points_earned": answer.points_earned,
                    "time_spent": answer.time_spent_seconds
                })

            return ExamReviewResponse(
                instance_id=instance.id,
                exam_title=exam.title if exam else "",
                student_name=f"{student.first_name} {student.last_name}".strip() if student else "",
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
                time_per_question=[]
            )
        except Exception as e:
            raise ValueError(f"Failed to review exam: {str(e)}")
    
    async def get_exam_statistics(self, exam_id: str) -> Dict[str, Any]:
        """Get examination statistics."""
        try:
            exam = await self.get_examination(exam_id)
            if not exam:
                raise ValueError("Examination not found")

            instances = await ExamInstance.find(ExamInstance.examination_id == exam_id).to_list()
            total_instances = len(instances)
            completed_instances = len([i for i in instances if i.status == ExamInstanceStatus.SUBMITTED])
            in_progress_instances = len([i for i in instances if i.status == ExamInstanceStatus.IN_PROGRESS])
            not_started_instances = len([i for i in instances if i.status == ExamInstanceStatus.NOT_STARTED])
            scores = [i.percentage_score for i in instances if i.percentage_score is not None]
            average_score = sum(scores) / len(scores) if scores else 0
            highest_score = max(scores) if scores else 0
            lowest_score = min(scores) if scores else 0
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
            
            instances = await ExamInstance.find(
                ExamInstance.examination_id == exam_id,
                ExamInstance.status == ExamInstanceStatus.SUBMITTED
            ).to_list()
            graded_count = 0
            grading_errors = []
            for instance in instances:
                try:
                    await self._grade_instance(instance)
                    graded_count += 1
                except Exception as e:
                    grading_errors.append(f"Instance {instance.id}: {str(e)}")

            scores = [i.percentage_score for i in instances if i.percentage_score is not None]
            average_score = sum(scores) / len(scores) if scores else 0
            passed_count = len([i for i in instances if (i.percentage_score or 0) >= 50])
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
                exam.updated_at = datetime.now(timezone.utc)
                exam.updated_by = published_by
                await exam.save()
            
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

    async def get_student_results(self, student_id: str, exam_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return released results for a student, respecting embargo flags."""
        query = ExamInstance.find(
            ExamInstance.student_id == student_id,
            ExamInstance.status == ExamInstanceStatus.SUBMITTED,
            ExamInstance.is_active == True,
        )
        if exam_id:
            query = query.find(ExamInstance.examination_id == exam_id)
        instances = await query.sort("-created_at").to_list()

        results = []
        for inst in instances:
            exam = await self.get_examination(inst.examination_id)
            if not exam:
                continue
            # Embargo check: results hidden until officer releases them
            if exam.embargo_active and not exam.show_results_immediately:
                results.append({
                    "instance_id": inst.id,
                    "exam_id": exam.id,
                    "exam_title": exam.title,
                    "course_id": exam.course_id,
                    "status": "embargoed",
                    "submitted_at": inst.end_time.isoformat() if inst.end_time else None,
                    "score": None,
                    "grade": None,
                    "percentage": None,
                    "message": "Results are currently under Senate embargo and will be released shortly.",
                })
            else:
                results.append({
                    "instance_id": inst.id,
                    "exam_id": exam.id,
                    "exam_title": exam.title,
                    "course_id": exam.course_id,
                    "status": "released",
                    "submitted_at": inst.end_time.isoformat() if inst.end_time else None,
                    "score": inst.total_points_earned,
                    "max_score": inst.total_points_possible,
                    "grade": inst.grade,
                    "percentage": round(inst.percentage_score or 0, 2),
                    "message": None,
                })
        return results

    async def get_item_analysis(self, exam_id: str) -> Dict[str, Any]:
        """Compute per-question P-value, discrimination, and distractor percentages."""
        instances = await ExamInstance.find(
            ExamInstance.examination_id == exam_id,
            ExamInstance.status == ExamInstanceStatus.SUBMITTED,
        ).to_list()

        if not instances:
            return {"exam_id": exam_id, "total_candidates": 0, "items": []}

        total = len(instances)
        instance_ids = [i.id for i in instances]

        questions = await self._get_exam_questions(exam_id)
        items = []

        for q in questions:
            answers = await ExamAnswer.find(
                ExamAnswer.question_id == q.id,
            ).to_list()
            # Filter to answers belonging to this exam's instances
            answers = [a for a in answers if a.exam_instance_id in instance_ids]

            options = await QuestionOption.find(QuestionOption.question_id == q.id).to_list()
            correct_opt = next((o for o in options if o.is_correct), None)

            option_counts: Dict[str, int] = {o.id: 0 for o in options}
            correct_count = 0

            for ans in answers:
                if ans.selected_option_id:
                    if ans.selected_option_id in option_counts:
                        option_counts[ans.selected_option_id] += 1
                    if correct_opt and ans.selected_option_id == correct_opt.id:
                        correct_count += 1

            p_value = round(correct_count / total, 4) if total else 0
            # Upper/lower 27% discrimination index
            sorted_instances = sorted(instances, key=lambda i: i.total_points_earned, reverse=True)
            cutoff = max(1, int(total * 0.27))
            upper_ids = {i.id for i in sorted_instances[:cutoff]}
            lower_ids = {i.id for i in sorted_instances[-cutoff:]}

            upper_correct = sum(1 for a in answers if a.exam_instance_id in upper_ids and correct_opt and a.selected_option_id == correct_opt.id)
            lower_correct = sum(1 for a in answers if a.exam_instance_id in lower_ids and correct_opt and a.selected_option_id == correct_opt.id)
            discrimination = round((upper_correct - lower_correct) / cutoff, 4) if cutoff else 0

            items.append({
                "question_id": q.id,
                "question_stem": q.question_text[:120],
                "p_value": p_value,
                "discrimination_index": discrimination,
                "correct_count": correct_count,
                "total_responses": len(answers),
                "distractor_percentages": {
                    opt_id: round(cnt / total * 100, 1)
                    for opt_id, cnt in option_counts.items()
                },
            })

        return {
            "exam_id": exam_id,
            "total_candidates": total,
            "items": items,
        }

    async def export_results_csv(self, exam_id: str) -> str:
        """Generate CSV string of all submitted results for an exam."""
        import csv
        import io

        instances = await ExamInstance.find(
            ExamInstance.examination_id == exam_id,
            ExamInstance.status == ExamInstanceStatus.SUBMITTED,
        ).to_list()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["student_id", "score", "max_score", "percentage", "grade", "submitted_at", "proctoring_strikes"])
        for inst in instances:
            writer.writerow([
                inst.student_id,
                inst.total_points_earned,
                inst.total_points_possible,
                round(inst.percentage_score or 0, 2),
                inst.grade or "",
                inst.end_time.isoformat() if inst.end_time else "",
                inst.proctoring_strikes,
            ])
        return output.getvalue()

    async def timeout_exam(self, instance_id: str, managed_by: str) -> Optional[ExamInstance]:
        """Mark an in-progress exam instance as timed out."""
        instance = await self.get_exam_instance(instance_id)
        if not instance:
            return None
        if instance.status not in [ExamInstanceStatus.IN_PROGRESS, ExamInstanceStatus.NOT_STARTED]:
            raise ValueError(f"Cannot timeout instance with status {instance.status}")
        instance.status = ExamInstanceStatus.TIMED_OUT
        instance.end_time = datetime.now(timezone.utc)
        await instance.save()
        await self._log_audit_event(
            user_id=managed_by,
            action=AuditAction.UPDATE,
            resource_type="exam_instance",
            resource_id=instance.id,
            new_values={"status": "TIMED_OUT"},
        )
        return instance

    async def extend_exam_time(self, instance_id: str, extension_minutes: int, reason: str, managed_by: str) -> Optional[ExamInstance]:
        """Extend exam time for a student instance."""
        instance = await self.get_exam_instance(instance_id)
        if not instance:
            return None
        if extension_minutes <= 0:
            raise ValueError("extension_minutes must be positive")
        instance.time_extension_minutes += extension_minutes
        await instance.save()
        await self._log_audit_event(
            user_id=managed_by,
            action=AuditAction.UPDATE,
            resource_type="exam_instance",
            resource_id=instance.id,
            new_values={"time_extension_minutes": instance.time_extension_minutes, "reason": reason},
        )
        return instance
    
    # Private helper methods
    
    async def _add_questions_to_exam(self, exam_id: str, question_ids: List[str], question_order: Optional[List[str]]):
        """Add questions to examination."""
        for i, question_id in enumerate(question_ids):
            order = question_order.index(question_id) + 1 if question_order else i + 1
            exam_question = ExamQuestion(examination_id=exam_id, question_id=question_id, question_order=order)
            await exam_question.insert()
    
    async def _get_exam_questions(self, exam_id: str) -> List[Question]:
        """Get questions for examination."""
        links = await ExamQuestion.find(ExamQuestion.examination_id == exam_id).sort("question_order").to_list()
        questions: List[Question] = []
        for l in links:
            q = await Question.find_one(Question.id == l.question_id)
            if q:
                questions.append(q)
        return questions
    
    async def _calculate_answer_points(self, question, selected_option_id: str, answer_text: str) -> int:
        """Calculate points earned for answer."""
        # Get correct answer
        if question.question_type.value == "MULTIPLE_CHOICE":
            # For MCQ, check if selected option is correct
            correct_option = await QuestionOption.find_one(
                QuestionOption.question_id == question.id,
                QuestionOption.is_correct == True
            )
            if correct_option and selected_option_id == correct_option.id:
                return question.points_value
            return 0
        else:
            # For text answers, this would require AI/manual grading
            # For now, return 0 (would be updated during grading)
            return 0
    
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
        await instance.save()
    
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
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=new_values,
                old_values=old_values
            )
            await audit_log.insert()
        except Exception:
            pass
