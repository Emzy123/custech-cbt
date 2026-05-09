"""
Course service for managing course operations and academic structures.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.academic import Course, Department, AcademicSession, Semester, SemesterType
from ..schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseSearch,
    AcademicSessionCreate, AcademicSessionUpdate, AcademicSessionResponse,
    SemesterCreate, SemesterResponse, CourseDepartmentAssignment,
    CurriculumPlan, StudentCourseRegistration
)


class CourseService:
    """Service for managing course operations."""
    
    def __init__(self, db: Any):
        self.db = db
    
    async def create_course(self, course_data: CourseCreate, created_by: str) -> Course:
        """Create a new course."""
        # Check if course code already exists
        existing = await self.db.execute(
            select(Course).where(Course.code == course_data.code)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Course code {course_data.code} already exists")
        
        # Create course
        course = Course(
            code=course_data.code,
            title=course_data.title,
            description=course_data.description,
            credit_units=course_data.credit_units,
            level=course_data.level,
            semester_type=course_data.semester_type,
            is_active=True
        )
        
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        
        # Assign to departments if provided
        if course_data.department_ids:
            for dept_id in course_data.department_ids:
                assignment = CourseDepartmentAssignment(
                    course_id=course.id,
                    department_id=dept_id,
                    assigned_by=created_by
                )
                self.db.add(assignment)
            await self.db.commit()
        
        return course
    
    async def list_courses(self, search_params: CourseSearch) -> List[Course]:
        """List courses with filtering and pagination."""
        query = select(Course)
        
        # Apply filters
        if search_params.department_id:
            query = query.join(Course.departments).where(
                Department.id == search_params.department_id
            )
        if search_params.level:
            query = query.where(Course.level == search_params.level)
        if search_params.semester_type:
            query = query.where(Course.semester_type == search_params.semester_type)
        if search_params.is_active is not None:
            query = query.where(Course.is_active == search_params.is_active)
        
        # Apply search
        if search_params.search:
            search_term = f"%{search_params.search}%"
            query = query.where(
                or_(
                    Course.code.ilike(search_term),
                    Course.title.ilike(search_term)
                )
            )
        
        # Apply ordering and pagination
        query = query.order_by(Course.code)
        if search_params.offset:
            query = query.offset(search_params.offset)
        if search_params.limit:
            query = query.limit(search_params.limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID."""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
    
    async def update_course(self, course_id: str, course_data: CourseUpdate, updated_by: str) -> Optional[Course]:
        """Update course record."""
        course = await self.get_course(course_id)
        if not course:
            return None
        
        # Update fields
        update_data = course_data.dict(exclude_unset=True)
        department_ids = update_data.pop('department_ids', None)
        
        for field, value in update_data.items():
            if hasattr(course, field):
                setattr(course, field, value)
        
        # Handle course code change if provided
        if 'code' in update_data:
            existing = await self.db.execute(
                select(Course).where(
                    Course.code == update_data['code'],
                    Course.id != course_id
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Course code {update_data['code']} already exists")
        
        await self.db.commit()
        await self.db.refresh(course)
        
        # Update department assignments if provided
        if department_ids is not None:
            # Remove existing assignments
            await self.db.execute(
                text("DELETE FROM course_departments WHERE course_id = :course_id"),
                {"course_id": course_id}
            )
            
            # Add new assignments
            for dept_id in department_ids:
                assignment = CourseDepartmentAssignment(
                    course_id=course_id,
                    department_id=dept_id,
                    assigned_by=updated_by
                )
                self.db.add(assignment)
            
            await self.db.commit()
        
        return course
    
    async def delete_course(self, course_id: str, deleted_by: str) -> bool:
        """Delete course record (soft delete)."""
        course = await self.get_course(course_id)
        if not course:
            return False
        
        # Soft delete by deactivating
        course.is_active = False
        course.deleted_at = datetime.utcnow()
        course.deleted_by = deleted_by
        
        await self.db.commit()
        return True
    
    async def create_academic_session(self, session_data: AcademicSessionCreate, created_by: str) -> AcademicSession:
        """Create a new academic session."""
        # Check if session code already exists
        existing = await self.db.execute(
            select(AcademicSession).where(AcademicSession.session_code == session_data.session_code)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Session code {session_data.session_code} already exists")
        
        # If this is set as current, unset other current sessions
        if session_data.is_current:
            await self.db.execute(
                update(AcademicSession).where(AcademicSession.is_current == True).values(is_current=False)
            )
        
        # Create session
        session = AcademicSession(
            session_code=session_data.session_code,
            start_date=session_data.start_date,
            end_date=session_data.end_date,
            is_current=session_data.is_current or False
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def list_academic_sessions(self) -> List[AcademicSession]:
        """List all academic sessions."""
        result = await self.db.execute(
            select(AcademicSession).order_by(AcademicSession.start_date.desc())
        )
        return result.scalars().all()
    
    async def get_academic_session(self, session_id: str) -> Optional[AcademicSession]:
        """Get academic session by ID."""
        result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def update_academic_session(self, session_id: str, session_data: AcademicSessionUpdate, updated_by: str) -> Optional[AcademicSession]:
        """Update academic session."""
        session = await self.get_academic_session(session_id)
        if not session:
            return None
        
        # Update fields
        update_data = session_data.dict(exclude_unset=True)
        
        # Handle current session change
        if 'is_current' in update_data and update_data['is_current']:
            # Unset other current sessions
            await self.db.execute(
                update(AcademicSession).where(AcademicSession.id != session_id).values(is_current=False)
            )
        
        for field, value in update_data.items():
            if hasattr(session, field):
                setattr(session, field, value)
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def create_semester(self, semester_data: SemesterCreate, created_by: str) -> Semester:
        """Create a new semester."""
        # Check if semester already exists for this session
        existing = await self.db.execute(
            select(Semester).where(
                Semester.academic_session_id == semester_data.academic_session_id,
                Semester.semester_type == semester_data.semester_type
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Semester {semester_data.semester_type.value} already exists for this session")
        
        # Create semester
        semester = Semester(
            academic_session_id=semester_data.academic_session_id,
            semester_type=semester_data.semester_type,
            start_date=semester_data.start_date,
            end_date=semester_data.end_date,
            is_active=semester_data.is_active or True
        )
        
        self.db.add(semester)
        await self.db.commit()
        await self.db.refresh(semester)
        return semester
    
    async def list_semesters(self, academic_session_id: Optional[str] = None) -> List[Semester]:
        """List semesters."""
        query = select(Semester)
        
        if academic_session_id:
            query = query.where(Semester.academic_session_id == academic_session_id)
        
        query = query.order_by(Semester.start_date)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def assign_course_to_department(self, assignment: CourseDepartmentAssignment, assigned_by: str) -> bool:
        """Assign course to department."""
        # Check if assignment already exists
        existing = await self.db.execute(
            text("SELECT 1 FROM course_departments WHERE course_id = :course_id AND department_id = :department_id"),
            {"course_id": assignment.course_id, "department_id": assignment.department_id}
        )
        if existing.scalar_one_or_none():
            return False  # Already assigned
        
        # Create assignment
        await self.db.execute(
            text("INSERT INTO course_departments (course_id, department_id, assigned_by, assigned_at) VALUES (:course_id, :department_id, :assigned_by, NOW())"),
            {"course_id": assignment.course_id, "department_id": assignment.department_id, "assigned_by": assigned_by}
        )
        
        await self.db.commit()
        return True
    
    async def create_curriculum_plan(self, plan: CurriculumPlan, created_by: str) -> bool:
        """Create curriculum plan."""
        # In a real implementation, this would create a curriculum plan record
        # For now, return success as a placeholder
        return True
    
    async def register_student_for_course(self, registration: StudentCourseRegistration, registered_by: str) -> bool:
        """Register student for course."""
        # Check if student exists
        student_exists = await self.db.execute(
            select(Student).where(Student.id == registration.student_id)
        )
        if not student_exists.scalar_one_or_none():
            raise ValueError(f"Student {registration.student_id} not found")
        
        # Check if course exists
        course_exists = await self.db.execute(
            select(Course).where(Course.id == registration.course_id)
        )
        if not course_exists.scalar_one_or_none():
            raise ValueError(f"Course {registration.course_id} not found")
        
        # Check if already registered
        existing = await self.db.execute(
            select(StudentCourse).where(
                StudentCourse.student_id == registration.student_id,
                StudentCourse.course_id == registration.course_id,
                StudentCourse.academic_session_id == registration.academic_session_id,
                StudentCourse.semester == registration.semester
            )
        )
        if existing.scalar_one_or_none():
            return False  # Already registered
        
        # Create registration
        student_course = StudentCourse(
            student_id=registration.student_id,
            course_id=registration.course_id,
            academic_session_id=registration.academic_session_id,
            semester=registration.semester,
            registered_by=registered_by,
            registration_date=datetime.utcnow()
        )
        
        self.db.add(student_course)
        await self.db.commit()
        return True
