# Student Lifecycle API

## Overview

This document defines the comprehensive Student Lifecycle API for the CBT system, providing endpoints for student record management, bulk operations, and lifecycle events while maintaining academic integrity and data consistency.

## API Architecture

### RESTful Design Principles
```
Base URL: https://api.cbt.custech.edu.ng/api/v1
Authentication: JWT Bearer Token
Content-Type: application/json
Rate Limiting: 100 requests per minute per user
Pagination: Cursor-based for large datasets
```

### Student Lifecycle States
```
1. Prospective → Admission Processing
2. Active → Enrolled and Taking Courses
3. Inactive → Suspended or Deferred
4. Graduated → Completed Program
5. Alumni → Post-Graduation Status
6. Archived → Historical Records
```

### Data Models
```python
# models/student.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class StudentStatus(str, Enum):
    PROSPECTIVE = "PROSPECTIVE"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    GRADUATED = "GRADUATED"
    ALUMNI = "ALUMNI"
    ARCHIVED = "ARCHIVED"

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class StudentBase(BaseModel):
    matric_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: date
    gender: Gender
    admission_year: int
    current_level: int
    department_id: str
    academic_session_id: str

class StudentCreate(StudentBase):
    user_id: str
    
    @validator('matric_number')
    def validate_matric_number(cls, v):
        import re
        if not re.match(r'^20\d{2}/\d{6}$', v):
            raise ValueError('Matric number must follow format: 20XX/XXXXXX')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not re.match(r'^\+234\d{10}$', v):
            raise ValueError('Phone number must follow format: +234XXXXXXXXXX')
        return v

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    current_level: Optional[int] = None
    department_id: Optional[str] = None

class StudentResponse(StudentBase):
    id: str
    user_id: str
    is_active: bool
    graduated: bool
    graduation_year: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StudentSearch(BaseModel):
    query: Optional[str] = None
    department_id: Optional[str] = None
    level: Optional[int] = None
    status: Optional[StudentStatus] = None
    academic_session: Optional[str] = None
    limit: int = 50
    cursor: Optional[str] = None

class BulkImportRequest(BaseModel):
    students: List[StudentCreate]
    validate_only: bool = False
    continue_on_error: bool = False

class BulkImportResponse(BaseModel):
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]]
    import_id: str

class StudentCourseRegistration(BaseModel):
    student_id: str
    course_id: str
    academic_session_id: str
    semester_id: str
    registration_date: date

class StudentStatusUpdate(BaseModel):
    status: StudentStatus
    reason: Optional[str] = None
    effective_date: date
```

---

## API Endpoints

### 1. Student CRUD Operations

#### Create Student
```python
# api/students.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.student import StudentCreate, StudentResponse, StudentSearch
from ..services.student_service import StudentService
from ..middleware.authorization_middleware import require_permission
from ..authorization import Permission

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.STUDENT_CREATE)
async def create_student(
    student_data: StudentCreate,
    student_service: StudentService = Depends()
):
    """Create a new student record"""
    try:
        student = await student_service.create_student(student_data)
        return student
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student record"
        )

@router.get("/{student_id}", response_model=StudentResponse)
@require_permission(Permission.STUDENT_READ)
async def get_student(
    student_id: str,
    student_service: StudentService = Depends()
):
    """Get student by ID"""
    student = await student_service.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student

@router.put("/{student_id}", response_model=StudentResponse)
@require_permission(Permission.STUDENT_UPDATE)
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    student_service: StudentService = Depends()
):
    """Update student record"""
    try:
        student = await student_service.update_student(student_id, student_data)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission(Permission.STUDENT_DELETE)
async def delete_student(
    student_id: str,
    student_service: StudentService = Depends()
):
    """Delete student record (soft delete)"""
    success = await student_service.delete_student(student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
```

