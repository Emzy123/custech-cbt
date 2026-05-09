# CBT Database Schema Design

## Overview

This document defines the physical database schema for the CBT system, designed to support secure, high-performance examination delivery while maintaining academic integrity and compliance with data protection requirements.

## Database Architecture

### Database Engine: PostgreSQL 14+
- **Rationale:** Advanced JSON support, robust security features, excellent performance for concurrent workloads
- **Extensions:** pgcrypto (encryption), pg_stat_statements (monitoring), pg_partman (partitioning)
- **Character Set:** UTF-8
- **Collation:** en_US.UTF-8

### Storage Strategy
```
Tablespaces:
- cbt_hot_data: SSD storage for active transactional data
- cbt_warm_data: Standard storage for recent historical data
- cbt_cold_data: Archive storage for long-term retention
- cbt_indexes: Dedicated index storage for performance optimization
```

---

## Core Schema Tables

### 1. User Management Tables

#### users
```sql
CREATE TABLESPACE cbt_hot_data LOCATION '/var/lib/postgresql/data/hot';
CREATE TABLESPACE cbt_indexes LOCATION '/var/lib/postgresql/data/indexes';

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10) CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
) TABLESPACE cbt_hot_data;

-- Indexes for users table
CREATE INDEX idx_users_username ON users(username) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_email ON users(email) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_active ON users(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_last_login ON users(last_login_at) TABLESPACE cbt_indexes;
```

#### user_roles
```sql
CREATE TYPE user_role_enum AS ENUM (
    'STUDENT', 'LECTURER', 'EXAM_OFFICER', 'ADMINISTRATOR', 'SUPER_ADMIN'
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role user_role_enum NOT NULL,
    department_id UUID REFERENCES departments(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, role, department_id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_role ON user_roles(role) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_department ON user_roles(department_id) TABLESPACE cbt_indexes;
```

### 2. Academic Structure Tables

#### academic_sessions
```sql
CREATE TABLE academic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_code VARCHAR(20) UNIQUE NOT NULL, -- e.g., "2026/2027"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_academic_sessions_current ON academic_sessions(is_current) TABLESPACE cbt_indexes;
CREATE INDEX idx_academic_sessions_dates ON academic_sessions(start_date, end_date) TABLESPACE cbt_indexes;
```

#### semesters
```sql
CREATE TYPE semester_type AS ENUM ('FIRST', 'SECOND');
CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_session_id UUID NOT NULL REFERENCES academic_sessions(id),
    semester semester_type NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(academic_session_id, semester)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_semesters_session ON semesters(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_semesters_current ON semesters(is_current) TABLESPACE cbt_indexes;
```

#### departments
```sql
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL, -- e.g., "CSC", "MTH"
    name VARCHAR(255) NOT NULL,
    faculty_code VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_departments_code ON departments(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_departments_active ON departments(is_active) TABLESPACE cbt_indexes;
```

