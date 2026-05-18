"""Course service for managing course operations with Beanie."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..models.academic import (
    Course,
    Department,
    AcademicSession,
    Semester,
    SemesterType,
    CourseDepartment,
)
from ..models.student import StudentCourse, Student
from ..schemas.course import (
    CourseCreate, CourseUpdate, CourseSearch,
    AcademicSessionCreate, AcademicSessionUpdate,
    SemesterCreate, CourseDepartmentAssignment,
    CurriculumPlan, StudentCourseRegistration
)


class CourseService:
    """Service for managing course operations."""

    def __init__(self, db: Any):
        self.db = db
    
    async def create_course(self, course_data: CourseCreate, created_by: str) -> Course:
        """Create a new course."""
        # Check if course code already exists
        existing = await Course.find_one(Course.code == course_data.code)
        if existing:
            raise ValueError(f"Course code {course_data.code} already exists")
        
        # Create course
        course = Course(
            code=course_data.code,
            title=course_data.title,
            description=course_data.description,
            credit_units=course_data.credit_units,
            level=course_data.level,
            semester_type=course_data.semester_type,
            created_by=created_by,
            is_active=True,
        )
        await course.insert()
        
        # Assign to departments if provided
        if course_data.department_ids:
            for dept_id in course_data.department_ids:
                assignment = CourseDepartment(
                    course_id=course.id,
                    department_id=dept_id,
                    is_mandatory=False,
                )
                await assignment.insert()
        
        return course
    
    async def list_courses(self, search_params: CourseSearch) -> List[Course]:
        """List courses with filtering and pagination."""
        query = Course.find(Course.is_active == True)
        if search_params.level:
            query = query.find(Course.level == search_params.level)
        if search_params.semester_type:
            query = query.find(Course.semester_type == search_params.semester_type)
        if search_params.is_active is not None:
            query = query.find(Course.is_active == search_params.is_active)
        if search_params.query:
            query = query.find(
                {"$or": [
                    {"code": {"$regex": search_params.query, "$options": "i"}},
                    {"title": {"$regex": search_params.query, "$options": "i"}},
                ]}
            )

        courses = await query.sort("code").limit(search_params.limit or 50).to_list()
        if search_params.department_id:
            links = await CourseDepartment.find(
                CourseDepartment.department_id == search_params.department_id
            ).to_list()
            allowed = {l.course_id for l in links}
            courses = [c for c in courses if c.id in allowed]
        return courses
    
    async def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID."""
        return await Course.find_one(Course.id == course_id)
    
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
            existing = await Course.find_one(
                Course.code == update_data['code'], Course.id != course_id
            )
            if existing:
                raise ValueError(f"Course code {update_data['code']} already exists")
        await course.save()
        
        # Update department assignments if provided
        if department_ids is not None:
            existing_links = await CourseDepartment.find(
                CourseDepartment.course_id == course_id
            ).to_list()
            for link in existing_links:
                await link.delete()
            for dept_id in department_ids:
                assignment = CourseDepartment(
                    course_id=course_id,
                    department_id=dept_id,
                    is_mandatory=False,
                )
                await assignment.insert()
        
        return course
    
    async def delete_course(self, course_id: str, deleted_by: str) -> bool:
        """Delete course record (soft delete)."""
        course = await self.get_course(course_id)
        if not course:
            return False
        
        # Soft delete by deactivating
        course.is_active = False
        await course.save()
        return True
    
    async def create_academic_session(self, session_data: AcademicSessionCreate, created_by: str) -> AcademicSession:
        """Create a new academic session."""
        # Check if session code already exists
        existing = await AcademicSession.find_one(AcademicSession.session_code == session_data.session_code)
        if existing:
            raise ValueError(f"Session code {session_data.session_code} already exists")
        
        # Create session
        session = AcademicSession(
            session_code=session_data.session_code,
            start_date=session_data.start_date,
            end_date=session_data.end_date,
            is_current=False,
        )
        await session.insert()
        return session
    
    async def list_academic_sessions(self, is_current: Optional[bool] = None) -> List[AcademicSession]:
        """List all academic sessions."""
        query = AcademicSession.find()
        if is_current is not None:
            query = query.find(AcademicSession.is_current == is_current)
        return await query.sort("-start_date").to_list()
    
    async def get_academic_session(self, session_id: str) -> Optional[AcademicSession]:
        """Get academic session by ID."""
        return await AcademicSession.find_one(AcademicSession.id == session_id)
    
    async def update_academic_session(self, session_id: str, session_data: AcademicSessionUpdate, updated_by: str) -> Optional[AcademicSession]:
        """Update academic session."""
        session = await self.get_academic_session(session_id)
        if not session:
            return None
        
        # Update fields
        update_data = session_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(session, field):
                setattr(session, field, value)
        await session.save()
        return session

    async def set_current_session(self, session_id: str, updated_by: str) -> Optional[AcademicSession]:
        session = await self.get_academic_session(session_id)
        if not session:
            return None
        sessions = await AcademicSession.find().to_list()
        for s in sessions:
            s.is_current = (s.id == session_id)
            await s.save()
        return session
    
    async def create_semester(self, session_id: str, semester_data: SemesterCreate, created_by: str) -> Semester:
        """Create a new semester."""
        # Check if semester already exists for this session
        existing = await Semester.find_one(
            Semester.academic_session_id == session_id,
            Semester.semester_type == semester_data.semester_type
        )
        if existing:
            raise ValueError(f"Semester {semester_data.semester_type.value} already exists for this session")
        
        # Create semester
        semester = Semester(
            academic_session_id=session_id,
            semester_type=semester_data.semester_type,
            start_date=semester_data.start_date,
            end_date=semester_data.end_date,
            is_current=False,
        )
        await semester.insert()
        return semester
    
    async def list_semesters(self, academic_session_id: Optional[str] = None, is_current: Optional[bool] = None) -> List[Semester]:
        """List semesters."""
        query = Semester.find()
        if academic_session_id:
            query = query.find(Semester.academic_session_id == academic_session_id)
        if is_current is not None:
            query = query.find(Semester.is_current == is_current)
        return await query.sort("start_date").to_list()
    
    async def assign_course_to_department(self, course_id: str, department_id: str, is_mandatory: bool, assigned_by: str) -> bool:
        """Assign course to department."""
        existing = await CourseDepartment.find_one(
            CourseDepartment.course_id == course_id,
            CourseDepartment.department_id == department_id,
        )
        if existing:
            return False
        link = CourseDepartment(course_id=course_id, department_id=department_id, is_mandatory=is_mandatory)
        await link.insert()
        return True
    
    async def create_curriculum_plan(self, plan: CurriculumPlan, created_by: str) -> bool:
        """Create curriculum plan."""
        # In a real implementation, this would create a curriculum plan record
        # For now, return success as a placeholder
        return True

    async def get_curriculum_plan(self, session_id: str, department_id: Optional[str], level: Optional[int]) -> Dict[str, Any]:
        courses = await self.list_courses(CourseSearch(department_id=department_id, level=level, limit=200))
        return {"session_id": session_id, "courses": [c.id for c in courses]}

    async def activate_curriculum_plan(self, session_id: str, activated_by: str) -> Dict[str, Any]:
        return {"success": True, "session_id": session_id, "message": "Curriculum activated"}

    async def get_course_departments(self, course_id: str) -> List[Dict[str, Any]]:
        links = await CourseDepartment.find(CourseDepartment.course_id == course_id).to_list()
        return [{"course_id": l.course_id, "department_id": l.department_id, "is_mandatory": l.is_mandatory} for l in links]

    async def get_department_courses(self, department_id: str, level: Optional[int], semester_type: Optional[SemesterType], is_mandatory: Optional[bool]):
        links_query = CourseDepartment.find(CourseDepartment.department_id == department_id)
        if is_mandatory is not None:
            links_query = links_query.find(CourseDepartment.is_mandatory == is_mandatory)
        links = await links_query.to_list()
        course_ids = [l.course_id for l in links]
        if not course_ids:
            return []
        query = Course.find({"_id": {"$in": course_ids}})
        if level:
            query = query.find(Course.level == level)
        if semester_type:
            query = query.find(Course.semester_type == semester_type)
        return await query.to_list()

    async def search_courses(self, query: str, limit: int = 20) -> List[Course]:
        return await Course.find(
            {"$or": [
                {"code": {"$regex": query, "$options": "i"}},
                {"title": {"$regex": query, "$options": "i"}},
            ]}
        ).limit(limit).to_list()

    async def get_course_by_code(self, course_code: str) -> Optional[Course]:
        return await Course.find_one(Course.code == course_code)
    
    async def register_student_for_course(self, registration: StudentCourseRegistration, registered_by: str) -> bool:
        """Register student for course."""
        # Check if student exists
        student_exists = await Student.find_one(Student.id == registration.student_id)
        if not student_exists:
            raise ValueError(f"Student {registration.student_id} not found")
        
        # Check if course exists
        course_exists = await Course.find_one(Course.id == registration.course_id)
        if not course_exists:
            raise ValueError(f"Course {registration.course_id} not found")
        
        # Check if already registered
        existing = await StudentCourse.find_one(
            StudentCourse.student_id == registration.student_id,
            StudentCourse.course_id == registration.course_id,
            StudentCourse.academic_session_id == registration.academic_session_id,
            StudentCourse.semester_id == registration.semester_id
        )
        if existing:
            return False  # Already registered
        
        # Create registration
        student_course = StudentCourse(
            student_id=registration.student_id,
            course_id=registration.course_id,
            academic_session_id=registration.academic_session_id,
            semester_id=registration.semester_id,
            registration_date=registration.registration_date
        )
        await student_course.insert()
        return True
