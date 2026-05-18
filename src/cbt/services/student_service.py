"""Student service for managing student records using Beanie."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from ..models.student import Student, StudentCourse, StudentStatus
from ..schemas.student import (
    StudentCreate, StudentUpdate, StudentSearch,
    BulkImportRequest, BulkImportResponse, StudentCourseRegistration,
    StudentStatusUpdate
)


class StudentService:
    """Service for managing student operations."""

    def __init__(self, db: Any):
        # db retained for compatibility with dependency injection.
        self.db = db

    async def create_student(self, student_data: StudentCreate, created_by: str) -> Student:
        """Create a new student record."""
        existing = await Student.find_one(Student.matric_number == student_data.matric_number)
        if existing:
            raise ValueError(f"Matric number {student_data.matric_number} already exists")

        existing_user = await Student.find_one(Student.user_id == student_data.user_id)
        if existing_user:
            raise ValueError(f"User {student_data.user_id} already has a student record")

        student = Student(
            user_id=student_data.user_id,
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            email=str(student_data.email),
            phone_number=student_data.phone_number,
            date_of_birth=student_data.date_of_birth,
            gender=student_data.gender,
            department_id=student_data.department_id,
            academic_session_id=student_data.academic_session_id,
            matric_number=student_data.matric_number,
            admission_year=student_data.admission_year,
            current_level=student_data.current_level,
            graduated=False,
            is_active=True,
        )
        await student.insert()
        return student
    
    async def list_students(self, search_params: StudentSearch) -> List[Student]:
        """List students with filtering and pagination."""
        query = Student.find(Student.is_active == True)

        if search_params.department_id:
            query = query.find(Student.department_id == search_params.department_id)
        if search_params.academic_session:
            query = query.find(Student.academic_session_id == search_params.academic_session)
        if search_params.level:
            query = query.find(Student.current_level == search_params.level)
        if search_params.status:
            if search_params.status == StudentStatus.GRADUATED:
                query = query.find(Student.graduated == True)
            elif search_params.status == StudentStatus.INACTIVE:
                query = query.find(Student.is_active == False)
            else:
                query = query.find(Student.graduated == False, Student.is_active == True)
        if search_params.query:
            query = query.find({"matric_number": {"$regex": search_params.query, "$options": "i"}})

        limit = search_params.limit or 50
        students = await query.sort("matric_number").limit(limit).to_list()
        return students
    
    async def search_students(self, query: str, limit: int = 50) -> List[Student]:
        """Search students by name or matric number."""
        return await Student.find(
            {"$or": [
                {"matric_number": {"$regex": query, "$options": "i"}},
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
            ]}
        ).limit(limit).to_list()
    
    async def get_student(self, student_id: str) -> Optional[Student]:
        """Get student by ID."""
        return await Student.find_one(Student.id == student_id)
    
    async def get_student_by_matric(self, matric_number: str) -> Optional[Student]:
        """Get student by matric number."""
        return await Student.find_one(Student.matric_number == matric_number)
    
    async def update_student(self, student_id: str, student_data: StudentUpdate, updated_by: str) -> Optional[Student]:
        """Update student record."""
        # Get student
        student = await self.get_student(student_id)
        if not student:
            return None
        
        update_data = student_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(student, field):
                setattr(student, field, value)

        await student.save()
        return student
    
    async def delete_student(self, student_id: str, deleted_by: str) -> bool:
        """Delete student record (soft delete)."""
        student = await self.get_student(student_id)
        if not student:
            return False
        
        student.is_active = False
        await student.save()
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
            errors=failed_imports,
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
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    email=row["email"],
                    phone_number=row.get('phone_number'),
                    admission_year=int(row['admission_year']),
                    current_level=int(row['current_level']),
                    department_id=row['department_id'],
                    academic_session_id=row["academic_session_id"]
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
        if status_update.status == StudentStatus.INACTIVE:
            student.is_active = False
        elif status_update.status == StudentStatus.GRADUATED:
            student.graduated = True
        else:
            student.is_active = True
        await student.save()
        return student
    
    async def activate_student(self, student_id: str, reason: str, updated_by: str) -> Optional[Student]:
        """Activate student account."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.is_active = True
        await student.save()
        return student
    
    async def deactivate_student(self, student_id: str, reason: str, updated_by: str) -> Optional[Student]:
        """Deactivate student account."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.is_active = False
        await student.save()
        return student
    
    async def graduate_student(self, student_id: str, graduation_year: int, updated_by: str) -> Optional[Student]:
        """Mark student as graduated."""
        student = await self.get_student(student_id)
        if not student:
            return None
        
        student.graduated = True
        student.graduation_year = graduation_year
        await student.save()
        return student
    
    async def get_student_courses(self, student_id: str, academic_session: str, semester: str) -> List[StudentCourse]:
        """Get student's course registrations."""
        query = StudentCourse.find(StudentCourse.student_id == student_id)
        if academic_session:
            query = query.find(StudentCourse.academic_session_id == academic_session)
        if semester:
            query = query.find(StudentCourse.semester_id == semester)
        return await query.to_list()
    
    async def register_for_course(self, registration: StudentCourseRegistration, registered_by: str) -> Dict[str, Any]:
        """Register student for course."""
        # Check if student exists
        student = await self.get_student(registration.student_id)
        if not student:
            raise ValueError(f"Student {registration.student_id} not found")
        
        # Check if already registered
        existing = await StudentCourse.find_one(
            StudentCourse.student_id == registration.student_id,
            StudentCourse.course_id == registration.course_id,
            StudentCourse.academic_session_id == registration.academic_session_id,
            StudentCourse.semester_id == registration.semester_id
        )
        if existing:
            raise ValueError("Student already registered for this course")
        
        # Create registration
        student_course = StudentCourse(
            student_id=registration.student_id,
            course_id=registration.course_id,
            academic_session_id=registration.academic_session_id,
            semester_id=registration.semester_id,
            registration_date=datetime.now(timezone.utc)
        )
        await student_course.insert()
        
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
        student_course = await StudentCourse.find_one(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id,
            StudentCourse.academic_session_id == academic_session,
            StudentCourse.semester_id == semester
        )
        
        if not student_course:
            raise ValueError("Course registration not found")
        
        # Update registration to withdrawn
        student_course.status = "WITHDRAWN"
        await student_course.save()
        
        return {
            "registration_id": student_course.id,
            "student_id": student_id,
            "course_id": course_id,
            "status": "withdrawn",
            "message": "Course withdrawal successful"
        }
