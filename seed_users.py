"""
Seed script — creates sample LECTURER and STUDENT users with supporting academic data.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import UserRoleAssignment, UserRole, User
from cbt.models.academic import AcademicSession, Semester, Department, Course, SemesterType, CourseLevel, LecturerCourse
from cbt.models.student import Student


# Default credentials (override with env vars)
DEFAULTS = {
    'lecturer_username': os.getenv('SEED_LECTURER_USERNAME', 'lecturer'),
    'lecturer_email': os.getenv('SEED_LECTURER_EMAIL', 'lecturer@custech.edu.ng'),
    'lecturer_password': os.getenv('SEED_LECTURER_PASSWORD', 'Lecturer123!'),
    'lecturer_first': os.getenv('SEED_LECTURER_FIRST', 'John'),
    'lecturer_last': os.getenv('SEED_LECTURER_LAST', 'Doe'),
    
    'student_username': os.getenv('SEED_STUDENT_USERNAME', 'student'),
    'student_email': os.getenv('SEED_STUDENT_EMAIL', 'student@custech.edu.ng'),
    'student_password': os.getenv('SEED_STUDENT_PASSWORD', 'Student123!'),
    'student_first': os.getenv('SEED_STUDENT_FIRST', 'Jane'),
    'student_last': os.getenv('SEED_STUDENT_LAST', 'Smith'),
    'matric_number': os.getenv('SEED_MATRIC_NUMBER', '2024/001'),
}


async def ensure_academic_structure():
    """Create basic academic structure if it doesn't exist."""
    
    # Department
    dept = await Department.find_one(Department.code == "CSC")
    if not dept:
        dept = Department(
            code="CSC",
            name="Computer Science",
            faculty_code="SCI"
        )
        await dept.insert()
        print(f"[OK] Department created: {dept.code} - {dept.name}")
    else:
        print(f"[OK] Department exists: {dept.code}")
    
    # Academic Session
    session = await AcademicSession.find_one(AcademicSession.session_code == "2024/2025")
    if not session:
        session = AcademicSession(
            session_code="2024/2025",
            start_date=datetime.now(timezone.utc) - timedelta(days=180),
            end_date=datetime.now(timezone.utc) + timedelta(days=180),
            is_current=True
        )
        await session.insert()
        print(f"[OK] Academic session created: {session.session_code}")
    else:
        print(f"[OK] Academic session exists: {session.session_code}")
    
    # Semester
    semester = await Semester.find_one(
        Semester.academic_session_id == str(session.id),
        Semester.semester_type == SemesterType.FIRST
    )
    if not semester:
        semester = Semester(
            academic_session_id=str(session.id),
            semester_type=SemesterType.FIRST,
            start_date=datetime.now(timezone.utc) - timedelta(days=90),
            end_date=datetime.now(timezone.utc) + timedelta(days=90),
            is_current=True
        )
        await semester.insert()
        print(f"[OK] Semester created: {semester.semester_type.value}")
    else:
        print(f"[OK] Semester exists: {semester.semester_type.value}")
    
    # Course
    course = await Course.find_one(Course.code == "GST101")
    if not course:
        course = Course(
            code="GST101",
            title="Communication in English",
            description="Basic communication skills for undergraduates",
            credit_units=2,
            level=CourseLevel.LEVEL_100,
            semester_type=SemesterType.FIRST,
            created_by="system"
        )
        await course.insert()
        print(f"[OK] Course created: {course.code} - {course.title}")
    else:
        print(f"[OK] Course exists: {course.code}")
    
    return dept, session, semester, course


async def create_lecturer(auth_service, department):
    """Create lecturer user with LECTURER role."""
    
    try:
        user = await auth_service.register_user(
            username=DEFAULTS['lecturer_username'],
            email=DEFAULTS['lecturer_email'],
            password=DEFAULTS['lecturer_password'],
            first_name=DEFAULTS['lecturer_first'],
            last_name=DEFAULTS['lecturer_last'],
            phone_number='+2348000000001',
            ip_address='127.0.0.1',
            user_agent='seed-script',
            date_of_birth=None,
            gender='MALE'
        )
        print(f"[OK] Lecturer user created: {user.username} (id={user.id})")
        
        # Mark as verified
        await user.set({type(user).is_verified: True})
        
        # Assign LECTURER role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.LECTURER,
            department_id=str(department.id),
            granted_by='system'
        )
        await role.insert()
        print('[OK] LECTURER role assigned')
        
        return user
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"[INFO] Lecturer user already exists")
            user = await auth_service._get_user_by_username(DEFAULTS['lecturer_username'])
            
            if user:
                if not user.is_verified:
                    await user.set({type(user).is_verified: True})
                
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role == UserRole.LECTURER
                )
                if not existing:
                    role = UserRoleAssignment(
                        user_id=user.id,
                        role=UserRole.LECTURER,
                        department_id=str(department.id),
                        granted_by='system'
                    )
                    await role.insert()
                    print('[OK] LECTURER role assigned')
                else:
                    print('[OK] LECTURER role already present')
            return user
        else:
            raise