#### Student Search and Listing
```python
@router.get("/", response_model=List[StudentResponse])
@require_permission(Permission.STUDENT_READ)
async def list_students(
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    academic_session: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    cursor: Optional[str] = Query(None),
    student_service: StudentService = Depends()
):
    """List students with filtering and pagination"""
    search_params = StudentSearch(
        department_id=department_id,
        level=level,
        status=status,
        academic_session=academic_session,
        limit=limit,
        cursor=cursor
    )
    
    students = await student_service.list_students(search_params)
    return students

@router.get("/search", response_model=List[StudentResponse])
@require_permission(Permission.STUDENT_READ)
async def search_students(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    student_service: StudentService = Depends()
):
    """Search students by name or matric number"""
    students = await student_service.search_students(query, limit)
    return students

@router.get("/matric/{matric_number}", response_model=StudentResponse)
@require_permission(Permission.STUDENT_READ)
async def get_student_by_matric(
    matric_number: str,
    student_service: StudentService = Depends()
):
    """Get student by matric number"""
    student = await student_service.get_student_by_matric(matric_number)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student
```

### 2. Bulk Operations

#### Bulk Import
```python
@router.post("/import", response_model=BulkImportResponse)
@require_permission(Permission.STUDENT_IMPORT)
async def bulk_import_students(
    import_request: BulkImportRequest,
    student_service: StudentService = Depends()
):
    """Bulk import students from CSV or JSON data"""
    try:
        result = await student_service.bulk_import_students(import_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )

@router.post("/import/csv")
@require_permission(Permission.STUDENT_IMPORT)
async def import_students_from_csv(
    file: UploadFile = File(...),
    validate_only: bool = Query(False),
    continue_on_error: bool = Query(False),
    student_service: StudentService = Depends()
):
    """Import students from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        result = await student_service.import_from_csv(
            file, validate_only, continue_on_error
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV import failed: {str(e)}"
        )

@router.get("/import/{import_id}/status")
@require_permission(Permission.STUDENT_READ)
async def get_import_status(
    import_id: str,
    student_service: StudentService = Depends()
):
    """Get bulk import status"""
    status = await student_service.get_import_status(import_id)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found"
        )
    return status
```

#### Bulk Operations
```python
@router.put("/bulk/update")
@require_permission(Permission.STUDENT_UPDATE)
async def bulk_update_students(
    student_ids: List[str],
    update_data: StudentUpdate,
    student_service: StudentService = Depends()
):
    """Bulk update multiple students"""
    try:
        result = await student_service.bulk_update_students(student_ids, update_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )

@router.put("/bulk/status")
@require_permission(Permission.STUDENT_UPDATE)
async def bulk_update_student_status(
    student_ids: List[str],
    status_update: StudentStatusUpdate,
    student_service: StudentService = Depends()
):
    """Bulk update student status"""
    try:
        result = await student_service.bulk_update_status(student_ids, status_update)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk status update failed: {str(e)}"
        )

@router.delete("/bulk")
@require_permission(Permission.STUDENT_DELETE)
async def bulk_delete_students(
    student_ids: List[str],
    student_service: StudentService = Depends()
):
    """Bulk delete students (soft delete)"""
    try:
        result = await student_service.bulk_delete_students(student_ids)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk delete failed: {str(e)}"
        )
```

### 3. Student Lifecycle Management

#### Status Management
```python
@router.put("/{student_id}/status")
@require_permission(Permission.STUDENT_UPDATE)
async def update_student_status(
    student_id: str,
    status_update: StudentStatusUpdate,
    student_service: StudentService = Depends()
):
    """Update student status"""
    try:
        student = await student_service.update_student_status(
            student_id, status_update
        )
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{student_id}/activate")
@require_permission(Permission.STUDENT_UPDATE)
async def activate_student(
    student_id: str,
    reason: Optional[str] = None,
    student_service: StudentService = Depends()
):
    """Activate student account"""
    try:
        student = await student_service.activate_student(student_id, reason)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student activation failed: {str(e)}"
        )

@router.post("/{student_id}/deactivate")
@require_permission(Permission.STUDENT_UPDATE)
async def deactivate_student(
    student_id: str,
    reason: str,
    student_service: StudentService = Depends()
):
    """Deactivate student account"""
    try:
        student = await student_service.deactivate_student(student_id, reason)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student deactivation failed: {str(e)}"
        )

@router.post("/{student_id}/graduate")
@require_permission(Permission.STUDENT_UPDATE)
async def graduate_student(
    student_id: str,
    graduation_year: int,
    student_service: StudentService = Depends()
):
    """Mark student as graduated"""
    try:
        student = await student_service.graduate_student(student_id, graduation_year)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student graduation failed: {str(e)}"
        )
```

