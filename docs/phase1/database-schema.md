# CBT Database Schema Design (MongoDB & Beanie ODM)

## Overview

The CUSTECH CBT system is built using a modern Document Store architecture powered by **MongoDB 6.0+** and the **Beanie ODM** (Object-Document Mapper) for Python. This document outlines the physical collections, indexes, and document structures of the database, reflecting the high-performance, real-time nature of examination delivery and proctoring.

## Database Architecture

### Database Engine: MongoDB & Beanie ODM
* **Rationale:** High write throughput for answers autosave, horizontal scale, flexible nested documents, and high agility.
* **Beanie ODM:** Uses Pydantic for validation and standard async MongoDB drivers for speed and correctness.
* **Character Set:** UTF-8 / BSON standard.

---

## Core Document Collections

### 1. User & Access Control

#### users (`User`)
Stores account authentication and profile information.

```python
class User(BaseDocument):
    username: str                     # Unique username (Matric / Staff ID)
    email: str                        # Unique email address
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[Gender] = None
    password_hash: str
    salt: str
    is_verified: bool = False
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
```
**Indexes:**
* Unique index on `username`
* Unique index on `email`

#### user_roles (`UserRoleAssignment`)
Maps users to specific departments and access roles.

```python
class UserRoleAssignment(BaseDocument):
    user_id: str                      # References users
    role: UserRole                    # STUDENT, LECTURER, EXAM_OFFICER, INVIGILATOR, ADMINISTRATOR, SUPER_ADMIN
    department_id: Optional[str] = None # References departments
    granted_at: datetime
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
```
**Indexes:**
* Compound index on `(user_id, role, department_id)`

---

### 2. Academic Structure

#### academic_sessions (`AcademicSession`)
Defines the academic session boundaries (e.g. "2026/2027").

```python
class AcademicSession(BaseDocument):
    session_code: str                 # e.g., "2026/2027"
    start_date: datetime
    end_date: datetime
    is_current: bool = False
```

#### semesters (`Semester`)
Defines semesters under a session.

```python
class Semester(BaseDocument):
    academic_session_id: str          # References academic_sessions
    semester_type: SemesterType       # FIRST, SECOND
    start_date: datetime
    end_date: datetime
    is_current: bool = False
```

#### departments (`Department`)
Defines faculties or departments.

```python
class Department(BaseDocument):
    code: str                         # e.g., "CSC", "MTH"
    name: str
    faculty_code: Optional[str] = None
```

#### courses (`Course`)
Defines subject courses in the curriculum.

```python
class Course(BaseDocument):
    code: str                         # e.g., "CSC301"
    title: str
    description: Optional[str] = None
    credit_units: int
    level: CourseLevel                # 100, 200, ..., 900
    semester_type: SemesterType
    created_by: Optional[str] = None
```

---

### 3. Student Records

#### students (`Student`)
Stores active student records associated with users.

```python
class Student(BaseDocument):
    user_id: str                      # References users
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    department_id: str                # References departments
    academic_session_id: str          # References academic_sessions
    matric_number: str                # Unique matric number
    admission_year: int
    current_level: int
    graduation_year: Optional[int] = None
    graduated: bool = False
```
**Indexes:**
* Unique index on `matric_number`
* Unique index on `user_id`

#### student_courses (`StudentCourse`)
Registrations of students to registered courses.

```python
class StudentCourse(BaseDocument):
    student_id: str                   # References students
    course_id: str                    # References courses
    academic_session_id: str          # References academic_sessions
    semester_id: str                  # References semesters
    registration_date: datetime
    status: str = "REGISTERED"        # REGISTERED, WITHDRAWN, COMPLETED, FAILED
```

---

### 4. Question Bank

#### question_banks (`QuestionBank`)
Containers for organizing exam questions.

```python
class QuestionBank(BaseDocument):
    title: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    course_id: Optional[str] = None
    level: Optional[int] = None
    is_public: bool = False
    created_by: str
```

#### questions (`Question`)
Individual exam questions containing difficulty, cognitive type, and options markers.

```python
class Question(BaseDocument):
    question_text: str
    question_type: QuestionType       # MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, ESSAY
    difficulty: QuestionDifficulty    # EASY, MEDIUM, HARD
    points_value: int
    time_limit_seconds: Optional[int] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    version: int = 1
    question_bank_id: Optional[str] = None
    course_id: str
    topic: str
    cognitive_level: CognitiveLevel   # Bloom's taxonomy
    status: QuestionStatus = QuestionStatus.DRAFT
    created_by: str
    updated_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    image_url: Optional[str] = None
    
    # Security/Hardening features
    encrypted_question_text: Optional[str] = None
    encryption_key_id: Optional[str] = None
    encrypted_at: Optional[datetime] = None
    encrypted_options: Optional[str] = None
```

