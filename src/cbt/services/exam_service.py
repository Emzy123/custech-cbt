"""
Examination service for CSC 131 simplified exam management using Beanie (MongoDB).
"""

import uuid
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from ..models.exam import Examination, ExamInstance, Result
from ..models.question import Question
from ..models.user import User
from ..schemas.exam import ExamStartResponse, ExamSubmissionResponse, ExamReviewResponse


class ExamService:
    """Examination management service for CUSTECH CSC 131."""

    def __init__(self, db: Any = None):
        self.db = db

    async def create_examination(self, exam_data, created_by: str) -> Examination:
        """Create a new CSC 131 examination."""
        try:
            # Standardize all exams to CSC131
            exam = Examination(
                title=exam_data.title,
                course_code="CSC131",
                duration_minutes=exam_data.duration_minutes,
                total_questions=exam_data.total_questions,
                passing_score=float(exam_data.pass_points) if getattr(exam_data, "pass_points", None) is not None else (float(exam_data.passing_score) if getattr(exam_data, "passing_score", None) is not None else 50.0),
                scheduled_date=datetime.combine(exam_data.exam_date, datetime.min.time()) if not isinstance(exam_data.exam_date, datetime) else exam_data.exam_date,
                start_time=exam_data.start_time.strftime("%H:%M") if isinstance(exam_data.start_time, datetime) else getattr(exam_data, "start_time", "09:00"),
                end_time=exam_data.end_time.strftime("%H:%M") if isinstance(exam_data.end_time, datetime) else getattr(exam_data, "end_time", "17:00"),
                is_active=True,
                created_by=created_by
            )
            await exam.insert()
            return exam
        except Exception as e:
            raise ValueError(f"Failed to create examination: {str(e)}")

    async def list_examinations(self, course_id: Optional[str] = None,
                               academic_session_id: Optional[str] = None,
                               status: Optional[Any] = None,
                               limit: int = 50, cursor: Optional[str] = None) -> List[Examination]:
        """List active examinations."""
        try:
            query = Examination.find(Examination.is_active == True)
            exams = await query.sort("-created_at").limit(limit).to_list()
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
        """Update examination fields."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None

            data_dict = exam_data.model_dump(exclude_unset=True) if hasattr(exam_data, "model_dump") else (exam_data.dict(exclude_unset=True) if hasattr(exam_data, "dict") else exam_data)
            
            for field, value in data_dict.items():
                if field == "exam_date" and value:
                    exam.scheduled_date = datetime.combine(value, datetime.min.time()) if not isinstance(value, datetime) else value
                elif field == "start_time" and value:
                    exam.start_time = value.strftime("%H:%M") if isinstance(value, datetime) else str(value)
                elif field == "end_time" and value:
                    exam.end_time = value.strftime("%H:%M") if isinstance(value, datetime) else str(value)
                elif field == "pass_points" and value is not None:
                    exam.passing_score = float(value)
                elif hasattr(exam, field):
                    setattr(exam, field, value)

            await exam.save()
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
            await exam.save()
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete examination: {str(e)}")

    async def schedule_examination(self, exam_id: str, schedule_data, scheduled_by: str) -> Optional[Examination]:
        """Schedule/Reschedule examination."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            
            scheduled_date = getattr(schedule_data, 'exam_date', None) or (schedule_data.get('exam_date') if isinstance(schedule_data, dict) else None)
            start_time = getattr(schedule_data, 'start_time', None) or (schedule_data.get('start_time') if isinstance(schedule_data, dict) else None)
            duration = getattr(schedule_data, 'duration_minutes', None) or (schedule_data.get('duration_minutes') if isinstance(schedule_data, dict) else None)

            if scheduled_date:
                exam.scheduled_date = datetime.combine(scheduled_date, datetime.min.time()) if not isinstance(scheduled_date, datetime) else scheduled_date
            if start_time:
                exam.start_time = start_time.strftime("%H:%M") if isinstance(start_time, datetime) else str(start_time)
            if duration:
                exam.duration_minutes = int(duration)

            await exam.save()
            return exam
        except Exception as e:
            raise ValueError(f"Failed to schedule examination: {str(e)}")

    async def publish_examination(self, exam_id: str, published_by: str) -> Optional[Examination]:
        """Publish examination to make it visible/active."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            exam.is_active = True
            await exam.save()
            return exam
        except Exception as e:
            raise ValueError(f"Failed to publish examination: {str(e)}")

    async def cancel_examination(self, exam_id: str, reason: str, cancelled_by: str) -> Optional[Examination]:
        """Cancel examination (deactivate it)."""
        try:
            exam = await Examination.find_one(Examination.id == exam_id, Examination.is_active == True)
            if not exam:
                return None
            exam.is_active = False
            await exam.save()
            return exam
        except Exception as e:
            raise ValueError(f"Failed to cancel examination: {str(e)}")

    async def list_exam_instances(self, exam_id: str, status: Optional[str] = None,
                                limit: int = 50, cursor: Optional[str] = None) -> List[ExamInstance]:
        """List student exam sessions."""
        try:
            query = ExamInstance.find(ExamInstance.exam_id == exam_id, ExamInstance.is_active == True)
            if status:
                query = query.find(ExamInstance.status == status)
            return await query.sort("-created_at").limit(limit).to_list()
        except Exception as e:
            raise ValueError(f"Failed to list exam instances: {str(e)}")

    async def get_exam_instance(self, instance_id: str) -> Optional[ExamInstance]:
        """Get student exam session."""
        try:
            return await ExamInstance.find_one(ExamInstance.id == instance_id, ExamInstance.is_active == True)
        except Exception as e:
            raise ValueError(f"Failed to get exam instance: {str(e)}")

    async def start_exam(self, exam_id: str, student_id: str, started_by: str) -> ExamStartResponse:
        """Start a new exam session for a student."""
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

            # Check if student has already completed this exam (has Result document)
            existing_result = await Result.find_one(Result.exam_id == exam_id, Result.student_id == student_id)
            if existing_result:
                return ExamStartResponse(
                    success=False,
                    message="You have already completed this examination.",
                    instance_id="",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                    duration_minutes=0,
                    question_count=0,
                    total_points=0,
                    biometric_required=False,
                )

            now = datetime.now(timezone.utc)
            end_time = now + timedelta(minutes=exam.duration_minutes)

            # Check if student has an existing in-progress session
            instance = await ExamInstance.find_one(
                ExamInstance.exam_id == exam_id,
                ExamInstance.student_id == student_id,
                ExamInstance.status == "in_progress",
                ExamInstance.is_active == True
            )

            if not instance:
                instance = ExamInstance(
                    student_id=student_id,
                    exam_id=exam_id,
                    start_time=now,
                    end_time=end_time,
                    answers=[],
                    status="in_progress"
                )
                await instance.insert()

            # Retrieve active questions for CSC131
            question_count = await Question.find(Question.course_code == "CSC131", Question.is_active == True).count()

            return ExamStartResponse(
                success=True,
                message="Exam started successfully",
                instance_id=instance.id,
                attempt_id=instance.id,
                start_time=instance.start_time,
                end_time=instance.end_time,
                duration_minutes=exam.duration_minutes,
                question_count=question_count,
                total_points=question_count,
                biometric_required=False
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
        """Get randomized, shuffled CSC 131 question paper for student session."""
        instance = await self.get_exam_instance(instance_id)
        if not instance or instance.status != "in_progress":
            raise ValueError("Invalid or inactive exam instance")

        exam = await self.get_examination(instance.exam_id)
        if not exam:
            raise ValueError("Examination not found")

        # Stable randomization per student session
        seed_str = f"{instance.student_id}:{instance.id}"
        rng = random.Random(seed_str)

        # Get all CSC131 questions
        questions = await Question.find(Question.course_code == "CSC131", Question.is_active == True).to_list()
        rng.shuffle(questions)

        # Limit to the total number of questions requested by exam, or all if not specified
        limit = exam.total_questions if exam.total_questions > 0 else len(questions)
        selected_questions = questions[:limit]

        paper_questions = []
        for i, q in enumerate(selected_questions):
            # Flat options representation: A, B, C, D
            paper_questions.append({
                "sequence": i + 1,
                "id": q.id,
                "stem": q.question_text,
                "options": [
                    {"id": "A", "label": "A", "text": q.option_a},
                    {"id": "B", "label": "B", "text": q.option_b},
                    {"id": "C", "label": "C", "text": q.option_c},
                    {"id": "D", "label": "D", "text": q.option_d},
                ]
            })

        return {
            "attempt_id": instance_id,
            "exam": {
                "id": exam.id,
                "course_code": "CSC131",
                "course_title": exam.title,
                "duration_minutes": exam.duration_minutes
            },
            "questions": paper_questions
        }

    async def save_answer(self, instance_id: str, answer_data) -> Dict[str, Any]:
        """Autosave answer to session."""
        instance = await self.get_exam_instance(instance_id)
        if not instance or instance.status != "in_progress":
            raise ValueError("Invalid or inactive exam instance")

        question_id = answer_data.question_id
        # Support both option letters and raw options from schemas compatibility
        selected_option = answer_data.selected_option_id or answer_data.answer_text or ""

        # Update answers list
        instance.answers = [a for a in instance.answers if a.get("question_id") != question_id]
        instance.answers.append({
            "question_id": question_id,
            "selected_option": selected_option
        })
        await instance.save()

        return {"success": True, "message": "Answer saved"}

    async def sync_clock(self, instance_id: str) -> Dict[str, Any]:
        """Sync session clock with server, auto-submitting if expired."""
        instance = await self.get_exam_instance(instance_id)
        if not instance:
            raise ValueError("Instance not found")

        now = datetime.now(timezone.utc)
        if now > instance.end_time and instance.status == "in_progress":
            await self.submit_exam(instance_id, None, "system")
            await instance.sync()

        return {
            "attempt_id": instance_id,
            "status": instance.status,
            "server_now": now.isoformat(),
            "ends_at": instance.end_time.isoformat() if instance.status == "in_progress" else None,
            "paused": False,
            "submitted_at": instance.updated_at.isoformat() if instance.status != "in_progress" else None
        }

    async def submit_exam(self, instance_id: str, submission_data, submitted_by: str) -> ExamSubmissionResponse:
        """Submit and instantly grade student's exam session."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                raise ValueError("Exam instance not found")

            # Check if already submitted to prevent double-grading
            if instance.status != "in_progress":
                result = await Result.find_one(Result.exam_id == instance.exam_id, Result.student_id == instance.student_id)
                if result:
                    return ExamSubmissionResponse(
                        success=True,
                        message="Exam already submitted.",
                        instance_id=instance.id,
                        submission_time=instance.end_time,
                        total_answers=result.total_questions,
                        points_earned=int(result.score),
                        percentage_score=result.percentage,
                        grade=result.grade
                    )

            # Store any final answers submitted directly in submission request body
            if submission_data and hasattr(submission_data, "answers") and submission_data.answers:
                for ans in submission_data.answers:
                    q_id = ans.get("question_id")
                    sel_opt = ans.get("selected_option_id") or ans.get("selected_option") or ""
                    instance.answers = [a for a in instance.answers if a.get("question_id") != q_id]
                    instance.answers.append({
                        "question_id": q_id,
                        "selected_option": sel_opt
                    })

            # Grade the examination
            questions = await Question.find(Question.course_code == "CSC131", Question.is_active == True).to_list()
            questions_dict = {q.id: q for q in questions}

            score = 0
            # Use actual exam total questions or fallback to total database CSC131 questions
            exam = await self.get_examination(instance.exam_id)
            total_questions = exam.total_questions if (exam and exam.total_questions > 0) else len(questions)
            if total_questions == 0:
                total_questions = len(questions)

            for ans in instance.answers:
                q_id = ans.get("question_id")
                sel_opt = str(ans.get("selected_option", "")).strip().upper()
                q = questions_dict.get(q_id)
                if q and q.correct_answer.strip().upper() == sel_opt:
                    score += 1

            percentage = (score / total_questions * 100) if total_questions > 0 else 0.0

            # Direct grading rubric mapping
            if percentage >= 70:
                grade = "A"
            elif percentage >= 60:
                grade = "B"
            elif percentage >= 50:
                grade = "C"
            elif percentage >= 45:
                grade = "D"
            else:
                grade = "F"

            # Finalize instance state
            instance.status = "submitted"
            instance.end_time = datetime.now(timezone.utc)
            await instance.save()

            # Insert/Update result document
            result = await Result.find_one(Result.exam_id == instance.exam_id, Result.student_id == instance.student_id)
            if not result:
                result = Result(
                    student_id=instance.student_id,
                    exam_id=instance.exam_id,
                    score=float(score),
                    total_questions=total_questions,
                    percentage=percentage,
                    grade=grade,
                    date_taken=instance.end_time
                )
                await result.insert()
            else:
                result.score = float(score)
                result.total_questions = total_questions
                result.percentage = percentage
                result.grade = grade
                result.date_taken = instance.end_time
                await result.save()

            return ExamSubmissionResponse(
                success=True,
                message="Exam submitted and graded successfully",
                instance_id=instance.id,
                submission_time=instance.end_time,
                total_answers=len(instance.answers),
                points_earned=score,
                percentage_score=percentage,
                grade=grade
            )

        except Exception as e:
            return ExamSubmissionResponse(
                success=False,
                message=f"Failed to submit exam: {str(e)}",
                instance_id=instance_id,
                submission_time=datetime.now(timezone.utc),
                total_answers=0,
                points_earned=0,
                percentage_score=None,
                grade=None,
            )

    async def review_exam(self, instance_id: str, reviewed_by: str) -> Optional[ExamReviewResponse]:
        """Retrieve student's graded exam review session details."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                return None

            exam = await self.get_examination(instance.exam_id)
            user = await User.find_one(User.id == instance.student_id)

            questions = await Question.find(Question.course_code == "CSC131", Question.is_active == True).to_list()
            questions_dict = {q.id: q for q in questions}

            result = await Result.find_one(Result.exam_id == instance.exam_id, Result.student_id == instance.student_id)
            score = result.score if result else 0.0
            total_questions = result.total_questions if result else len(questions)
            percentage = result.percentage if result else 0.0
            grade = result.grade if result else "F"

            answers_processed = []
            correct_count = 0
            incorrect_count = 0
            unanswered_count = 0

            for ans in instance.answers:
                q_id = ans.get("question_id")
                sel_opt = str(ans.get("selected_option", "")).strip().upper()
                q = questions_dict.get(q_id)
                if not q:
                    continue

                is_correct = q.correct_answer.strip().upper() == sel_opt
                if not sel_opt:
                    unanswered_count += 1
                elif is_correct:
                    correct_count += 1
                else:
                    incorrect_count += 1

                answers_processed.append({
                    "question_id": q_id,
                    "question_text": q.question_text,
                    "selected_option_id": sel_opt,
                    "answer_text": None,
                    "is_correct": is_correct,
                    "points_earned": 1 if is_correct else 0,
                    "time_spent": 0,
                    "options": [
                        {"id": "A", "option_text": q.option_a, "is_correct": q.correct_answer == "A"},
                        {"id": "B", "option_text": q.option_b, "is_correct": q.correct_answer == "B"},
                        {"id": "C", "option_text": q.option_c, "is_correct": q.correct_answer == "C"},
                        {"id": "D", "option_text": q.option_d, "is_correct": q.correct_answer == "D"},
                    ],
                    "correct_option_id": q.correct_answer,
                    "explanation": ""
                })

            return ExamReviewResponse(
                instance_id=instance.id,
                exam_title=exam.title if exam else "Introduction to Computer Science",
                student_name=user.full_name if user else "Student",
                start_time=instance.start_time,
                end_time=instance.end_time,
                duration_taken=int((instance.end_time - instance.start_time).total_seconds() / 60) if instance.end_time and instance.start_time else 0,
                total_points=total_questions,
                points_earned=int(score),
                percentage_score=percentage,
                grade=grade,
                passed=percentage >= 50.0,
                answers=answers_processed,
                correct_answers=correct_count,
                incorrect_answers=incorrect_count,
                unanswered=unanswered_count,
                time_per_question=[]
            )
        except Exception as e:
            raise ValueError(f"Failed to review exam: {str(e)}")

    async def get_student_results(self, student_id: str, exam_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List released exam results for a student."""
        try:
            query = Result.find(Result.student_id == student_id)
            if exam_id:
                query = query.find(Result.exam_id == exam_id)
            results_list = await query.sort("-date_taken").to_list()

            formatted_results = []
            for r in results_list:
                exam = await Examination.find_one(Examination.id == r.exam_id)
                formatted_results.append({
                    "instance_id": r.id,
                    "exam_id": r.exam_id,
                    "exam_title": exam.title if exam else "Introduction to Computer Science",
                    "course_id": "CSC131",
                    "status": "released",
                    "submitted_at": r.date_taken.isoformat(),
                    "score": r.score,
                    "max_score": r.total_questions,
                    "grade": r.grade,
                    "percentage": round(r.percentage, 2),
                    "message": None
                })
            return formatted_results
        except Exception as e:
            raise ValueError(f"Failed to get student results: {str(e)}")

    async def export_results_csv(self, exam_id: str) -> str:
        """Export exam results table to CSV format."""
        try:
            import csv
            import io

            results = await Result.find(Result.exam_id == exam_id).to_list()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Matric Number", "Student Name", "Score", "Total Questions", "Percentage", "Grade", "Date Taken"])

            for r in results:
                user = await User.find_one(User.id == r.student_id)
                name = user.full_name if user else "Student"
                matric = user.matric_number if user else r.student_id
                writer.writerow([
                    matric,
                    name,
                    r.score,
                    r.total_questions,
                    round(r.percentage, 2),
                    r.grade,
                    r.date_taken.isoformat()
                ])
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to export results CSV: {str(e)}")

    async def timeout_exam(self, instance_id: str, managed_by: str) -> Optional[ExamInstance]:
        """Forcefully timeout/submit an in-progress exam session."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                return None
            if instance.status == "in_progress":
                await self.submit_exam(instance_id, None, managed_by)
                await instance.sync()
            return instance
        except Exception as e:
            raise ValueError(f"Failed to timeout exam: {str(e)}")

    async def extend_exam_time(self, instance_id: str, extension_minutes: int, reason: str, managed_by: str) -> Optional[ExamInstance]:
        """Extend exam session end time."""
        try:
            instance = await self.get_exam_instance(instance_id)
            if not instance:
                return None
            instance.end_time = instance.end_time + timedelta(minutes=extension_minutes)
            await instance.save()
            return instance
        except Exception as e:
            raise ValueError(f"Failed to extend exam time: {str(e)}")

    async def get_exam_statistics(self, exam_id: str) -> Dict[str, Any]:
        """Calculate basic exam score statistics for Lecturer."""
        try:
            exam = await self.get_examination(exam_id)
            if not exam:
                raise ValueError("Examination not found")

            results = await Result.find(Result.exam_id == exam_id).to_list()
            total_instances = len(results)
            scores = [r.percentage for r in results]
            average_score = sum(scores) / len(scores) if scores else 0.0
            highest_score = max(scores) if scores else 0.0
            lowest_score = min(scores) if scores else 0.0

            pass_count = len([s for s in scores if s >= 50.0])
            pass_rate = (pass_count / total_instances * 100) if total_instances > 0 else 0.0

            return {
                "exam_id": exam_id,
                "exam_title": exam.title,
                "total_instances": total_instances,
                "completed_instances": total_instances,
                "in_progress_instances": 0,
                "not_started_instances": 0,
                "average_score": round(average_score, 2),
                "highest_score": round(highest_score, 2),
                "lowest_score": round(lowest_score, 2),
                "pass_rate": round(pass_rate, 2),
                "completion_rate": 100.0,
                "score_distribution": {},
                "time_distribution": {}
            }
        except Exception as e:
            raise ValueError(f"Failed to get exam statistics: {str(e)}")

    async def get_exam_results(self, exam_id: str, format: str = "summary") -> Dict[str, Any]:
        """Get examination results summary or detail."""
        try:
            if format == "summary":
                return await self.get_exam_statistics(exam_id)
            
            results = await Result.find(Result.exam_id == exam_id).to_list()
            details = []
            for r in results:
                user = await User.find_one(User.id == r.student_id)
                details.append({
                    "matric_number": user.username if user else r.student_id,
                    "student_name": user.full_name if user else "Student",
                    "score": r.score,
                    "total_questions": r.total_questions,
                    "percentage": round(r.percentage, 2),
                    "grade": r.grade,
                    "date_taken": r.date_taken.isoformat()
                })
            return {"exam_id": exam_id, "results": details}
        except Exception as e:
            raise ValueError(f"Failed to get exam results: {str(e)}")

    async def log_proctoring_event(self, instance_id: str, event_data) -> Dict[str, Any]:
        """Stub for proctoring event logging compatibility."""
        return {"success": True, "strikes": 0}