### 4. Course Registration

#### Course Management
```python
@router.get("/{student_id}/courses")
@require_permission(Permission.STUDENT_READ)
async def get_student_courses(
    student_id: str,
    academic_session: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    student_service: StudentService = Depends()
):
    """Get student's course registrations"""
    courses = await student_service.get_student_courses(
        student_id, academic_session, semester
    )
    return courses

@router.post("/{student_id}/courses")
@require_permission(Permission.STUDENT_UPDATE)
async def register_student_for_course(
    student_id: str,
    registration: StudentCourseRegistration,
    student_service: StudentService = Depends()
):
    """Register student for course"""
    try:
        result = await student_service.register_for_course(registration)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{student_id}/courses/{course_id}")
@require_permission(Permission.STUDENT_UPDATE)
async def withdraw_student_from_course(
    student_id: str,
    course_id: str,
    academic_session: str,
    semester: str,
    student_service: StudentService = Depends()
):
    """Withdraw student from course"""
    try:
        result = await student_service.withdraw_from_course(
            student_id, course_id, academic_session, semester
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
```

---

## Service Implementation

### Student Service
```python
# services/student_service.py
import uuid
import csv
import io
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from ..models.student import StudentCreate, StudentUpdate, StudentResponse, StudentSearch
from ..models.database import Student, User, Department, AcademicSession
from ..services.validation_service import ValidationService
from ..services.audit_service import AuditService

class StudentService:
    def __init__(self, db: AsyncSession, validation_service: ValidationService,
                 audit_service: AuditService):
        self.db = db
        self.validation_service = validation_service
        self.audit_service = audit_service
        self.bulk_import_jobs = {}
    
    async def create_student(self, student_data: StudentCreate) -> StudentResponse:
        """Create a new student record"""
        # Validate data
        await self._validate_student_data(student_data)
        
        # Check if user exists
        user_result = await self.db.execute(
            select(User).where(User.id == student_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        
        # Check for duplicate matric number
        existing = await self.db.execute(
            select(Student).where(Student.matric_number == student_data.matric_number)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Matric number already exists")
        
        # Create student record
        student = Student(
            id=str(uuid.uuid4()),
            user_id=student_data.user_id,
            matric_number=student_data.matric_number,
            admission_year=student_data.admission_year,
            current_level=student_data.current_level,
            department_id=student_data.department_id,
            academic_session_id=student_data.academic_session_id,
            is_active=True,
            graduated=False
        )
        
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        
        # Log audit
        await self.audit_service.log_action(
            action="CREATE_STUDENT",
            resource_type="student",
            resource_id=student.id,
            details=f"Created student {student_data.matric_number}"
        )
        
        return StudentResponse.from_orm(student)
    
    async def get_student(self, student_id: str) -> Optional[StudentResponse]:
        """Get student by ID"""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        return StudentResponse.from_orm(student) if student else None
    
    async def get_student_by_matric(self, matric_number: str) -> Optional[StudentResponse]:
        """Get student by matric number"""
        result = await self.db.execute(
            select(Student).where(Student.matric_number == matric_number)
        )
        student = result.scalar_one_or_none()
        return StudentResponse.from_orm(student) if student else None
    
    async def update_student(self, student_id: str, update_data: StudentUpdate) -> Optional[StudentResponse]:
        """Update student record"""
        # Get existing student
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(student, field):
                setattr(student, field, value)
        
        student.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(student)
        
        # Log audit
        await self.audit_service.log_action(
            action="UPDATE_STUDENT",
            resource_type="student",
            resource_id=student.id,
            details=f"Updated student {student.matric_number}"
        )
        
        return StudentResponse.from_orm(student)
    
    async def delete_student(self, student_id: str) -> bool:
        """Soft delete student record"""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            return False
        
        # Soft delete
        student.is_active = False
        student.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Log audit
        await self.audit_service.log_action(
            action="DELETE_STUDENT",
            resource_type="student",
            resource_id=student.id,
            details=f"Deleted student {student.matric_number}"
        )
        
        return True
    
    async def list_students(self, search_params: StudentSearch) -> List[StudentResponse]:
        """List students with filtering and pagination"""
        query = select(Student)
        
        # Apply filters
        if search_params.department_id:
            query = query.where(Student.department_id == search_params.department_id)
        
        if search_params.level:
            query = query.where(Student.current_level == search_params.level)
        
        if search_params.status:
            if search_params.status == "ACTIVE":
                query = query.where(Student.is_active == True, Student.graduated == False)
            elif search_params.status == "GRADUATED":
                query = query.where(Student.graduated == True)
            elif search_params.status == "INACTIVE":
                query = query.where(Student.is_active == False)
        
        if search_params.academic_session:
            query = query.where(Student.academic_session_id == search_params.academic_session)
        
        # Apply pagination
        query = query.limit(search_params.limit)
        
        if search_params.cursor:
            query = query.where(Student.id > search_params.cursor)
        
        # Execute query
        result = await self.db.execute(query)
        students = result.scalars().all()
        
        return [StudentResponse.from_orm(student) for student in students]
    
    async def search_students(self, query: str, limit: int = 20) -> List[StudentResponse]:
        """Search students by name or matric number"""
        # Search by matric number (exact match)
        matric_query = select(Student).where(
            Student.matric_number.ilike(f"%{query}%")
        )
        
        # Search by name (fuzzy match)
        name_query = select(Student).join(User).where(
            or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%")
            )
        )
        
        # Combine queries
        combined_query = matric_query.union(name_query).limit(limit)
        
        result = await self.db.execute(combined_query)
        students = result.scalars().all()
        
        return [StudentResponse.from_orm(student) for student in students]
    
    async def bulk_import_students(self, import_request: BulkImportRequest) -> BulkImportResponse:
        """Bulk import students"""
        import_id = str(uuid.uuid4())
        successful_imports = 0
        failed_imports = 0
        errors = []
        
        for i, student_data in enumerate(import_request.students):
            try:
                if import_request.validate_only:
                    # Only validate, don't create
                    await self._validate_student_data(student_data)
                    successful_imports += 1
                else:
                    # Create student
                    await self.create_student(student_data)
                    successful_imports += 1
                    
            except Exception as e:
                failed_imports += 1
                errors.append({
                    "row": i + 1,
                    "matric_number": student_data.matric_number,
                    "error": str(e)
                })
                
                if not import_request.continue_on_error:
                    break
        
        return BulkImportResponse(
            total_records=len(import_request.students),
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            errors=errors,
            import_id=import_id
        )
    
    async def import_from_csv(self, file, validate_only: bool = False,
                            continue_on_error: bool = False) -> BulkImportResponse:
        """Import students from CSV file"""
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Convert to StudentCreate objects
        students = []
        for row in csv_reader:
            try:
                student_data = StudentCreate(
                    user_id=row.get('user_id', ''),
                    matric_number=row['matric_number'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row['email'],
                    phone_number=row.get('phone_number'),
                    date_of_birth=datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date(),
                    gender=row['gender'],
                    admission_year=int(row['admission_year']),
                    current_level=int(row['current_level']),
                    department_id=row['department_id'],
                    academic_session_id=row['academic_session_id']
                )
                students.append(student_data)
            except Exception as e:
                if not continue_on_error:
                    raise ValueError(f"CSV parsing error: {str(e)}")
        
        # Bulk import
        import_request = BulkImportRequest(
            students=students,
            validate_only=validate_only,
            continue_on_error=continue_on_error
        )
        
        return await self.bulk_import_students(import_request)
    
    async def update_student_status(self, student_id: str, 
                                  status_update: StudentStatusUpdate) -> Optional[StudentResponse]:
        """Update student status"""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            return None
        
        # Update status based on status_update.status
        if status_update.status == StudentStatus.ACTIVE:
            student.is_active = True
        elif status_update.status == StudentStatus.INACTIVE:
            student.is_active = False
        elif status_update.status == StudentStatus.GRADUATED:
            student.graduated = True
            student.graduation_year = status_update.effective_date.year
        elif status_update.status == StudentStatus.ARCHIVED:
            student.is_active = False
            # Move to archive table
        
        student.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(student)
        
        # Log audit
        await self.audit_service.log_action(
            action="UPDATE_STUDENT_STATUS",
            resource_type="student",
            resource_id=student.id,
            details=f"Updated status to {status_update.status.value}"
        )
        
        return StudentResponse.from_orm(student)
    
    async def _validate_student_data(self, student_data: StudentCreate):
        """Validate student data"""
        # Validate matric number format
        import re
        if not re.match(r'^20\d{2}/\d{6}$', student_data.matric_number):
            raise ValueError("Invalid matric number format")
        
        # Validate department exists
        dept_result = await self.db.execute(
            select(Department).where(Department.id == student_data.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise ValueError("Department not found")
        
        # Validate academic session exists
        session_result = await self.db.execute(
            select(AcademicSession).where(AcademicSession.id == student_data.academic_session_id)
        )
        if not session_result.scalar_one_or_none():
            raise ValueError("Academic session not found")
        
        # Validate admission year matches academic session
        session = session_result.scalar_one()
        if student_data.admission_year != int(session.session_code.split('/')[0]):
            raise ValueError("Admission year must match academic session")
```

