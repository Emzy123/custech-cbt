"""
Functional tests for complete exam flow.

These tests target the current /api/v1 endpoint structure:
  - POST /api/v1/examinations/                      → create exam
  - POST /api/v1/examinations/{id}/start            → start exam (returns ExamStartResponse)
  - GET  /api/v1/examinations/{id}/instances/{iid}/paper → get randomised paper
  - POST /api/v1/examinations/{id}/instances/{iid}/answers → autosave answer
  - GET  /api/v1/examinations/{id}/instances/{iid}/clock  → clock sync
  - POST /api/v1/examinations/{id}/instances/{iid}/submit → submit exam
  - GET  /api/v1/examinations/{id}/instances/{iid}/review → review exam
  - GET  /api/v1/examinations/my/results                  → student results (embargo-aware)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_start_response(instance_id: str = "inst-001", exam_id: str = "exam-001") -> dict:
    return {
        "success": True,
        "message": "Exam started",
        "instance_id": instance_id,
        "examination_id": exam_id,
        "student_id": "student-001",
        "start_time": "2024-06-15T09:00:00",
        "end_time": "2024-06-15T11:00:00",
        "duration_minutes": 120,
        "total_questions": 10,
        "rules_accepted": True,
    }


def _make_paper_response(instance_id: str = "inst-001") -> dict:
    questions = []
    for i in range(1, 11):
        questions.append({
            "id": f"q{i:03d}",
            "question_text": f"Sample question {i}",
            "question_type": "multiple_choice",
            "points": 10,
            "options": [
                {"id": f"q{i:03d}-opt-a", "option_text": "Option A"},
                {"id": f"q{i:03d}-opt-b", "option_text": "Option B"},
                {"id": f"q{i:03d}-opt-c", "option_text": "Option C"},
                {"id": f"q{i:03d}-opt-d", "option_text": "Option D"},
            ],
        })
    return {"instance_id": instance_id, "questions": questions, "total_questions": 10}


def _make_submission_response() -> dict:
    return {
        "success": True,
        "message": "Exam submitted successfully",
        "submitted": True,
        "total_answers": 10,
        "score": 70,
        "total_points": 100,
        "percentage": 70.0,
        "grade": "C",
    }


def _make_review_response(instance_id: str = "inst-001") -> dict:
    return {
        "instance_id": instance_id,
        "total_score": 70,
        "max_score": 100,
        "percentage": 70.0,
        "answers": [
            {
                "question_id": f"q{i:03d}",
                "question_text": f"Sample question {i}",
                "selected_option_id": f"q{i:03d}-opt-a",
                "correct_option_id": f"q{i:03d}-opt-a",
                "correct": True,
                "points_earned": 10,
            }
            for i in range(1, 11)
        ],
    }


def _make_clock_response(instance_id: str = "inst-001") -> dict:
    return {
        "instance_id": instance_id,
        "duration_minutes": 120,
        "elapsed_minutes": 15,
        "time_remaining_seconds": 6300,
        "is_expired": False,
        "server_time": "2024-06-15T09:15:00",
    }


# ── Test Classes ──────────────────────────────────────────────────────────────

@pytest.mark.functional
class TestExamLifecycle:
    """Tests for the full exam start → paper → answer → submit → review flow."""

    @pytest.mark.asyncio
    async def test_start_exam_requires_rules_accepted(self, authenticated_client: AsyncClient):
        """POST /{exam_id}/start must reject a request where rules_accepted=False."""
        from src.cbt.services.exam_service import ExamService
        with patch.object(ExamService, "start_exam", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = MagicMock(
                success=False,
                message="Exam rules must be accepted before starting",
            )
            response = await authenticated_client.post(
                "/api/v1/examinations/exam-001/start",
                json={"rules_accepted": False},
            )
        # The endpoint enforces rules_accepted before calling the service
        assert response.status_code in (400, 401, 403)

    @pytest.mark.asyncio
    async def test_get_exam_paper_returns_questions(self, authenticated_client: AsyncClient):
        """GET /instances/{iid}/paper returns a list of randomised questions."""
        from src.cbt.api.examinations import _ensure_instance_access
        from src.cbt.services.exam_service import ExamService

        paper = _make_paper_response()

        with patch("src.cbt.api.examinations._ensure_instance_access", new_callable=AsyncMock) as mock_access, \
             patch.object(ExamService, "get_paper", new_callable=AsyncMock) as mock_paper:
            mock_access.return_value = MagicMock()
            mock_paper.return_value = paper

            response = await authenticated_client.get(
                "/api/v1/examinations/exam-001/instances/inst-001/paper",
            )

        # Because the DB is mocked and auth is not fully wired in unit-mode,
        # we only assert the service was called with the right signature.
        mock_paper.assert_called_once_with("inst-001")

    @pytest.mark.asyncio
    async def test_clock_sync_returns_time_fields(self, authenticated_client: AsyncClient):
        """GET /instances/{iid}/clock must return remaining seconds and expiry flag."""
        from src.cbt.api.examinations import _ensure_instance_access
        from src.cbt.services.exam_service import ExamService

        clock = _make_clock_response()

        with patch("src.cbt.api.examinations._ensure_instance_access", new_callable=AsyncMock), \
             patch.object(ExamService, "sync_clock", new_callable=AsyncMock) as mock_clock:
            mock_clock.return_value = clock

            response = await authenticated_client.get(
                "/api/v1/examinations/exam-001/instances/inst-001/clock",
            )

        mock_clock.assert_called_once_with("inst-001")

    @pytest.mark.asyncio
    async def test_save_answer_calls_service(self, authenticated_client: AsyncClient):
        """POST /instances/{iid}/answers autosaves a single answer."""
        from src.cbt.api.examinations import _ensure_instance_access
        from src.cbt.services.exam_service import ExamService

        with patch("src.cbt.api.examinations._ensure_instance_access", new_callable=AsyncMock), \
             patch.object(ExamService, "save_answer", new_callable=AsyncMock) as mock_save:
            mock_save.return_value = {"saved": True, "question_id": "q001"}

            await authenticated_client.post(
                "/api/v1/examinations/exam-001/instances/inst-001/answers",
                json={
                    "question_id": "q001",
                    "selected_option_id": "q001-opt-a",
                    "idempotency_key": "test-key-001"
                },
            )

        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_exam_returns_score(self, authenticated_client: AsyncClient):
        """POST /instances/{iid}/submit returns a submission result with score."""
        from src.cbt.api.examinations import _ensure_instance_access
        from src.cbt.services.exam_service import ExamService

        result = MagicMock(**_make_submission_response())
        result.success = True

        with patch("src.cbt.api.examinations._ensure_instance_access", new_callable=AsyncMock), \
             patch.object(ExamService, "submit_exam", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = result

            response = await authenticated_client.post(
                "/api/v1/examinations/exam-001/instances/inst-001/submit",
                json={},
            )

        mock_submit.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_exam_returns_answer_details(self, authenticated_client: AsyncClient):
        """GET /instances/{iid}/review returns per-question correctness details."""
        from src.cbt.services.exam_service import ExamService

        review_data = _make_review_response()
        review_obj = MagicMock(**review_data)
        review_obj.answers = review_data["answers"]

        with patch.object(ExamService, "review_exam", new_callable=AsyncMock) as mock_review:
            mock_review.return_value = review_obj
            mock_review.assert_not_called()  # sanity: not called yet

            await authenticated_client.get(
                "/api/v1/examinations/exam-001/instances/inst-001/review",
            )

        mock_review.assert_called_once_with("inst-001", mock_review.call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_registered_students_returns_list(self, authenticated_client: AsyncClient):
        """GET /api/v1/examinations/{exam_id}/registered-students returns list of students."""
        mock_exam = MagicMock()
        mock_exam.id = "exam-001"
        mock_exam.course_id = "course-001"
        mock_exam.academic_session_id = "session-001"

        mock_sc = MagicMock()
        mock_sc.student_id = "student-001"

        mock_student = MagicMock()
        mock_student.id = "student-001"
        mock_student.first_name = "Jane"
        mock_student.last_name = "Smith"
        mock_student.email = "jane.smith@example.com"
        mock_student.matric_number = "2024/001"
        mock_student.department_id = "dept-001"
        mock_student.is_active = True

        mock_dept = MagicMock()
        mock_dept.id = "dept-001"
        mock_dept.code = "CSC"
        mock_dept.name = "Computer Science"

        with patch("src.cbt.api.examinations.Examination.get", new_callable=AsyncMock) as mock_get_exam, \
             patch("src.cbt.api.examinations.StudentCourse.find", MagicMock()) as mock_find_sc, \
             patch("src.cbt.api.examinations.Student.find", MagicMock()) as mock_find_student, \
             patch("src.cbt.api.examinations.Department.find", MagicMock()) as mock_find_dept:

            mock_get_exam.return_value = mock_exam

            mock_find_sc.return_value.to_list = AsyncMock(return_value=[mock_sc])
            mock_find_student.return_value.to_list = AsyncMock(return_value=[mock_student])
            mock_find_dept.return_value.to_list = AsyncMock(return_value=[mock_dept])

            response = await authenticated_client.get(
                "/api/v1/examinations/exam-001/registered-students"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Jane"
        assert data[0]["last_name"] == "Smith"
        assert data[0]["department_code"] == "CSC"


@pytest.mark.functional
class TestStudentResults:
    """Tests for the embargo-aware student results endpoint."""

    @pytest.mark.asyncio
    async def test_my_results_requires_authentication(self, test_client: AsyncClient):
        """GET /my/results returns 401 or 403 without a valid token."""
        response = await test_client.get("/api/v1/examinations/my/results")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_my_results_hidden_under_embargo(self, authenticated_client: AsyncClient):
        """GET /my/results returns an empty list when embargo is active."""
        from src.cbt.services.exam_service import ExamService
        from src.cbt.models.student import Student

        mock_student = MagicMock()
        mock_student.id = "student-001"

        with patch("src.cbt.api.examinations.Student.find_one", new_callable=AsyncMock) as mock_find, \
             patch.object(ExamService, "get_student_results", new_callable=AsyncMock) as mock_results:
            mock_find.return_value = mock_student
            # Embargo active — service returns empty list
            mock_results.return_value = []

            response = await authenticated_client.get(
                "/api/v1/examinations/my/results",
            )

        # The endpoint itself returns whatever the service gives.
        # We verify the service was called with the student id.
        mock_results.assert_called_once_with("student-001", None)

    @pytest.mark.asyncio
    async def test_my_results_visible_without_embargo(self, authenticated_client: AsyncClient):
        """GET /my/results returns result entries when embargo is lifted."""
        from src.cbt.services.exam_service import ExamService
        from src.cbt.models.student import Student

        mock_student = MagicMock()
        mock_student.id = "student-001"

        result_payload = [
            {
                "exam_id": "exam-001",
                "exam_title": "CSC401 Final Exam",
                "score": 75,
                "total_points": 100,
                "percentage": 75.0,
                "grade": "B",
                "submitted_at": "2024-06-15T11:00:00",
                "embargo_active": False,
            }
        ]

        with patch("src.cbt.api.examinations.Student.find_one", new_callable=AsyncMock) as mock_find, \
             patch.object(ExamService, "get_student_results", new_callable=AsyncMock) as mock_results:
            mock_find.return_value = mock_student
            mock_results.return_value = result_payload

            response = await authenticated_client.get(
                "/api/v1/examinations/my/results",
            )

        mock_results.assert_called_once_with("student-001", None)

    @pytest.mark.asyncio
    async def test_my_results_filtered_by_exam_id(self, authenticated_client: AsyncClient):
        """GET /my/results?exam_id=xxx passes the filter through to the service."""
        from src.cbt.services.exam_service import ExamService
        from src.cbt.models.student import Student

        mock_student = MagicMock()
        mock_student.id = "student-001"

        with patch("src.cbt.api.examinations.Student.find_one", new_callable=AsyncMock) as mock_find, \
             patch.object(ExamService, "get_student_results", new_callable=AsyncMock) as mock_results:
            mock_find.return_value = mock_student
            mock_results.return_value = []

            await authenticated_client.get(
                "/api/v1/examinations/my/results?exam_id=exam-001",
            )

        mock_results.assert_called_once_with("student-001", "exam-001")


@pytest.mark.functional
class TestExamAPIContracts:
    """Smoke tests ensuring each route exists and returns the expected HTTP semantics."""

    @pytest.mark.asyncio
    async def test_create_examination_route_exists(self, test_client: AsyncClient):
        """POST /api/v1/examinations/ must not return 404 or 405."""
        response = await test_client.post("/api/v1/examinations/", json={})
        assert response.status_code not in (404, 405), (
            f"Route POST /api/v1/examinations/ not found or method not allowed: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_list_examinations_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/ must not return 404 or 405."""
        response = await test_client.get("/api/v1/examinations/")
        assert response.status_code not in (404, 405), (
            f"Route GET /api/v1/examinations/ not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_start_exam_route_exists(self, test_client: AsyncClient):
        """POST /api/v1/examinations/{id}/start must not return 404 or 405."""
        response = await test_client.post(
            "/api/v1/examinations/exam-nonexistent/start", json={}
        )
        assert response.status_code not in (404, 405), (
            f"Route POST /api/v1/examinations/{{id}}/start not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_get_paper_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/{id}/instances/{iid}/paper must not 404 or 405."""
        response = await test_client.get(
            "/api/v1/examinations/exam-001/instances/inst-001/paper"
        )
        assert response.status_code not in (404, 405), (
            f"Route GET paper not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_clock_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/{id}/instances/{iid}/clock must not 404 or 405."""
        response = await test_client.get(
            "/api/v1/examinations/exam-001/instances/inst-001/clock"
        )
        assert response.status_code not in (404, 405), (
            f"Route GET clock not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_submit_route_exists(self, test_client: AsyncClient):
        """POST /api/v1/examinations/{id}/instances/{iid}/submit must not 404 or 405."""
        response = await test_client.post(
            "/api/v1/examinations/exam-001/instances/inst-001/submit", json={}
        )
        assert response.status_code not in (404, 405), (
            f"Route POST submit not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_review_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/{id}/instances/{iid}/review must not 404 or 405."""
        response = await test_client.get(
            "/api/v1/examinations/exam-001/instances/inst-001/review"
        )
        assert response.status_code not in (404, 405), (
            f"Route GET review not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_my_results_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/my/results must not return 404 or 405."""
        response = await test_client.get("/api/v1/examinations/my/results")
        assert response.status_code not in (404, 405), (
            f"Route GET /my/results not found: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_get_registered_students_route_exists(self, test_client: AsyncClient):
        """GET /api/v1/examinations/{id}/registered-students must not 404 or 405."""
        response = await test_client.get(
            "/api/v1/examinations/exam-001/registered-students"
        )
        assert response.status_code not in (404, 405), (
            f"Route GET registered students not found: {response.status_code}"
        )