#### question_options (`QuestionOption`)
MCQ options linked to Questions.

```python
class QuestionOption(BaseDocument):
    question_id: str                  # References questions
    option_text: str
    is_correct: bool = False
    option_order: int
    explanation: Optional[str] = None
```

---

### 5. Examination & Lifecycle

#### examinations (`Examination`)
Defines the configured exam events.

```python
class Examination(BaseDocument):
    title: str
    description: Optional[str] = None
    exam_date: datetime
    start_time: datetime
    duration_minutes: int
    total_points: int
    pass_points: Optional[int] = None
    status: ExamStatus = ExamStatus.DRAFT # DRAFT, SCHEDULED, ACTIVE, COMPLETED, CANCELLED
    randomize_questions: bool = False
    randomize_options: bool = False
    allow_review: bool = False
    show_results_immediately: bool = False
    max_attempts: int = 1
    settings: Optional[Dict[str, Any]] = None
    course_id: str                    # References courses
    academic_session_id: str          # References academic_sessions
    semester_id: str                  # References semesters
    created_by: str
    updated_by: Optional[str] = None
    release_mode: str = "manual"
    release_at: Optional[datetime] = None
    embargo_active: bool = False      # Withholds grades on student view
```

#### exam_questions (`ExamQuestion`)
Links questions included in an examination.

```python
class ExamQuestion(BaseDocument):
    examination_id: str               # References examinations
    question_id: str                  # References questions
    question_order: int
    points_override: Optional[int] = None
```

#### exam_instances (`ExamInstance`)
Stores a student's active exam session.

```python
class ExamInstance(BaseDocument):
    examination_id: str               # References examinations
    student_id: str                   # References students
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_extension_minutes: int = 0
    status: ExamInstanceStatus = ExamInstanceStatus.NOT_STARTED
    total_points_earned: int = 0
    total_points_possible: int = 0
    percentage_score: Optional[float] = None
    grade: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    biometric_verified: bool = False
    biometric_verification_time: Optional[datetime] = None
    rules_accepted: bool = False
    proctoring_strikes: int = 0
```
**Indexes:**
* Compound index on `(examination_id, student_id)` (Unique)

#### exam_answers (`ExamAnswer`)
Stores student responses (autosaved in real-time).

```python
class ExamAnswer(BaseDocument):
    exam_instance_id: str             # References exam_instances
    question_id: str                  # References questions
    exam_question_id: Optional[str] = None
    selected_option_id: Optional[str] = None
    answer_text: Optional[str] = None
    is_marked_for_review: bool = False
    time_spent_seconds: int = 0
    points_earned: int = 0
    is_correct: Optional[bool] = None
```
**Indexes:**
* Compound index on `(exam_instance_id, question_id)` (Unique)

---

### 6. Security & Auditing

#### user_sessions (`UserSession`)
Tracks active browser login sessions and refresh tokens.

```python
class UserSession(BaseDocument):
    user_id: str
    session_token: str
    refresh_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    biometric_verified: bool = False
    expires_at: datetime
    last_activity_at: datetime
```

#### audit_logs (`AuditLog`)
Compliance tracking of academic and system administrative mutations.

```python
class AuditLog(BaseDocument):
    user_id: Optional[str] = None
    action: AuditAction               # CREATE, UPDATE, DELETE, LOGIN, EXAM_START, EXAM_SUBMIT...
    resource_type: str                # Collection name modified
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
```

#### venues (`Venue`)
Physical examination spaces mapping rows/cols capacity.

```python
class Venue(BaseDocument):
    name: str
    code: str
    capacity: int
    rows: Optional[int] = None
    columns: Optional[int] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_by: Optional[str] = None
```

#### exam_venue_assignments (`ExamVenueAssignment`)
Proctoring assignments linking seats to candidates.

```python
class ExamVenueAssignment(BaseDocument):
    examination_id: str
    venue_id: str
    student_id: str
    seat_row: Optional[int] = None
    seat_column: Optional[int] = None
    seat_label: Optional[str] = None
    exam_number: Optional[str] = None
    assigned_by: Optional[str] = None
```

---

## Constraints & Security Audits

1. **Academic Integrity:** Exam instances restrict double submission using MongoDB unique compounds.
2. **Access Control:** User authorization RBAC is dynamically validated via FastAPI dependency injection guards and verified token signatures.
3. **Data Quality Verification:** Validation rules are fully maintained at-rest inside Pydantic model configurations (e.g. matric format `^20\d{2}/\d{6}$`).