---

## Validation and Error Handling

### Validation Service
```python
# services/validation_service.py
import re
from typing import List, Dict, Any
from datetime import datetime, date

class ValidationService:
    def __init__(self):
        self.matric_pattern = re.compile(r'^20\d{2}/\d{6}$')
        self.phone_pattern = re.compile(r'^\+234\d{10}$')
        self.email_pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    
    def validate_student_data(self, student_data: Dict[str, Any]) -> List[str]:
        """Validate student data and return list of errors"""
        errors = []
        
        # Validate matric number
        if 'matric_number' in student_data:
            if not self.matric_pattern.match(student_data['matric_number']):
                errors.append("Invalid matric number format. Expected: 20XX/XXXXXX")
        
        # Validate email
        if 'email' in student_data:
            if not self.email_pattern.match(student_data['email']):
                errors.append("Invalid email format")
        
        # Validate phone number
        if 'phone_number' in student_data and student_data['phone_number']:
            if not self.phone_pattern.match(student_data['phone_number']):
                errors.append("Invalid phone number format. Expected: +234XXXXXXXXXX")
        
        # Validate dates
        if 'date_of_birth' in student_data:
            try:
                dob = student_data['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                
                # Check if student is at least 16 years old
                age = date.today().year - dob.year
                if age < 16:
                    errors.append("Student must be at least 16 years old")
            except ValueError:
                errors.append("Invalid date of birth format")
        
        # Validate academic level
        if 'current_level' in student_data:
            level = student_data['current_level']
            if not isinstance(level, int) or level < 100 or level > 900:
                errors.append("Invalid academic level. Must be between 100 and 900")
        
        return errors
```

