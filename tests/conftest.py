"""
Pytest configuration and fixtures for CBT testing suite.
"""

import os
from pathlib import Path
import sys

# Integration tests: point Beanie at a real Mongo before importing the app (see tests/integration/).
_mongo_url = os.environ.get("CBT_INTEGRATION_MONGO_URL")
if _mongo_url:
    os.environ["DATABASE_URL"] = _mongo_url

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock
from httpx import AsyncClient
import redis.asyncio as redis

# Ensure `src.*` imports resolve regardless of invocation cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cbt.core.database import get_db
from src.cbt.main import app


# Test database URL (MongoDB; tests may mock DB where needed)
TEST_DATABASE_URL = "mongodb://localhost:27017/cbt_test"

# Test Redis URL
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Legacy fixture kept for compatibility with existing tests."""
    yield None


@pytest.fixture
async def test_session(test_engine):
    """Provide lightweight async DB-like mock session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    yield session


@pytest.fixture
async def test_redis() -> AsyncGenerator[redis.Redis, None]:
    """Create test Redis client."""
    redis_client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    
    # Clear test database
    await redis_client.flushdb()
    
    yield redis_client
    
    # Clean up
    await redis_client.flushdb()
    await redis_client.close()


@pytest.fixture
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    # Override database dependency
    app.dependency_overrides[get_db] = lambda: test_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Remove override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test.user@university.edu",
        "full_name": "Test User",
        "password": "SecureTestPassword123!",
        "role": "student",
        "department": "Computer Science",
        "matric_number": "202400001"
    }


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "matric_number": "202400001",
        "full_name": "Test Student",
        "email": "test.student@university.edu",
        "department": "Computer Science",
        "level": "400",
        "program": "Computer Science",
        "admission_year": 2020,
        "expected_graduation": 2024
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "course_code": "CSC401",
        "course_title": "Advanced Software Engineering",
        "department": "Computer Science",
        "level": "400",
        "credit_units": 3,
        "semester": "second",
        "academic_session": "2023/2024",
        "description": "Advanced topics in software engineering"
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "question_text": "What is the primary purpose of software testing?",
        "question_type": "multiple_choice",
        "difficulty_level": "medium",
        "subject_area": "Software Engineering",
        "topic": "Testing",
        "points": 5,
        "options": [
            {"option_text": "To find bugs", "is_correct": True},
            {"option_text": "To write code", "is_correct": False},
            {"option_text": "To design systems", "is_correct": False},
            {"option_text": "To manage projects", "is_correct": False}
        ],
        "explanation": "Software testing is primarily conducted to find bugs and ensure software quality.",
        "tags": ["testing", "quality", "bugs"],
        "estimated_time_minutes": 2
    }


@pytest.fixture
def sample_examination_data():
    """Sample examination data for testing."""
    return {
        "title": "Software Engineering Final Examination",
        "description": "Comprehensive final exam covering all course topics",
        "course_code": "CSC401",
        "duration_minutes": 120,
        "total_points": 100,
        "exam_date": "2024-06-15",
        "start_time": "09:00:00",
        "exam_type": "final",
        "instructions": "Read all questions carefully. Manage your time effectively.",
        "allow_review": True,
        "show_results_immediately": False,
        "randomize_questions": True,
        "randomize_options": True
    }


@pytest.fixture
def sample_exam_blueprint_data():
    """Sample exam blueprint data for testing."""
    return {
        "examination_id": "test-exam-id",
        "title": "Software Engineering Exam Blueprint",
        "total_questions": 50,
        "total_points": 100,
        "duration_minutes": 120,
        "requirements": [
            {
                "subject_area": "Software Engineering",
                "difficulty_level": "easy",
                "question_count": 10,
                "points_per_question": 2
            },
            {
                "subject_area": "Software Engineering",
                "difficulty_level": "medium",
                "question_count": 30,
                "points_per_question": 2
            },
            {
                "subject_area": "Software Engineering",
                "difficulty_level": "hard",
                "question_count": 10,
                "points_per_question": 4
            }
        ]
    }


@pytest.fixture
async def authenticated_client(test_client: AsyncClient, sample_user_data: dict) -> AsyncClient:
    """Create an authenticated test client."""
    # Register user
    await test_client.post("/api/v1/auth/register", json=sample_user_data)
    
    # Login user
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    response = await test_client.post("/api/v1/auth/login", json=login_data)
    
    # Extract token
    token_data = response.json()
    token = token_data["access_token"]
    
    # Set authorization header
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return test_client


@pytest.fixture
async def admin_client(test_client: AsyncClient) -> AsyncClient:
    """Create an admin authenticated test client."""
    admin_data = {
        "email": "admin@university.edu",
        "full_name": "System Administrator",
        "password": "AdminPassword123!",
        "role": "admin",
        "department": "ICT"
    }
    
    # Register admin
    await test_client.post("/api/v1/auth/register", json=admin_data)
    
    # Login admin
    login_data = {
        "email": admin_data["email"],
        "password": admin_data["password"]
    }
    response = await test_client.post("/api/v1/auth/login", json=login_data)
    
    # Extract token
    token_data = response.json()
    token = token_data["access_token"]
    
    # Set authorization header
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return test_client


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        async def delete(self, *keys):
            for key in keys:
                self.data.pop(key, None)
            return len(keys)
        
        async def exists(self, key):
            return key in self.data
        
        async def flushdb(self):
            self.data.clear()
            return True
        
        async def close(self):
            pass
    
    mock_redis_instance = MockRedis()
    monkeypatch.setattr("src.cbt.core.redis.cache_manager", mock_redis_instance)
    
    return mock_redis_instance


@pytest.fixture
def load_test_config():
    """Load testing configuration."""
    return {
        "concurrent_users": 100,
        "duration_seconds": 300,
        "ramp_up_seconds": 30,
        "target_endpoints": [
            "/api/v1/auth/login",
            "/api/v1/questions",
            "/api/v1/examinations",
            "/api/v1/students/profile"
        ],
        "performance_thresholds": {
            "response_time_p95": 2000,  # milliseconds
            "response_time_p99": 4000,  # milliseconds
            "error_rate": 0.01,  # 1%
            "throughput_min": 50  # requests per second
        }
    }


@pytest.fixture
def performance_test_data():
    """Performance test data generator."""
    import random
    import string
    
    def generate_random_email():
        return f"{''.join(random.choices(string.ascii_lowercase, k=8))}@test.edu"
    
    def generate_random_password():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    return {
        "users": [
            {
                "email": generate_random_email(),
                "password": generate_random_password(),
                "full_name": f"Test User {i}"
            }
            for i in range(1000)
        ],
        "questions": [
            {
                "question_text": f"Test question {i}",
                "question_type": "multiple_choice",
                "difficulty_level": random.choice(["easy", "medium", "hard"]),
                "subject_area": "Test Subject",
                "points": random.randint(1, 5)
            }
            for i in range(500)
        ]
    }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security
pytest.mark.functional = pytest.mark.functional
pytest.mark.regression = pytest.mark.regression


# Custom pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "functional: mark test as functional test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit test marker for tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration test marker for tests in integration directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance test marker for tests in performance directory
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Add security test marker for tests in security directory
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add functional test marker for tests in functional directory
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)
        
        # Add regression test marker for tests in regression directory
        elif "regression" in str(item.fspath):
            item.add_marker(pytest.mark.regression)
