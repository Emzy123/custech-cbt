"""
Student service for managing student records and operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..models.student import Student, StudentCourse, StudentStatus
from ..models.user import User
from ..models.academic import AcademicSession, Semester, Department
from ..schemas.student import (
    StudentCreate, StudentUpdate, StudentSearch,
    BulkImportRequest, BulkImportResponse, StudentCourseRegistration,
    StudentStatusUpdate
)


class StudentService:
    """Service for managing student operations."""
    
    def __init__(self, db: Any):
        self.db = db
    
    async def create_student(self, student_data: StudentCreate, created_by: str) -> Student:
        """Create a new student record."""
        # Check if matric number already exists
        existing = await self.db.execute(
            select(Student).where(Student.matric_number == student_data.matric_number)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Matric number {student_data.matric_number} already exists")
        
        # Check if user already has a student record
        existing_user = await self.db.execute(
            select(Student).where(Student.user_id == student_data.user_id)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError(f"User {student_data.user_id} already has a student record")
        
        # Create student record
        student = Student(
            user_id=student_data.user_id,
            department_id=student_data.department_id,
            academic_session_id=student_data.academic_session_id,
            matric_number=student_data.matric_number,
            admission_year=student_data.admission_year,
            current_level=student_data.current_level,
            is_active=True,
            graduated=False
        )
        
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def list_students(self, search_params: StudentSearch) -> List[Student]:
        """List students with filtering and pagination."""
        query = select(Student)
        
        # Apply filters
        if search_params.department_id:
            query = query.where(Student.department_id == search_params.department_id)
        if search_params.academic_session_id:
            query = query.where(Student.academic_session_id == search_params.academic_session_id)
        if search_params.current_level:
            query = query.where(Student.current_level == search_params.current_level)
        if search_params.is_active is not None:
            query = query.where(Student.is_active == search_params.is_active)
        if search_params.graduated is not None:
            query = query.where(Student.graduated == search_params.graduated)
        
        # Apply search
        if search_params.search:
            search_term = f"%{search_params.search}%"
            query = query.where(
                Student.matric_number.ilike(search_term)
            )
        
        # Apply ordering and pagination
        query = query.order_by(Student.matric_number)
        if search_params.offset:
            query = query.offset(search_params.offset)
        if search_params.limit:
            query = query.limit(search_params.limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_students(self, query: str, limit: int = 50) -> List[Student]:
        """Search students by name or matric number."""
        search_term = f"%{query}%"
        db_query = select(Student).where(
            Student.matric_number.ilike(search_term)
        ).limit(limit)
        
        result = await self.db.execute(db_query)
        return result.scalars().all()
    
    async def get_student(self, student_id: str) -> Optional[Student]:
        """Get student by ID."""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_by_matric(self, matric_number: str) -> Optional[Student]:
        """Get student by matric number."""
        result = await self.db.execute(
            select(Student).where(Student.matric_number == matric_number)
        )
        return result.scalar_one_or_none()
    
    async def update_student(self, student_id: str, student_data: StudentUpdate, updated_by: str) -> Optional[Student]:
        """Update student record."""
        # Get student
        student = await self.get_student(student_id)
        if not student:
            return None
        
        # Update fields
        update_data = student_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(student, field):
                setattr(student, field, value)
        
        # Handle matric number change if provided
        if 'matric_number' in update_data:
            existing = await self.db.execute(
                select(Student).where(
                    Student.matric_number == update_data['matric_number'],
                    Student.id != student_id
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Matric number {update_data['matric_number']} already exists")
        
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def delete_student(self, student_id: str, deleted_by: str) -> bool:
        """Delete student record (soft delete)."""
        student = await self.get_student(student_id)
        if not student:
            return False
        
        # Soft delete by deactivating
        student.is_active = False
        student.deleted_at = datetime.utcnow()
        student.deleted_by = deleted_by
        
        await self.db.commit()
        return True
    
    async def bulk_import_students(self, import_request: BulkImportRequest, created_by: str) -> BulkImportResponse:
        """Bulk import students from data."""
        import_id = str(uuid.uuid4())
        successful_imports = []
        failed_imports = []
        
        for student_data in import_request.students:
            try:
                # Create student
                student = await self.create_student(student_data, created_by)
                successful_imports.append({
                    "matric_number": student.matric_number,
                    "student_id": student.id,
                    "status": "success"
                })
            except Exception as e:
                failed_imports.append({
                    "matric_number": student_data.matric_number,
                    "error": str(e),
                    "status": "failed"
                })
        
        return BulkImportResponse(
            import_id=import_id,
            total_records=len(import_request.students),
            successful_imports=len(successful_imports),
            failed_imports=len(failed_imports),
            successful_records=successful_imports,
            failed_records=failed_imports,
            status="completed"
        )
    
    async def import_from_csv(self, file, validate_only: bool, continue_on_error: bool, created_by: str) -> Dict[str, Any]:
        """Import students from CSV file."""
        import csv
        import io
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        students_data = []
        validation_errors = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Validate and map CSV data to StudentCreate
                student_data = StudentCreate(
                    user_id=row.get('user_id', ''),
                    matric_number=row['matric_number'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row['email'],
                    phone_number=row.get('phone_number'),
                    admission_year=int(row['admission_year']),
                    current_level=int(row['current_level']),
                    department_id=row['department_id'],
                    academic_session_id=row['academic_session_id']
                )
                students_data.append(student_data)
            except Exception as e:
                validation_errors.append({
                    "row": row_num,
                    "error": str(e),
                    "data": row
                })
                if not continue_on_error:
                    break
        
        if validate_only:
            return {
                "validation_errors": validation_errors,
                "total_rows": row_num,
                "valid_records": len(students_data)
            }
        
        # Perform actual import
        import_request = BulkImportRequest(students=students_data)
        result = await self.bulk_import_students(import_request, created_by)
        
        return {
            "import_result": result.dict(),
            "validation_errors": validation_errors
        }
    
    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get bulk import status."""
        # In a real implementation, this would check a database or cache
        # For now, return a mock response
        return {
            "import_id": import_id,
            "status": "completed",
            "progress": 100,
            "message": "Import completed successfully"
        }
    
    async def update_student_status(self, student_id: str, status_update: StudentStatusUpdate, updated_by: str) -> Optional[Student]:
        """Update student status."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        # Update status based on the status_update data
        if hasattr(status_update, 'status') and status_update.status:
            # Convert string to enum if needed
            if isinstance(status_update.status, str):
                student.status = StudentStatus(status_update.status)
            else:
                student.status = status_update.status
        
        if hasattr(status_update, 'is_active') and status_update.is_active is not None:
            student.is_active = status_update.is_active
        
        if hasattr(status_update, 'graduated') and status_update.graduated is not None:
            student.graduated = status_update.graduated
            if status_update.graduated and hasattr(status_update, 'graduation_year'):
                student.graduation_year = status_update.graduation_year
        
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def activate_student(self, student_id: str, reason: str, updated_by: str) -> Optional[Student]:
        """Activate student account."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.is_active = True
        student.status = StudentStatus.ACTIVE
        
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def deactivate_student(self, student_id: str, reason: str, updated_by: str) -> Optional[Student]:
        """Deactivate student account."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.is_active = False
        student.status = StudentStatus.INACTIVE
        
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def graduate_student(self, student_id: str, graduation_year: int, updated_by: str) -> Optional[Student]:
        """Mark student as graduated."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.graduated = True
        student.graduation_year = graduation_year
        student.status = StudentStatus.GRADUATED
        
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def get_student_courses(self, student_id: str, academic_session: str, semester: str) -> List[StudentCourse]:
        """Get student's course registrations."""
        result = await self.db.execute(
            select(StudentCourse).where(
                StudentCourse.student_id == student_id,
                StudentCourse.academic_session_id == academic_session,
                StudentCourse.semester == semester
            )
        )
        return result.scalars().all()
    
    async def register_for_course(self, registration: StudentCourseRegistration, registered_by: str) -> Dict[str, Any]:
        """Register student for course."""
        # Check if student exists
        student = await self.get_student(registration.student_id)
        if not student:
            raise ValueError(f"Student {registration.student_id} not found")
        
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
            raise ValueError("Student already registered for this course")
        
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
        await self.db.refresh(student_course)
        
        return {
            "registration_id": student_course.id,
            "student_id": registration.student_id,
            "course_id": registration.course_id,
            "status": "registered",
            "message": "Course registration successful"
        }
    
    async def withdraw_from_course(self, student_id: str, course_id: str, academic_session: str, semester: str, withdrawn_by: str) -> Dict[str, Any]:
        """Withdraw student from course."""
        # Find existing registration
        result = await self.db.execute(
            select(StudentCourse).where(
                StudentCourse.student_id == student_id,
                StudentCourse.course_id == course_id,
                StudentCourse.academic_session_id == academic_session,
                StudentCourse.semester == semester
            )
        )
        student_course = result.scalar_one_or_none()
        
        if not student_course:
            raise ValueError("Course registration not found")
        
        # Update registration to withdrawn
        student_course.is_active = False
        student_course.withdrawn_by = withdrawn_by
        student_course.withdrawal_date = datetime.utcnow()
        
        await self.db.commit()
        
        return {
            "registration_id": student_course.id,
            "student_id": student_id,
            "course_id": course_id,
            "status": "withdrawn",
            "message": "Course withdrawal successful"
        }
