"""
Cryptographically secure question selection and randomisation service.
"""

import uuid
import secrets
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from ..models.question import Question, QuestionType, QuestionStatus
from ..models.exam import Examination, ExamQuestion
from ..services.audit_service import AuditService, AuditAction
from ..core.redis import cache_manager


class QuestionRandomisationService:
    """Cryptographically secure question selection and randomisation service."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.backend = default_backend()
    
    async def generate_exam_questions(self, examination_id: str, student_id: str) -> Dict[str, Any]:
        """
        Generate personalized exam questions for a student with cryptographically secure randomisation.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            
        Returns:
            Dict containing question data and randomisation metadata
        """
        try:
            # Get examination details
            exam_result = await self.db.execute(
                select(Examination).where(Examination.id == examination_id)
            )
            exam = exam_result.scalar_one_or_none()
            if not exam:
                raise ValueError("Examination not found")
            
            # Generate secure seed for this student-exam combination
            seed = self._generate_student_exam_seed(examination_id, student_id)
            
            # Get exam questions (base questions from blueprint)
            base_questions = await self._get_exam_base_questions(examination_id)
            if not base_questions:
                raise ValueError("No questions found for examination")
            
            # Apply randomisation
            randomised_questions = await self._apply_question_randomisation(
                base_questions, seed, exam.randomize_questions, exam.randomize_options
            )
            
            # Generate question order if randomization enabled
            if exam.randomize_questions:
                question_order = self._generate_question_order(randomised_questions, seed)
            else:
                question_order = list(range(len(randomised_questions)))
            
            # Create exam instance data
            exam_instance = {
                "examination_id": examination_id,
                "student_id": student_id,
                "seed": seed,
                "questions": randomised_questions,
                "question_order": question_order,
                "total_questions": len(randomised_questions),
                "generated_at": datetime.utcnow(),
                "randomisation_applied": {
                    "questions_randomized": exam.randomize_questions,
                    "options_randomized": exam.randomize_options,
                    "order_randomized": exam.randomize_questions
                }
            }
            
            # Cache the generated questions
            cache_key = f"exam_questions:{examination_id}:{student_id}"
            await self.cache.set(cache_key, exam_instance, ttl=exam.duration_minutes * 60 + 300)  # Exam duration + 5 minutes buffer
            
            # Log question generation
            await self._log_audit_event(
                user_id=student_id,
                action=AuditAction.CREATE,
                resource_type="exam_instance_questions",
                resource_id=f"{examination_id}:{student_id}",
                new_values={
                    "examination_id": examination_id,
                    "question_count": len(randomised_questions),
                    "seed": seed[:16] + "..."  # Log partial seed only
                }
            )
            
            return exam_instance
            
        except Exception as e:
            raise ValueError(f"Failed to generate exam questions: {str(e)}")
    
    async def get_student_exam_questions(self, examination_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get previously generated exam questions for a student.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            
        Returns:
            Exam instance data or None if not found
        """
        try:
            cache_key = f"exam_questions:{examination_id}:{student_id}"
            exam_instance = await self.cache.get(cache_key)
            return exam_instance
        except Exception as e:
            raise ValueError(f"Failed to get exam questions: {str(e)}")
    
    async def verify_question_integrity(self, examination_id: str, student_id: str, provided_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify the integrity of submitted answers against the original question set.
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            provided_answers: List of submitted answers
            
        Returns:
            Verification result with integrity check
        """
        try:
            # Get original exam questions
            exam_instance = await self.get_student_exam_questions(examination_id, student_id)
            if not exam_instance:
                raise ValueError("Exam instance not found")
            
            # Verify answer structure
            verification_result = {
                "is_valid": True,
                "verification_errors": [],
                "missing_answers": [],
                "invalid_answers": [],
                "answer_count_mismatch": False
            }
            
            # Check answer count
            if len(provided_answers) != exam_instance["total_questions"]:
                verification_result["answer_count_mismatch"] = True
                verification_result["verification_errors"].append(
                    f"Answer count mismatch: expected {exam_instance['total_questions']}, got {len(provided_answers)}"
                )
            
            # Verify each answer
            provided_question_ids = set()
            for answer in provided_answers:
                question_id = answer.get("question_id")
                if not question_id:
                    verification_result["invalid_answers"].append({
                        "answer": answer,
                        "error": "Missing question_id"
                    })
                    continue
                
                provided_question_ids.add(question_id)
                
                # Check if question belongs to this exam instance
                if question_id not in [q["id"] for q in exam_instance["questions"]]:
                    verification_result["invalid_answers"].append({
                        "question_id": question_id,
                        "error": "Question not part of this exam instance"
                    })
            
            # Check for missing answers
            expected_question_ids = set(q["id"] for q in exam_instance["questions"])
            missing_ids = expected_question_ids - provided_question_ids
            if missing_ids:
                verification_result["missing_answers"] = list(missing_ids)
                verification_result["verification_errors"].append(
                    f"Missing answers for {len(missing_ids)} questions"
                )
            
            # Set overall validity
            verification_result["is_valid"] = (
                not verification_result["verification_errors"] and
                not verification_result["invalid_answers"] and
                not verification_result["missing_answers"]
            )
            
            return verification_result
            
        except Exception as e:
            raise ValueError(f"Failed to verify question integrity: {str(e)}")
    
    async def regenerate_exam_questions(self, examination_id: str, student_id: str, reason: str, regenerated_by: str) -> Dict[str, Any]:
        """
        Regenerate exam questions for a student (for exceptional circumstances).
        
        Args:
            examination_id: Examination ID
            student_id: Student ID
            reason: Reason for regeneration
            regenerated_by: User who authorized regeneration
            
        Returns:
            New exam instance data
        """
        try:
            # Clear existing cached questions
            cache_key = f"exam_questions:{examination_id}:{student_id}"
            await self.cache.delete(cache_key)
            
            # Generate new questions
            new_instance = await self.generate_exam_questions(examination_id, student_id)
            
            # Log regeneration
            await self._log_audit_event(
                user_id=regenerated_by,
                action=AuditAction.UPDATE,
                resource_type="exam_instance_questions",
                resource_id=f"{examination_id}:{student_id}",
                new_values={
                    "reason": reason,
                    "new_seed": new_instance["seed"][:16] + "..."
                }
            )
            
            return new_instance
            
        except Exception as e:
            raise ValueError(f"Failed to regenerate exam questions: {str(e)}")
    
    async def get_randomisation_statistics(self, examination_id: str) -> Dict[str, Any]:
        """
        Get statistics about question randomisation for an examination.
        
        Args:
            examination_id: Examination ID
            
        Returns:
            Randomisation statistics
        """
        try:
            # Get examination details
            exam_result = await self.db.execute(
                select(Examination).where(Examination.id == examination_id)
            )
            exam = exam_result.scalar_one_or_none()
            if not exam:
                raise ValueError("Examination not found")
            
            # Get base questions
            base_questions = await self._get_exam_base_questions(examination_id)
            
            # Calculate theoretical randomisation possibilities
            statistics = {
                "examination_id": examination_id,
                "total_base_questions": len(base_questions),
                "randomization_enabled": {
                    "questions": exam.randomize_questions,
                    "options": exam.randomize_options,
                    "order": exam.randomize_questions
                },
                "theoretical_combinations": self._calculate_theoretical_combinations(base_questions, exam),
                "question_distribution": self._analyze_question_distribution(base_questions),
                "generated_at": datetime.utcnow()
            }
            
            return statistics
            
        except Exception as e:
            raise ValueError(f"Failed to get randomisation statistics: {str(e)}")
    
    # Private helper methods
    
    def _generate_student_exam_seed(self, examination_id: str, student_id: str) -> str:
        """
        Generate cryptographically secure seed for student-exam combination.
        
        Uses HKDF with SHA-256 to derive a deterministic but unpredictable seed
        from the examination ID, student ID, and a server secret.
        """
        # Combine inputs
        input_data = f"{examination_id}:{student_id}".encode('utf-8')
        
        # Add server secret (this should be stored securely)
        server_secret = "cbt-exam-randomisation-secret-2024".encode('utf-8')
        
        # Derive key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=None,
            info=b'CBT-Exam-Randomisation',
            backend=self.backend
        )
        
        seed = hkdf.derive(input_data + server_secret)
        
        # Convert to hex string for storage
        return seed.hex()
    
    async def _get_exam_base_questions(self, examination_id: str) -> List[Dict[str, Any]]:
        """Get base questions for examination from blueprint selection."""
        try:
            # Get exam questions from exam_questions table
            result = await self.db.execute(
                select(Question, ExamQuestion.question_order, ExamQuestion.points_override)
                .join(ExamQuestion, Question.id == ExamQuestion.question_id)
                .where(ExamQuestion.examination_id == examination_id)
                .order_by(ExamQuestion.question_order)
            )
            
            questions = []
            for row in result:
                question, question_order, points_override = row
                
                # Get question options
                options_result = await self.db.execute(
                    select(QuestionOption)
                    .where(QuestionOption.question_id == question.id)
                    .order_by(QuestionOption.order)
                )
                options = options_result.scalars().all()
                
                question_data = {
                    "id": question.id,
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "points_value": points_override or question.points_value,
                    "explanation": question.explanation,
                    "reference": question.reference,
                    "image_url": question.image_url,
                    "order": question_order,
                    "options": [
                        {
                            "id": opt.id,
                            "option_text": opt.option_text,
                            "is_correct": opt.is_correct,
                            "explanation": opt.explanation,
                            "order": opt.order
                        }
                        for opt in options
                    ]
                }
                
                questions.append(question_data)
            
            return questions
            
        except Exception as e:
            raise ValueError(f"Failed to get base questions: {str(e)}")
    
    async def _apply_question_randomisation(self, base_questions: List[Dict[str, Any]], seed: str, 
                                           randomize_questions: bool, randomize_options: bool) -> List[Dict[str, Any]]:
        """Apply randomisation to questions and options."""
        import random
        
        # Create deterministic random generator from seed
        seed_bytes = bytes.fromhex(seed)
        random_gen = random.Random(seed_bytes)
        
        randomised_questions = []
        
        if randomize_questions:
            # Shuffle question order
            shuffled_questions = base_questions.copy()
            random_gen.shuffle(shuffled_questions)
        else:
            shuffled_questions = base_questions
        
        # Apply option randomisation if enabled
        for question in shuffled_questions:
            question_copy = question.copy()
            
            if randomize_options and question["options"]:
                # Shuffle options but keep track of correct answer
                options = question["options"].copy()
                original_indices = [opt["order"] for opt in options]
                
                # Shuffle options
                random_gen.shuffle(options)
                
                # Update option orders and create mapping
                option_mapping = {}
                for new_order, opt in enumerate(options):
                    old_order = opt["order"]
                    opt["order"] = new_order + 1
                    option_mapping[old_order] = new_order + 1
                
                # Store mapping for answer verification
                question_copy["option_mapping"] = option_mapping
                question_copy["options"] = options
            else:
                question_copy["options"] = question["options"]
            
            randomised_questions.append(question_copy)
        
        return randomised_questions
    
    def _generate_question_order(self, questions: List[Dict[str, Any]], seed: str) -> List[int]:
        """Generate question order based on seed."""
        import random
        
        # Create deterministic random generator from seed
        seed_bytes = bytes.fromhex(seed)
        random_gen = random.Random(seed_bytes)
        
        # Generate order based on question IDs for consistency
        question_ids = [q["id"] for q in questions]
        
        # Create mapping from question ID to position
        id_to_position = {qid: i for i, qid in enumerate(question_ids)}
        
        # Shuffle positions
        positions = list(range(len(questions)))
        random_gen.shuffle(positions)
        
        return positions
    
    def _calculate_theoretical_combinations(self, questions: List[Dict[str, Any]], exam: Examination) -> Dict[str, Any]:
        """Calculate theoretical number of possible exam combinations."""
        import math
        
        total_questions = len(questions)
        
        # Question order combinations
        if exam.randomize_questions:
            question_order_combinations = math.factorial(total_questions)
        else:
            question_order_combinations = 1
        
        # Option randomisation combinations
        option_combinations = 1
        if exam.randomize_options:
            for question in questions:
                option_count = len(question["options"])
                if option_count > 1:
                    option_combinations *= math.factorial(option_count)
        
        # Total combinations
        total_combinations = question_order_combinations * option_combinations
        
        return {
            "total_questions": total_questions,
            "question_order_combinations": question_order_combinations,
            "option_combinations": option_combinations,
            "total_combinations": total_combinations,
            "entropy_bits": math.log2(total_combinations) if total_combinations > 0 else 0
        }
    
    def _analyze_question_distribution(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze distribution of question types and characteristics."""
        distribution = {
            "by_type": {},
            "by_points": {},
            "with_images": 0,
            "with_explanations": 0,
            "average_options": 0
        }
        
        total_options = 0
        
        for question in questions:
            # Count by type
            qtype = question["question_type"].value
            distribution["by_type"][qtype] = distribution["by_type"].get(qtype, 0) + 1
            
            # Count by points
            points = question["points_value"]
            distribution["by_points"][str(points)] = distribution["by_points"].get(str(points), 0) + 1
            
            # Count special features
            if question.get("image_url"):
                distribution["with_images"] += 1
            
            if question.get("explanation"):
                distribution["with_explanations"] += 1
            
            # Count options
            option_count = len(question.get("options", []))
            total_options += option_count
        
        if questions:
            distribution["average_options"] = total_options / len(questions)
        
        return distribution
    
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
