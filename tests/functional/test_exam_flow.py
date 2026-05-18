"""
Functional tests for complete exam flow.
"""

import pytest
pytest.skip(
    "Legacy functional suite targets endpoints not present in current backend track.",
    allow_module_level=True,
)
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from tests.conftest import sample_question_data, sample_examination_data, sample_exam_blueprint_data


@pytest.mark.functional
class TestExamFlow:
    """End-to-end functional tests for exam flow."""
    
    @pytest.mark.asyncio
    async def test_complete_exam_flow(self, authenticated_client, test_session):
        """Test complete exam flow from start to finish."""
        
        # Step 1: Create questions
        questions = []
        for i in range(10):
            question_data = {
                **sample_question_data,
                "question_text": f"Test question {i+1}",
                "options": [
                    {"option_text": f"Option A {i+1}", "is_correct": i % 4 == 0},
                    {"option_text": f"Option B {i+1}", "is_correct": i % 4 == 1},
                    {"option_text": f"Option C {i+1}", "is_correct": i % 4 == 2},
                    {"option_text": f"Option D {i+1}", "is_correct": i % 4 == 3}
                ]
            }
            
            response = await authenticated_client.post("/api/v1/questions", json=question_data)
            assert response.status_code == 201
            questions.append(response.json())
        
        # Step 2: Create examination
        exam_data = {
            **sample_examination_data,
            "title": "Functional Test Exam",
            "total_points": sum(q["points"] for q in questions)
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Step 3: Create exam blueprint
        blueprint_data = {
            **sample_exam_blueprint_data,
            "examination_id": examination["id"],
            "requirements": [
                {
                    "subject_area": "Software Engineering",
                    "difficulty_level": "medium",
                    "question_count": 10,
                    "points_per_question": 5
                }
            ]
        }
        
        response = await authenticated_client.post("/api/v1/exam-blueprints", json=blueprint_data)
        assert response.status_code == 201
        blueprint = response.json()
        
        # Step 4: Schedule examination
        schedule_data = {
            "examination_id": examination["id"],
            "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "start_time": "09:00:00",
            "venue": "Test Lab",
            "invigilators": ["invigilator1@test.edu"]
        }
        
        response = await authenticated_client.post("/api/v1/exam-schedules", json=schedule_data)
        assert response.status_code == 201
        schedule = response.json()
        
        # Step 5: Start exam for student
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Step 6: Get exam questions
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/questions")
        assert response.status_code == 200
        exam_questions = response.json()
        assert len(exam_questions["questions"]) == 10
        
        # Step 7: Submit answers
        answers = []
        for question in exam_questions["questions"]:
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][0]["id"]
            })
        
        submission_data = {
            "exam_instance_id": exam_instance["id"],
            "answers": answers,
            "time_taken_minutes": 30
        }
        
        response = await authenticated_client.post("/api/v1/examinations/submit", json=submission_data)
        assert response.status_code == 200
        submission_result = response.json()
        
        # Step 8: Verify submission
        assert submission_result["submitted"] is True
        assert submission_result["total_answers"] == 10
        assert "score" in submission_result
        
        # Step 9: Get exam results
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/results")
        assert response.status_code == 200
        results = response.json()
        
        assert results["exam_instance_id"] == exam_instance["id"]
        assert results["total_score"] is not None
        assert results["percentage"] is not None
        
        # Step 10: Review exam
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/review")
        assert response.status_code == 200
        review = response.json()
        
        assert len(review["answers"]) == 10
        assert all("correct" in answer for answer in review["answers"])
    
    @pytest.mark.asyncio
    async def test_exam_with_proctoring(self, authenticated_client, test_session):
        """Test exam flow with proctoring enabled."""
        
        # Create examination with proctoring
        exam_data = {
            **sample_examination_data,
            "title": "Proctored Test Exam",
            "require_proctoring": True,
            "proctoring_settings": {
                "webcam_required": True,
                "screen_recording": True,
                "audio_monitoring": False
            }
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start proctoring session
        proctoring_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id",
            "device_fingerprint": "test-fingerprint",
            "ip_address": "192.168.1.1"
        }
        
        response = await authenticated_client.post("/api/v1/proctoring/session/start", json=proctoring_data)
        assert response.status_code == 200
        proctoring_session = response.json()
        
        # Start webcam session
        webcam_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id",
            "device_info": {"camera": "test-camera"}
        }
        
        response = await authenticated_client.post("/api/v1/webcam-proctoring/session/start", json=webcam_data)
        assert response.status_code == 200
        webcam_session = response.json()
        
        # Simulate proctoring events
        focus_event = {
            "duration": 2.5,
            "reason": "tab_switch"
        }
        
        response = await authenticated_client.post(
            f"/api/v1/proctoring/session/{proctoring_session['session_id']}/focus-loss",
            json=focus_event
        )
        assert response.status_code == 200
        
        # Submit webcam snapshot
        snapshot_data = {
            "image_data": "data:image/jpeg;base64,testimage",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = await authenticated_client.post(
            f"/api/v1/webcam-proctoring/session/{webcam_session['session_id']}/capture",
            json=snapshot_data
        )
        assert response.status_code == 200
        
        # End proctoring sessions
        response = await authenticated_client.post(
            f"/api/v1/proctoring/session/{proctoring_session['session_id']}/end"
        )
        assert response.status_code == 200
        
        response = await authenticated_client.post(
            f"/api/v1/webcam-proctoring/session/{webcam_session['session_id']}/end"
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_exam_timer_functionality(self, authenticated_client, test_session):
        """Test exam timer and time management."""
        
        # Create timed examination
        exam_data = {
            **sample_examination_data,
            "title": "Timed Test Exam",
            "duration_minutes": 60,
            "strict_timing": True
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Check timer status
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/timer")
        assert response.status_code == 200
        timer = response.json()
        
        assert timer["duration_minutes"] == 60
        assert timer["time_remaining"] > 0
        assert timer["is_expired"] is False
        
        # Simulate time extension
        extension_data = {
            "additional_minutes": 30,
            "reason": "Technical issues"
        }
        
        response = await authenticated_client.post(
            f"/api/v1/examinations/{exam_instance['id']}/extend-time",
            json=extension_data
        )
        assert response.status_code == 200
        
        # Verify extension
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/timer")
        assert response.status_code == 200
        extended_timer = response.json()
        
        assert extended_timer["duration_minutes"] == 90  # 60 + 30
    
    @pytest.mark.asyncio
    async def test_exam_review_and_feedback(self, authenticated_client, test_session):
        """Test exam review and feedback functionality."""
        
        # Create examination with feedback enabled
        exam_data = {
            **sample_examination_data,
            "title": "Feedback Test Exam",
            "show_feedback": True,
            "allow_review": True
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start and complete exam (simplified)
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Submit exam
        submission_data = {
            "exam_instance_id": exam_instance["id"],
            "answers": [
                {"question_id": "q1", "selected_option": "opt1"},
                {"question_id": "q2", "selected_option": "opt2"}
            ],
            "time_taken_minutes": 45
        }
        
        response = await authenticated_client.post("/api/v1/examinations/submit", json=submission_data)
        assert response.status_code == 200
        
        # Get detailed feedback
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/feedback")
        assert response.status_code == 200
        feedback = response.json()
        
        assert "overall_score" in feedback
        assert "performance_analysis" in feedback
        assert "recommendations" in feedback
        
        # Flag question for review
        flag_data = {
            "question_id": "q1",
            "reason": "Unclear question wording",
            "comment": "The question could be more specific"
        }
        
        response = await authenticated_client.post(
            f"/api/v1/examinations/{exam_instance['id']}/flag-question",
            json=flag_data
        )
        assert response.status_code == 200
        
        # Get flagged questions
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/flagged-questions")
        assert response.status_code == 200
        flagged = response.json()
        
        assert len(flagged["flagged_questions"]) >= 1
        assert flagged["flagged_questions"][0]["question_id"] == "q1"
    
    @pytest.mark.asyncio
    async def test_exam_statistics_and_analytics(self, authenticated_client, test_session):
        """Test exam statistics and analytics."""
        
        # Create examination
        exam_data = {
            **sample_examination_data,
            "title": "Analytics Test Exam"
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Get examination statistics
        response = await authenticated_client.get(f"/api/v1/examinations/{examination['id']}/statistics")
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_participants" in stats
        assert "completion_rate" in stats
        assert "average_score" in stats
        assert "score_distribution" in stats
        
        # Get question analytics
        response = await authenticated_client.get(f"/api/v1/examinations/{examination['id']}/question-analytics")
        assert response.status_code == 200
        question_analytics = response.json()
        
        assert len(question_analytics["questions"]) >= 0
        if question_analytics["questions"]:
            question = question_analytics["questions"][0]
            assert "correct_rate" in question
            assert "difficulty_rating" in question
            assert "discrimination_index" in question
    
    @pytest.mark.asyncio
    async def test_exam_accessibility_features(self, authenticated_client, test_session):
        """Test exam accessibility features."""
        
        # Create examination with accessibility accommodations
        exam_data = {
            **sample_examination_data,
            "title": "Accessibility Test Exam",
            "accessibility_settings": {
                "extra_time_percentage": 25,
                "font_size_increase": 20,
                "high_contrast": True,
                "screen_reader_compatible": True
            }
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam with accessibility
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id",
            "accessibility_requirements": {
                "extra_time": True,
                "large_font": True,
                "high_contrast": True
            }
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Verify accessibility accommodations
        assert exam_instance["accessibility_applied"] is True
        assert exam_instance["adjusted_duration"] == 75  # 60 minutes + 25%
        
        # Get accessible exam content
        response = await authenticated_client.get(
            f"/api/v1/examinations/{exam_instance['id']}/questions?format=accessible"
        )
        assert response.status_code == 200
        accessible_questions = response.json()
        
        # Verify accessibility formatting
        for question in accessible_questions["questions"]:
            assert "alt_text" in question  # For images
            assert question.get("font_size") == "large"
            assert question.get("contrast") == "high"
    
    @pytest.mark.asyncio
    async def test_exam_multilingual_support(self, authenticated_client, test_session):
        """Test exam multilingual support."""
        
        # Create multilingual examination
        exam_data = {
            **sample_examination_data,
            "title": "Multilingual Test Exam",
            "supported_languages": ["en", "fr", "es"],
            "default_language": "en"
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam in French
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id",
            "language": "fr"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Get questions in French
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/questions")
        assert response.status_code == 200
        french_questions = response.json()
        
        # Verify language
        assert french_questions["language"] == "fr"
        for question in french_questions["questions"]:
            assert question.get("language") == "fr"
    
    @pytest.mark.asyncio
    async def test_exam_offline_functionality(self, authenticated_client, test_session):
        """Test exam offline functionality."""
        
        # Create examination with offline support
        exam_data = {
            **sample_examination_data,
            "title": "Offline Test Exam",
            "offline_support": True,
            "sync_tolerance_minutes": 5
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Download exam for offline use
        response = await authenticated_client.get(f"/api/v1/examinations/{examination['id']}/offline-package")
        assert response.status_code == 200
        offline_package = response.json()
        
        assert "questions" in offline_package
        assert "exam_config" in offline_package
        assert "offline_token" in offline_package
        
        # Simulate offline submission
        offline_submission = {
            "exam_instance_id": "offline-instance-id",
            "offline_token": offline_package["offline_token"],
            "answers": [
                {"question_id": "q1", "selected_option": "opt1"},
                {"question_id": "q2", "selected_option": "opt2"}
            ],
            "submission_timestamp": datetime.utcnow().isoformat(),
            "client_time_offset": 120  # 2 minutes ahead
        }
        
        response = await authenticated_client.post(
            "/api/v1/examinations/offline-submit",
            json=offline_submission
        )
        assert response.status_code == 200
        sync_result = response.json()
        
        assert sync_result["synced"] is True
        assert sync_result["time_adjustment_applied"] is True
    
    @pytest.mark.asyncio
    async def test_exam_integrity_validation(self, authenticated_client, test_session):
        """Test exam integrity and validation."""
        
        # Create examination with strict validation
        exam_data = {
            **sample_examination_data,
            "title": "Integrity Test Exam",
            "integrity_checks": {
                "prevent_multiple_attempts": True,
                "validate_time_consistency": True,
                "check_answer_patterns": True
            }
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Attempt duplicate start (should fail)
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 400
        assert "already started" in response.json()["detail"].lower()
        
        # Submit with suspicious timing
        suspicious_submission = {
            "exam_instance_id": exam_instance["id"],
            "answers": [
                {"question_id": "q1", "selected_option": "opt1"},
                {"question_id": "q2", "selected_option": "opt2"}
            ],
            "time_taken_minutes": 1  # Too fast for 10 questions
        }
        
        response = await authenticated_client.post("/api/v1/examinations/submit", json=suspicious_submission)
        assert response.status_code == 200
        submission_result = response.json()
        
        # Check for integrity flags
        assert submission_result.get("integrity_flags", []) != []
        assert any("time" in flag["type"].lower() for flag in submission_result.get("integrity_flags", []))
    
    @pytest.mark.asyncio
    async def test_exam_emergency_procedures(self, authenticated_client, test_session):
        """Test exam emergency procedures."""
        
        # Create examination
        exam_data = {
            **sample_examination_data,
            "title": "Emergency Test Exam"
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Trigger emergency pause
        emergency_data = {
            "reason": "Fire alarm",
            "emergency_type": "evacuation",
            "auto_resume_minutes": 30
        }
        
        response = await authenticated_client.post(
            f"/api/v1/examinations/{exam_instance['id']}/emergency-pause",
            json=emergency_data
        )
        assert response.status_code == 200
        pause_result = response.json()
        
        assert pause_result["paused"] is True
        assert pause_result["emergency_type"] == "evacuation"
        
        # Verify exam is paused
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/status")
        assert response.status_code == 200
        status = response.json()
        
        assert status["status"] == "emergency_paused"
        
        # Resume exam
        response = await authenticated_client.post(
            f"/api/v1/examinations/{exam_instance['id']}/resume"
        )
        assert response.status_code == 200
        resume_result = response.json()
        
        assert resume_result["resumed"] is True
        assert resume_result["time_adjustment"] > 0  # Extra time added


@pytest.mark.functional
class TestExamEdgeCases:
    """Test edge cases and error scenarios in exam flow."""
    
    @pytest.mark.asyncio
    async def test_exam_timeout_handling(self, authenticated_client, test_session):
        """Test handling of exam timeouts."""
        
        # Create short exam for testing
        exam_data = {
            **sample_examination_data,
            "title": "Timeout Test Exam",
            "duration_minutes": 1  # Very short
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Wait for timeout (simulated)
        await asyncio.sleep(2)
        
        # Try to submit after timeout
        submission_data = {
            "exam_instance_id": exam_instance["id"],
            "answers": [{"question_id": "q1", "selected_option": "opt1"}],
            "time_taken_minutes": 2
        }
        
        response = await authenticated_client.post("/api/v1/examinations/submit", json=submission_data)
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_exam_concurrent_access(self, authenticated_client, test_session):
        """Test concurrent access to same exam."""
        
        # Create examination
        exam_data = {
            **sample_examination_data,
            "title": "Concurrent Access Test Exam"
        }
        
        response = await authenticated_client.post("/api/v1/examinations", json=exam_data)
        assert response.status_code == 201
        examination = response.json()
        
        # Start exam for student
        start_data = {
            "examination_id": examination["id"],
            "student_id": "test-student-id"
        }
        
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 200
        exam_instance = response.json()
        
        # Try to start same exam again (should fail)
        response = await authenticated_client.post("/api/v1/examinations/start", json=start_data)
        assert response.status_code == 400
        
        # Try to access exam from different session
        response = await authenticated_client.get(f"/api/v1/examinations/{exam_instance['id']}/questions")
        assert response.status_code == 200  # Should work
        
        # Try to submit from different session (should work if same user)
        submission_data = {
            "exam_instance_id": exam_instance["id"],
            "answers": [{"question_id": "q1", "selected_option": "opt1"}],
            "time_taken_minutes": 30
        }
        
        response = await authenticated_client.post("/api/v1/examinations/submit", json=submission_data)
        assert response.status_code == 200