#### courses
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL, -- e.g., "GST111"
    title VARCHAR(255) NOT NULL,
    description TEXT,
    credit_units INTEGER NOT NULL CHECK (credit_units > 0),
    level INTEGER NOT NULL CHECK (level BETWEEN 100 AND 900),
    semester_type semester_type NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_courses_code ON courses(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_level ON courses(level) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_semester ON courses(semester_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_active ON courses(is_active) TABLESPACE cbt_indexes;
```

#### course_departments
```sql
CREATE TABLE course_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_mandatory BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, department_id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_course_departments_course ON course_departments(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_course_departments_department ON course_departments(department_id) TABLESPACE cbt_indexes;
```

### 3. Student Records Tables

#### students
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    matric_number VARCHAR(20) UNIQUE NOT NULL,
    admission_year INTEGER NOT NULL,
    current_level INTEGER NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id),
    academic_session_id UUID NOT NULL REFERENCES academic_sessions(id),
    graduation_year INTEGER,
    is_active BOOLEAN DEFAULT true,
    graduated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_students_user_id ON students(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_matric ON students(matric_number) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_department ON students(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_active ON students(is_active) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_students_active_session ON students(user_id, academic_session_id) WHERE is_active = true;
```

#### student_courses
```sql
CREATE TABLE student_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    academic_session_id UUID NOT NULL REFERENCES academic_sessions(id),
    semester_id UUID NOT NULL REFERENCES semesters(id),
    registration_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'REGISTERED' CHECK (status IN ('REGISTERED', 'WITHDRAWN', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id, academic_session_id, semester_id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_student_courses_student ON student_courses(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_course ON student_courses(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_session ON student_courses(academic_session_id) TABLESPACE cbt_indexes;
```

### 4. Question Bank Tables

#### question_banks
```sql
CREATE TABLE question_banks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department_id UUID REFERENCES departments(id),
    course_id UUID REFERENCES courses(id),
    level INTEGER CHECK (level BETWEEN 100 AND 900),
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_question_banks_course ON question_banks(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_department ON question_banks(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_active ON question_banks(is_active) TABLESPACE cbt_indexes;
```

#### questions
```sql
CREATE TYPE question_type AS ENUM (
    'MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_ANSWER', 'ESSAY', 'FILL_BLANK', 'MATCHING'
);
CREATE TYPE difficulty_level AS ENUM ('EASY', 'MEDIUM', 'HARD');

CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_bank_id UUID NOT NULL REFERENCES question_banks(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type question_type NOT NULL,
    difficulty difficulty_level NOT NULL,
    points_value INTEGER NOT NULL CHECK (points_value > 0),
    time_limit_seconds INTEGER CHECK (time_limit_seconds > 0),
    explanation TEXT,
    tags JSONB, -- Array of tags as JSON array
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_questions_bank ON questions(question_bank_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_type ON questions(question_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_difficulty ON questions(difficulty) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_active ON questions(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_tags ON questions USING GIN(tags) TABLESPACE cbt_indexes;
```

#### question_options
```sql
CREATE TABLE question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    option_order INTEGER NOT NULL CHECK (option_order > 0),
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_question_options_question ON question_options(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_options_correct ON question_options(is_correct) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_question_options_unique ON question_options(question_id, option_order);
```

#### question_answers
```sql
CREATE TABLE question_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_question_answers_question ON question_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_answers_correct ON question_answers(is_correct) TABLESPACE cbt_indexes;
```

### 5. Examination Tables

#### examinations
```sql
CREATE TYPE exam_status AS ENUM ('DRAFT', 'SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED');

CREATE TABLE examinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    course_id UUID NOT NULL REFERENCES courses(id),
    academic_session_id UUID NOT NULL REFERENCES academic_sessions(id),
    semester_id UUID NOT NULL REFERENCES semesters(id),
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    total_points INTEGER NOT NULL CHECK (total_points > 0),
    pass_points INTEGER CHECK (pass_points > 0 AND pass_points <= total_points),
    status exam_status DEFAULT 'DRAFT',
    randomize_questions BOOLEAN DEFAULT false,
    randomize_options BOOLEAN DEFAULT false,
    allow_review BOOLEAN DEFAULT false,
    show_results_immediately BOOLEAN DEFAULT false,
    max_attempts INTEGER DEFAULT 1 CHECK (max_attempts > 0),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_examinations_course ON examinations(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_session ON examinations(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_date ON examinations(exam_date) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_status ON examinations(status) TABLESPACE cbt_indexes;
```

#### exam_questions
```sql
CREATE TABLE exam_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES examinations(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id),
    question_order INTEGER NOT NULL CHECK (question_order > 0),
    points_override INTEGER CHECK (points_override > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, question_order)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_exam_questions_exam ON exam_questions(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_question ON exam_questions(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_order ON exam_questions(exam_id, question_order) TABLESPACE cbt_indexes;
```

#### exam_instances
```sql
CREATE TYPE exam_instance_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'TIMED_OUT', 'ABANDONED');

CREATE TABLE exam_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES examinations(id),
    student_id UUID NOT NULL REFERENCES students(id),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    time_extension_minutes INTEGER DEFAULT 0 CHECK (time_extension_minutes >= 0),
    status exam_instance_status DEFAULT 'NOT_STARTED',
    total_points_earned INTEGER DEFAULT 0,
    total_points_possible INTEGER DEFAULT 0,
    percentage_score DECIMAL(5,2),
    grade VARCHAR(5),
    ip_address INET,
    user_agent TEXT,
    browser_fingerprint VARCHAR(255),
    biometric_verified BOOLEAN DEFAULT false,
    biometric_verification_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, student_id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_exam_instances_exam ON exam_instances(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_student ON exam_instances(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_status ON exam_instances(status) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_start_time ON exam_instances(start_time) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_exam_instances_active ON exam_instances(exam_id, student_id) WHERE status IN ('NOT_STARTED', 'IN_PROGRESS');
```

#### exam_answers
```sql
CREATE TABLE exam_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id),
    selected_option_id UUID REFERENCES question_options(id),
    answer_text TEXT,
    is_marked_for_review BOOLEAN DEFAULT false,
    time_spent_seconds INTEGER CHECK (time_spent_seconds >= 0),
    points_earned INTEGER DEFAULT 0,
    is_correct BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_instance_id, question_id)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_exam_answers_instance ON exam_answers(exam_instance_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_question ON exam_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_correct ON exam_answers(is_correct) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_review ON exam_answers(is_marked_for_review) TABLESPACE cbt_indexes;
```

### 6. Security and Audit Tables

#### user_sessions
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    browser_fingerprint VARCHAR(255),
    biometric_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    terminated_at TIMESTAMP WITH TIME ZONE,
    termination_reason VARCHAR(50)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_refresh ON user_sessions(refresh_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at) TABLESPACE cbt_indexes;
```

#### biometric_templates
```sql
CREATE TABLE biometric_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL, -- 'FINGERPRINT', 'FACIAL', etc.
    template_data BYTEA NOT NULL, -- Encrypted biometric template
    device_id VARCHAR(100),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, template_type)
) TABLESPACE cbt_hot_data;

CREATE INDEX idx_biometric_templates_user ON biometric_templates(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_type ON biometric_templates(template_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_active ON biometric_templates(is_active) TABLESPACE cbt_indexes;
```

#### audit_logs
```sql
CREATE TYPE audit_action AS ENUM (
    'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 
    'EXAM_START', 'EXAM_SUBMIT', 'GRADE_ASSIGN', 'ROLE_CHANGE',
    'EXPORT', 'IMPORT', 'SYSTEM_CHANGE'
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create partitions for audit logs
CREATE TABLE audit_logs_y2026m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m02 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01') TABLESPACE cbt_warm_data;

-- Additional partitions will be created automatically

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_action ON audit_logs(action) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_success ON audit_logs(success) TABLESPACE cbt_indexes;
```

---

## Views and Materialized Views

### Student Exam Status View
```sql
CREATE VIEW student_exam_status AS
SELECT 
    s.id as student_id,
    s.matric_number,
    u.first_name,
    u.last_name,
    e.id as exam_id,
    e.title as exam_title,
    e.exam_date,
    e.start_time,
    ei.status as instance_status,
    ei.start_time as actual_start_time,
    ei.end_time as actual_end_time,
    ei.percentage_score,
    ei.grade,
    d.name as department_name
FROM students s
JOIN users u ON s.user_id = u.id
JOIN departments d ON s.department_id = d.id
JOIN student_courses sc ON s.id = sc.student_id
JOIN examinations e ON sc.course_id = e.course_id 
    AND sc.academic_session_id = e.academic_session_id
    AND sc.semester_id = e.semester_id
LEFT JOIN exam_instances ei ON e.id = ei.exam_id AND s.id = ei.student_id
WHERE s.is_active = true;
```

### Question Bank Statistics View
```sql
CREATE MATERIALIZED VIEW question_bank_stats AS
SELECT 
    qb.id as bank_id,
    qb.title as bank_title,
    COUNT(q.id) as total_questions,
    COUNT(CASE WHEN q.question_type = 'MULTIPLE_CHOICE' THEN 1 END) as mcq_count,
    COUNT(CASE WHEN q.question_type = 'TRUE_FALSE' THEN 1 END) as tf_count,
    COUNT(CASE WHEN q.question_type = 'SHORT_ANSWER' THEN 1 END) as sa_count,
    COUNT(CASE WHEN q.question_type = 'ESSAY' THEN 1 END) as essay_count,
    COUNT(CASE WHEN q.difficulty = 'EASY' THEN 1 END) as easy_count,
    COUNT(CASE WHEN q.difficulty = 'MEDIUM' THEN 1 END) as medium_count,
    COUNT(CASE WHEN q.difficulty = 'HARD' THEN 1 END) as hard_count,
    SUM(q.points_value) as total_points,
    MAX(q.created_at) as last_updated
FROM question_banks qb
LEFT JOIN questions q ON qb.id = q.question_bank_id AND q.is_active = true
WHERE qb.is_active = true
GROUP BY qb.id, qb.title;

CREATE UNIQUE INDEX idx_question_bank_stats_id ON question_bank_stats(bank_id);
```

### Exam Performance Analytics View
```sql
CREATE MATERIALIZED VIEW exam_performance_analytics AS
SELECT 
    e.id as exam_id,
    e.title as exam_title,
    c.code as course_code,
    c.title as course_title,
    COUNT(ei.id) as total_participants,
    COUNT(CASE WHEN ei.status = 'SUBMITTED' THEN 1 END) as completed_count,
    COUNT(CASE WHEN ei.status = 'TIMED_OUT' THEN 1 END) as timed_out_count,
    COUNT(CASE WHEN ei.status = 'ABANDONED' THEN 1 END) as abandoned_count,
    ROUND(AVG(ei.percentage_score), 2) as average_score,
    MAX(ei.percentage_score) as highest_score,
    MIN(ei.percentage_score) as lowest_score,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ei.percentage_score), 2) as median_score,
    COUNT(CASE WHEN ei.percentage_score >= e.pass_points THEN 1 END) as passed_count,
    ROUND(COUNT(CASE WHEN ei.percentage_score >= e.pass_points THEN 1 END) * 100.0 / COUNT(ei.id), 2) as pass_rate
FROM examinations e
JOIN courses c ON e.course_id = c.id
LEFT JOIN exam_instances ei ON e.id = ei.exam_id
WHERE e.status = 'COMPLETED'
GROUP BY e.id, e.title, c.code, c.title;

CREATE UNIQUE INDEX idx_exam_performance_analytics_id ON exam_performance_analytics(exam_id);
```

---

## Constraints and Business Rules

### Academic Integrity Constraints
```sql
-- Prevent duplicate exam attempts for same student in same exam
ALTER TABLE exam_instances 
ADD CONSTRAINT check_single_attempt_per_exam 
CHECK (
    (SELECT COUNT(*) FROM exam_instances ei2 
     WHERE ei2.exam_id = exam_id AND ei2.student_id = student_id 
     AND ei2.status IN ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED')) <= 1
);

-- Ensure exam duration is reasonable
ALTER TABLE examinations 
ADD CONSTRAINT check_exam_duration 
CHECK (duration_minutes BETWEEN 30 AND 480); -- 30 min to 8 hours

-- Ensure exam dates are within academic session
ALTER TABLE examinations 
ADD CONSTRAINT check_exam_in_session 
CHECK (
    exam_date BETWEEN (SELECT start_date FROM academic_sessions WHERE id = academic_session_id)
    AND (SELECT end_date FROM academic_sessions WHERE id = academic_session_id)
);

-- Ensure start_time and end_time are logical for exam instances
ALTER TABLE exam_instances 
ADD CONSTRAINT check_exam_times 
CHECK (
    (end_time IS NULL) OR 
    (end_time > start_time)
);
```

### Data Quality Constraints
```sql
-- Email format validation
ALTER TABLE users 
ADD CONSTRAINT check_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Matric number format (CUSTECH format: 20XX/XXXXXX)
ALTER TABLE students 
ADD CONSTRAINT check_matric_format 
CHECK (matric_number ~* '^20\d{2}/\d{6}$');

-- Phone number format (Nigerian format)
ALTER TABLE users 
ADD CONSTRAINT check_phone_format 
CHECK (phone_number IS NULL OR phone_number ~* '^\+234\d{10}$');

-- Ensure total_points equals sum of question points
ALTER TABLE examinations 
ADD CONSTRAINT check_total_points_matches_questions 
CHECK (
    total_points = (
        SELECT COALESCE(SUM(COALESCE(eq.points_override, q.points_value)), 0)
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        WHERE eq.exam_id = examinations.id
    )
);
```

---

## Triggers and Functions

### Audit Logging Trigger
```sql
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, new_values)
        VALUES (
            COALESCE(NEW.created_by, NEW.updated_by),
            'CREATE',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_values, new_values)
        VALUES (
            COALESCE(NEW.updated_by),
            'UPDATE',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_values)
        VALUES (
            OLD.updated_by,
            'DELETE',
            TG_TABLE_NAME,
            OLD.id,
            row_to_json(OLD)
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to key tables
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_examinations
    AFTER INSERT OR UPDATE OR DELETE ON examinations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_exam_instances
    AFTER INSERT OR UPDATE OR DELETE ON exam_instances
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### Score Calculation Trigger
```sql
CREATE OR REPLACE FUNCTION calculate_exam_score()
RETURNS TRIGGER AS $$
DECLARE
    total_earned INTEGER;
    total_possible INTEGER;
    percentage DECIMAL(5,2);
    grade VARCHAR(5);
BEGIN
    -- Calculate total points earned and possible
    SELECT 
        COALESCE(SUM(points_earned), 0),
        COALESCE(SUM(q.points_value), 0)
    INTO total_earned, total_possible
    FROM exam_answers ea
    JOIN questions q ON ea.question_id = q.id
    WHERE ea.exam_instance_id = NEW.id;
    
    -- Calculate percentage
    IF total_possible > 0 THEN
        percentage := (total_earned::DECIMAL / total_possible::DECIMAL) * 100;
    ELSE
        percentage := 0;
    END IF;
    
    -- Determine grade based on CUSTECH grading scale
    IF percentage >= 70 THEN
        grade := 'A';
    ELSIF percentage >= 60 THEN
        grade := 'B';
    ELSIF percentage >= 50 THEN
        grade := 'C';
    ELSIF percentage >= 45 THEN
        grade := 'D';
    ELSE
        grade := 'F';
    END IF;
    
    -- Update the exam instance
    NEW.total_points_earned := total_earned;
    NEW.total_points_possible := total_possible;
    NEW.percentage_score := percentage;
    NEW.grade := grade;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_score_trigger
    BEFORE UPDATE ON exam_instances
    FOR EACH ROW
    WHEN (OLD.status != 'SUBMITTED' AND NEW.status = 'SUBMITTED')
    EXECUTE FUNCTION calculate_exam_score();
```

### Session Cleanup Function
```sql
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    UPDATE user_sessions 
    SET is_active = false, terminated_at = CURRENT_TIMESTAMP, termination_reason = 'EXPIRED'
    WHERE is_active = true AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    
    INSERT INTO audit_logs (action, resource_type, success)
    VALUES ('SYSTEM_CHANGE', 'USER_SESSION', true);
    
    RETURN cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule to run every hour
-- This would be configured in pg_cron or external scheduler
```

---

## Security Considerations

### Row Level Security (RLS)
```sql
-- Enable RLS on sensitive tables
ALTER TABLE exam_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Student can only see their own exam instances
CREATE POLICY student_own_exam_instances ON exam_instances
    FOR ALL
    TO authenticated_users
    USING (
        student_id IN (
            SELECT id FROM students WHERE user_id = current_user_id()
        )
    );

-- Lecturers can only see exam instances for their courses
CREATE POLICY lecturer_course_exam_instances ON exam_instances
    FOR SELECT
    TO lecturers
    USING (
        exam_id IN (
            SELECT e.id FROM examinations e
            JOIN courses c ON e.course_id = c.id
            JOIN user_roles ur ON ur.user_id = current_user_id()
            WHERE ur.role = 'LECTURER' 
            AND c.id IN (
                SELECT course_id FROM course_departments 
                WHERE department_id = ur.department_id
            )
        )
    );
```

### Data Encryption
```sql
-- Enable transparent data encryption (TDE) for sensitive columns
-- This would be configured at the database level

-- Example of application-level encryption for biometric data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to encrypt biometric templates
CREATE OR REPLACE FUNCTION encrypt_biometric_data(data BYTEA)
RETURNS BYTEA AS $$
BEGIN
    RETURN encrypt(data, 'encryption_key_here', 'aes');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt biometric data
CREATE OR REPLACE FUNCTION decrypt_biometric_data(encrypted_data BYTEA)
RETURNS BYTEA AS $$
BEGIN
    RETURN decrypt(encrypted_data, 'encryption_key_here', 'aes');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## Performance Optimization

### Partitioning Strategy
```sql
-- Partition exam_answers by semester for better performance
CREATE TABLE exam_answers_partitioned (
    LIKE exam_answers INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create current semester partition
CREATE TABLE exam_answers_current_semester
PARTITION OF exam_answers_partitioned
FOR VALUES FROM ('2026-01-01') TO ('2026-07-01')
TABLESPACE cbt_hot_data;

-- Create archive partitions
CREATE TABLE exam_answers_archive_2025
PARTITION OF exam_answers_partitioned
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01')
TABLESPACE cbt_cold_data;
```

### Index Optimization
```sql
-- Composite index for exam delivery performance
CREATE INDEX idx_exam_delivery_optimized 
ON exam_instances (exam_id, student_id, status) 
INCLUDE (start_time, end_time, biometric_verified)
TABLESPACE cbt_indexes;

-- Partial index for active exam instances only
CREATE INDEX idx_active_exam_instances 
ON exam_instances (exam_id, start_time) 
WHERE status IN ('NOT_STARTED', 'IN_PROGRESS')
TABLESPACE cbt_indexes;

-- Covering index for question retrieval
CREATE INDEX idx_question_retrieval_covering 
ON questions (question_bank_id, is_active, question_type) 
INCLUDE (question_text, points_value, time_limit_seconds)
TABLESPACE cbt_indexes;
```

---

## Backup and Recovery Strategy

### Backup Configuration
```sql
-- Create backup roles
CREATE ROLE cbt_backup_role WITH LOGIN PASSWORD 'secure_backup_password';
GRANT CONNECT ON DATABASE cbt TO cbt_backup_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cbt_backup_role;

-- Backup schedule (to be configured in pgBackRest or pg_dump)
-- 1. Full backup: Daily at 2 AM
-- 2. Incremental backup: Every 4 hours
-- 3. WAL archiving: Continuous
-- 4. Point-in-time recovery: 7-day retention
```

### Point-in-Time Recovery
```sql
-- Enable WAL archiving
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /backup/wal_archive/%f'

-- Recovery configuration example
-- restore_command = 'cp /backup/wal_archive/%f %p'
-- recovery_target_time = '2026-04-28 14:30:00'
```

This comprehensive database schema provides the foundation for a secure, performant, and scalable CBT system that maintains academic integrity while supporting the complex requirements of university examinations.
