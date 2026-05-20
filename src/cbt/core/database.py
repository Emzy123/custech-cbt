"""
Database configuration and connection management for CBT system using MongoDB and Beanie.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# Global instances
client: Optional[AsyncIOMotorClient] = None

async def init_db():
    """Initialize MongoDB connection and Beanie documents."""
    global client
    try:
        # Create Motor client
        mongodb_url = settings.database_url or "mongodb://localhost:27017"
        if not str(mongodb_url).lower().startswith("mongodb"):
            raise ValueError(
                "DATABASE_URL must use the mongodb:// or mongodb+srv:// scheme."
            )

        client = AsyncIOMotorClient(
            mongodb_url,
            uuidRepresentation="standard"
        )
        
        # Select database
        database = client[settings.database_name]
        
        # Initialize Beanie
        from beanie import init_beanie
        
        # Import all models here to avoid circular imports
        from ..models.user import User, UserRoleAssignment
        from ..models.academic import AcademicSession, Semester, Department, Course, CourseDepartment, LecturerCourse
        from ..models.student import Student, StudentCourse
        from ..models.question import QuestionBank, Question, QuestionOption, QuestionAnswer
        from ..models.exam import Examination, ExamQuestion, ExamInstance, ExamAnswer
        from ..models.venue import Venue, ExamVenueAssignment
        from ..models.security import (
            UserSession,
            AuditLog,
            SecurityEvent,
            SecurityScan,
            Vulnerability,
        )
        from ..models.biometric import (
            BiometricTemplate,
            BiometricVerification,
            BiometricDevice,
            BiometricSession,
            BiometricAnomaly,
            BiometricConfiguration,
            BiometricAuditLog,
        )

        # Add models to Beanie
        document_models = [
            User, UserRoleAssignment, Department, Course, CourseDepartment, LecturerCourse,
            AcademicSession, Semester, Student, StudentCourse,
            QuestionBank, Question, QuestionOption, QuestionAnswer,
            Examination, ExamQuestion, ExamInstance, ExamAnswer,
            Venue, ExamVenueAssignment,
            UserSession, AuditLog, SecurityEvent, SecurityScan, Vulnerability,
            BiometricTemplate, BiometricVerification, BiometricDevice,
            BiometricSession, BiometricAnomaly, BiometricConfiguration,
            BiometricAuditLog,
        ]
        
        await init_beanie(database=database, document_models=document_models)
        
        logger.info("MongoDB and Beanie initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

async def check_db_connection() -> bool:
    """Check database connection health."""
    global client
    try:
        if client is None:
            return False
        await client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

class DatabaseManager:
    """Database connection and session management (Legacy wrapper)."""
    
    async def health_check(self) -> dict:
        is_healthy = await check_db_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": settings.database_name,
            "host": settings.database_host,
            "port": settings.database_port
        }
        
    async def close(self):
        await close_db()

# Global database manager instance
db_manager = DatabaseManager()

# Legacy dependency injection generator for endpoints requiring a DB session
# In MongoDB with Beanie, documents manage their own sessions (or use global context)
async def get_db():
    """Dependency function for MongoDB (placeholder for legacy compatibility)."""
    yield None
