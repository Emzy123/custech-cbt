"""
Cryptographically secure question selection and randomisation service.
"""

import secrets
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from ..models.question import Question, QuestionOption, QuestionType, QuestionStatus
from ..models.exam import Examination, ExamQuestion
from ..models.security import AuditLog, AuditAction
from ..core.redis import cache_manager
from ..core.config import settings


class QuestionRandomisationService:
    """Cryptographically secure question selection and randomisation service."""

    def __init__(self, db: Any = None):
        # db kept for backwards-compat; all queries go through Beanie document API.
        self.db = db
        self.cache = cache_manager
        self.backend = default_backend()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_exam_questions(self, examination_id: str, student_id: str) -> Dict[str, Any]:
        """Generate personalised exam questions for a student with cryptographically secure randomisation."""
        try:
            exam = await Examination.get(examination_id)
            if not exam:
                raise ValueError("Examination not found")

            seed = self._generate_student_exam_seed(examination_id, student_id)

            base_questions = await self._get_exam_base_questions(examination_id)
            if not base_questions:
                raise ValueError("No questions found for examination")

            randomised_questions = await self._apply_question_randomisation(
                base_questions, seed, exam.randomize_questions, exam.randomize_options
            )

            if exam.randomize_questions:
                question_order = self._generate_question_order(randomised_questions, seed)
            else:
                question_order = list(range(len(randomised_questions)))

            exam_instance = {
                "examination_id": examination_id,
                "student_id": student_id,
                "seed": seed,
                "questions": randomised_questions,
                "question_order": question_order,
                "total_questions": len(randomised_questions),
                "generated_at": datetime.utcnow().isoformat(),
                "randomisation_applied": {
                    "questions_randomized": exam.randomize_questions,
                    "options_randomized": exam.randomize_options,
                    "order_randomized": exam.randomize_questions,
                },
            }

            cache_key = f"exam_questions:{examination_id}:{student_id}"
            ttl = exam.duration_minutes * 60 + 300
            await self.cache.set(cache_key, exam_instance, ttl=ttl)

            await self._log_audit_event(
                user_id=student_id,
                action=AuditAction.EXAM_START,
                resource_type="exam_instance_questions",
                resource_id=f"{examination_id}:{student_id}",
                new_values={
                    "examination_id": examination_id,
                    "question_count": len(randomised_questions),
                    "seed_preview": seed[:16] + "...",
                },
            )

            return exam_instance

        except Exception as e:
            raise ValueError(f"Failed to generate exam questions: {str(e)}")

    async def get_student_exam_questions(self, examination_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve previously generated exam questions for a student from cache."""
        try:
            cache_key = f"exam_questions:{examination_id}:{student_id}"
            return await self.cache.get(cache_key)
        except Exception as e:
            raise ValueError(f"Failed to get exam questions: {str(e)}")

    async def verify_question_integrity(
        self,
        examination_id: str,
        student_id: str,
        provided_answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Verify submitted answers against the original question set."""
        try:
            exam_instance = await self.get_student_exam_questions(examination_id, student_id)
            if not exam_instance:
                raise ValueError("Exam instance not found")

            result: Dict[str, Any] = {
                "is_valid": True,
                "verification_errors": [],
                "missing_answers": [],
                "invalid_answers": [],
                "answer_count_mismatch": False,
            }

            if len(provided_answers) != exam_instance["total_questions"]:
                result["answer_count_mismatch"] = True
                result["verification_errors"].append(
                    f"Answer count mismatch: expected {exam_instance['total_questions']}, got {len(provided_answers)}"
                )

            provided_qids = set()
            expected_qids = {q["id"] for q in exam_instance["questions"]}

            for answer in provided_answers:
                qid = answer.get("question_id")
                if not qid:
                    result["invalid_answers"].append({"answer": answer, "error": "Missing question_id"})
                    continue
                provided_qids.add(qid)
                if qid not in expected_qids:
                    result["invalid_answers"].append({"question_id": qid, "error": "Question not part of this exam instance"})

            missing = expected_qids - provided_qids
            if missing:
                result["missing_answers"] = list(missing)
                result["verification_errors"].append(f"Missing answers for {len(missing)} questions")

            result["is_valid"] = not any([result["verification_errors"], result["invalid_answers"], result["missing_answers"]])

            return result
        except Exception as e:
            raise ValueError(f"Failed to verify question integrity: {str(e)}")

    async def regenerate_exam_questions(
        self,
        examination_id: str,
        student_id: str,
        reason: str,
        regenerated_by: str,
    ) -> Dict[str, Any]:
        """Regenerate exam questions for a student (exceptional circumstances only)."""
        try:
            cache_key = f"exam_questions:{examination_id}:{student_id}"
            await self.cache.delete(cache_key)

            new_instance = await self.generate_exam_questions(examination_id, student_id)

            await self._log_audit_event(
                user_id=regenerated_by,
                action=AuditAction.SYSTEM_CHANGE,
                resource_type="exam_instance_questions",
                resource_id=f"{examination_id}:{student_id}",
                new_values={"reason": reason, "new_seed_preview": new_instance["seed"][:16] + "..."},
            )
            return new_instance
        except Exception as e:
            raise ValueError(f"Failed to regenerate exam questions: {str(e)}")

    async def get_randomisation_statistics(self, examination_id: str) -> Dict[str, Any]:
        """Get statistics about question randomisation for an examination."""
        try:
            exam = await Examination.get(examination_id)
            if not exam:
                raise ValueError("Examination not found")

            base_questions = await self._get_exam_base_questions(examination_id)

            return {
                "examination_id": examination_id,
                "total_base_questions": len(base_questions),
                "randomization_enabled": {
                    "questions": exam.randomize_questions,
                    "options": exam.randomize_options,
                    "order": exam.randomize_questions,
                },
                "theoretical_combinations": self._calculate_theoretical_combinations(base_questions, exam),
                "question_distribution": self._analyze_question_distribution(base_questions),
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            raise ValueError(f"Failed to get randomisation statistics: {str(e)}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_student_exam_seed(self, examination_id: str, student_id: str) -> str:
        """Derive a cryptographically secure, deterministic seed for a student-exam pair."""
        input_data = f"{examination_id}:{student_id}".encode("utf-8")
        server_secret = settings.randomisation_secret.encode("utf-8")

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"CBT-Exam-Randomisation",
            backend=self.backend,
        )
        seed = hkdf.derive(input_data + server_secret)
        return seed.hex()

    async def _get_exam_base_questions(self, examination_id: str) -> List[Dict[str, Any]]:
        """Fetch base questions for an examination via Beanie."""
        try:
            exam_questions = await ExamQuestion.find(
                {"examination_id": examination_id}
            ).sort("question_order").to_list()

            questions = []
            for eq in exam_questions:
                question = await Question.get(eq.question_id)
                if not question:
                    continue

                options = await QuestionOption.find(
                    {"question_id": eq.question_id}
                ).sort("option_order").to_list()

                questions.append({
                    "id": str(question.id),
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "points_value": eq.points_override or question.points_value,
                    "explanation": question.explanation,
                    "reference": question.reference,
                    "image_url": question.image_url,
                    "order": eq.question_order,
                    "options": [
                        {
                            "id": str(opt.id),
                            "option_text": opt.option_text,
                            "is_correct": opt.is_correct,
                            "explanation": opt.explanation,
                            "order": opt.option_order,
                        }
                        for opt in options
                    ],
                })

            return questions
        except Exception as e:
            raise ValueError(f"Failed to get base questions: {str(e)}")

    async def _apply_question_randomisation(
        self,
        base_questions: List[Dict[str, Any]],
        seed: str,
        randomize_questions: bool,
        randomize_options: bool,
    ) -> List[Dict[str, Any]]:
        """Shuffle questions and/or options deterministically from seed."""
        import random

        seed_bytes = bytes.fromhex(seed)
        rng = random.Random(seed_bytes)

        pool = base_questions.copy()
        if randomize_questions:
            rng.shuffle(pool)

        randomised = []
        for question in pool:
            q_copy = question.copy()
            if randomize_options and question.get("options"):
                opts = question["options"].copy()
                rng.shuffle(opts)
                mapping = {}
                for new_idx, opt in enumerate(opts):
                    old_order = opt["order"]
                    opt = dict(opt)
                    opt["order"] = new_idx + 1
                    mapping[old_order] = new_idx + 1
                    opts[new_idx] = opt
                q_copy["option_mapping"] = mapping
                q_copy["options"] = opts
            randomised.append(q_copy)

        return randomised

    def _generate_question_order(self, questions: List[Dict[str, Any]], seed: str) -> List[int]:
        """Return a shuffled list of positional indices."""
        import random

        seed_bytes = bytes.fromhex(seed)
        rng = random.Random(seed_bytes)
        positions = list(range(len(questions)))
        rng.shuffle(positions)
        return positions

    def _calculate_theoretical_combinations(self, questions: List[Dict[str, Any]], exam: Examination) -> Dict[str, Any]:
        import math

        n = len(questions)
        q_combos = math.factorial(n) if exam.randomize_questions else 1
        opt_combos = 1
        if exam.randomize_options:
            for q in questions:
                oc = len(q.get("options", []))
                if oc > 1:
                    opt_combos *= math.factorial(oc)

        total = q_combos * opt_combos
        return {
            "total_questions": n,
            "question_order_combinations": q_combos,
            "option_combinations": opt_combos,
            "total_combinations": total,
            "entropy_bits": math.log2(total) if total > 0 else 0,
        }

    def _analyze_question_distribution(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        dist: Dict[str, Any] = {"by_type": {}, "by_points": {}, "with_images": 0, "with_explanations": 0, "average_options": 0}
        total_opts = 0
        for q in questions:
            qtype = q["question_type"].value if hasattr(q["question_type"], "value") else str(q["question_type"])
            dist["by_type"][qtype] = dist["by_type"].get(qtype, 0) + 1
            pts = str(q["points_value"])
            dist["by_points"][pts] = dist["by_points"].get(pts, 0) + 1
            if q.get("image_url"):
                dist["with_images"] += 1
            if q.get("explanation"):
                dist["with_explanations"] += 1
            total_opts += len(q.get("options", []))
        if questions:
            dist["average_options"] = total_opts / len(questions)
        return dist

    async def _log_audit_event(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        new_values: Optional[Dict] = None,
        old_values: Optional[Dict] = None,
    ):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=new_values,
                old_values=old_values,
            )
            await audit.insert()
        except Exception:
            pass