---

## Performance Optimization

### Caching Strategy
```python
# services/cache_service.py
import redis
import json
from typing import Optional, List
from ..models.student import StudentResponse

class StudentCacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def get_student(self, student_id: str) -> Optional[StudentResponse]:
        """Get student from cache"""
        key = f"student:{student_id}"
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            student_dict = json.loads(cached_data)
            return StudentResponse(**student_dict)
        
        return None
    
    async def cache_student(self, student: StudentResponse):
        """Cache student data"""
        key = f"student:{student.id}"
        student_json = json.dumps(student.dict())
        self.redis_client.setex(key, self.cache_ttl, student_json)
    
    async def invalidate_student(self, student_id: str):
        """Remove student from cache"""
        key = f"student:{student_id}"
        self.redis_client.delete(key)
    
    async def get_student_by_matric(self, matric_number: str) -> Optional[StudentResponse]:
        """Get student by matric number from cache"""
        key = f"student:matric:{matric_number}"
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            student_dict = json.loads(cached_data)
            return StudentResponse(**student_dict)
        
        return None
    
    async def cache_student_by_matric(self, matric_number: str, student: StudentResponse):
        """Cache student by matric number"""
        key = f"student:matric:{matric_number}"
        student_json = json.dumps(student.dict())
        self.redis_client.setex(key, self.cache_ttl, student_json)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_student_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date

from ..services.student_service import StudentService
from ..models.student import StudentCreate, StudentUpdate

@pytest.mark.asyncio
class TestStudentService:
    async def test_create_student_success(self):
        # Setup
        db_mock = AsyncMock()
        validation_service = AsyncMock()
        audit_service = AsyncMock()
        
        student_service = StudentService(db_mock, validation_service, audit_service)
        
        student_data = StudentCreate(
            user_id="user-123",
            matric_number="2026/123456",
            first_name="John",
            last_name="Doe",
            email="john.doe@custech.edu.ng",
            date_of_birth=date(2000, 1, 1),
            gender="MALE",
            admission_year=2026,
            current_level=100,
            department_id="dept-123",
            academic_session_id="session-2026"
        )
        
        # Mock validation
        validation_service._validate_student_data = AsyncMock(return_value=[])
        
        # Mock database queries
        db_mock.execute.return_value.scalar_one_or_none.return_value = Mock()
        
        # Execute
        result = await student_service.create_student(student_data)
        
        # Assert
        assert result is not None
        assert result.matric_number == "2026/123456"
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()
    
    async def test_create_student_duplicate_matric(self):
        # Setup
        db_mock = AsyncMock()
        validation_service = AsyncMock()
        audit_service = AsyncMock()
        
        student_service = StudentService(db_mock, validation_service, audit_service)
        
        student_data = StudentCreate(
            user_id="user-123",
            matric_number="2026/123456",
            first_name="John",
            last_name="Doe",
            email="john.doe@custech.edu.ng",
            date_of_birth=date(2000, 1, 1),
            gender="MALE",
            admission_year=2026,
            current_level=100,
            department_id="dept-123",
            academic_session_id="session-2026"
        )
        
        # Mock validation
        validation_service._validate_student_data = AsyncMock(return_value=[])
        
        # Mock duplicate matric number
        db_mock.execute.return_value.scalar_one_or_none.return_value = Mock()  # User exists
        db_mock.execute.return_value.scalar_one_or_none.return_value = Mock()  # Duplicate matric
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Matric number already exists"):
            await student_service.create_student(student_data)
```

This comprehensive Student Lifecycle API provides:

1. **Complete CRUD Operations**: Full student record management
2. **Bulk Operations**: Efficient bulk import, update, and delete operations
3. **Lifecycle Management**: Status transitions and academic progression
4. **Data Validation**: Comprehensive validation with error handling
5. **Performance Optimization**: Caching and optimized database queries
6. **Audit Trail**: Complete logging of all student operations
7. **Search Capabilities**: Fuzzy search and filtering options
8. **CSV Import**: File-based bulk import functionality

The API maintains data integrity while providing efficient operations for managing the student lifecycle throughout their academic journey at CUSTECH.