async def create_student(auth_service, department, session):
    """Create student user with STUDENT role and Student profile."""
    
    try:
        user = await auth_service.register_user(
            username=DEFAULTS['student_username'],
            email=DEFAULTS['student_email'],
            password=DEFAULTS['student_password'],
            first_name=DEFAULTS['student_first'],
            last_name=DEFAULTS['student_last'],
            phone_number='+2348000000002',
            ip_address='127.0.0.1',
            user_agent='seed-script',
            date_of_birth=None,
            gender='FEMALE'
        )
        print(f"[OK] Student user created: {user.username} (id={user.id})")
        
        # Mark as verified
        await user.set({type(user).is_verified: True})
        
        # Assign STUDENT role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.STUDENT,
            department_id=str(department.id),
            granted_by='system'
        )
        await role.insert()
        print('[OK] STUDENT role assigned')
        
        # Create Student profile
        existing_student = await Student.find_one(Student.user_id == str(user.id))
        if not existing_student:
            student_profile = Student(
                user_id=str(user.id),
                first_name=DEFAULTS['student_first'],
                last_name=DEFAULTS['student_last'],
                email=DEFAULTS['student_email'],
                phone_number='+2348000000002',
                department_id=str(department.id),
                academic_session_id=str(session.id),
                matric_number=DEFAULTS['matric_number'],
                admission_year=2024,
                current_level=100,
                graduated=False
            )
            await student_profile.insert()
            print(f"[OK] Student profile created: matric={student_profile.matric_number}")
        else:
            print(f"[OK] Student profile already exists: matric={existing_student.matric_number}")
        
        return user
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"[INFO] Student user already exists")
            user = await auth_service._get_user_by_username(DEFAULTS['student_username'])
            
            if user:
                if not user.is_verified:
                    await user.set({type(user).is_verified: True})
                
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role == UserRole.STUDENT
                )
                if not existing:
                    role = UserRoleAssignment(
                        user_id=user.id,
                        role=UserRole.STUDENT,
                        department_id=str(department.id),
                        granted_by='system'
                    )
                    await role.insert()
                    print('[OK] STUDENT role assigned')
                else:
                    print('[OK] STUDENT role already present')
            return user
        else:
            raise


async def assign_lecturer_to_course(lecturer, course):
    """Assign lecturer to the sample course."""
    
    existing = await LecturerCourse.find_one(
        LecturerCourse.lecturer_id == str(lecturer.id),
        LecturerCourse.course_id == str(course.id)
    )
    if not existing:
        assignment = LecturerCourse(
            lecturer_id=str(lecturer.id),
            course_id=str(course.id),
            assigned_by='system'
        )
        await assignment.insert()
        print(f"[OK] Lecturer assigned to course: {course.code}")
    else:
        print(f"[OK] Lecturer already assigned to course: {course.code}")


async def seed_users():
    """Main seed function."""
    print("=" * 50)
    print("CBT System — Seed Lecturer & Student")
    print("=" * 50)
    
    # 1. Boot MongoDB + Beanie
    print("\n=== Connecting to database... ===")
    await init_db()
    await redis_manager.connect()
    print("[OK] Connected")
    
    # 2. Ensure academic structure exists
    print("\n=== Setting up academic structure... ===")
    dept, session, semester, course = await ensure_academic_structure()
    
    # 3. Create auth service
    auth_service = AuthService(None, cache_manager, session_manager)
    
    # 4. Create Lecturer
    print("\n=== Creating Lecturer... ===")
    lecturer = await create_lecturer(auth_service, dept)
    
    # 5. Create Student
    print("\n=== Creating Student... ===")
    student = await create_student(auth_service, dept, session)
    
    # 6. Assign lecturer to course
    print("\n=== Assigning lecturer to course... ===")
    if lecturer:
        await assign_lecturer_to_course(lecturer, course)
    
    # Cleanup
    await redis_manager.disconnect()
    
    # Print credentials
    print("\n" + "=" * 50)
    print("SEED COMPLETE — Credentials")
    print("=" * 50)
    print("\n--- LECTURER ---")
    print(f"  Username : {DEFAULTS['lecturer_username']}")
    print(f"  Password : {DEFAULTS['lecturer_password']}")
    print(f"  Email    : {DEFAULTS['lecturer_email']}")
    print(f"  Name     : {DEFAULTS['lecturer_first']} {DEFAULTS['lecturer_last']}")
    print(f"  Role     : LECTURER")
    print(f"  Dept     : CSC (Computer Science)")
    print("\n--- STUDENT ---")
    print(f"  Username : {DEFAULTS['student_username']}")
    print(f"  Password : {DEFAULTS['student_password']}")
    print(f"  Email    : {DEFAULTS['student_email']}")
    print(f"  Name     : {DEFAULTS['student_first']} {DEFAULTS['student_last']}")
    print(f"  Matric   : {DEFAULTS['matric_number']}")
    print(f"  Role     : STUDENT")
    print(f"  Dept     : CSC (Computer Science)")
    print(f"  Level    : 100")
    print("=" * 50)
    print("\nUse these credentials to login via /api/v1/auth/login")


if __name__ == "__main__":
    asyncio.run(seed_users())
