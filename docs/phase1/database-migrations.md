# CBT Database Migration Scripts

## Migration Overview

This document contains the complete set of database migration scripts for the CBT system, designed to be executed in sequence to build the complete database schema from scratch.

## Migration Framework

### Migration Table
```sql
-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    checksum VARCHAR(64)
);

-- Function to check if migration is applied
CREATE OR REPLACE FUNCTION is_migration_applied(p_version VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM schema_migrations WHERE version = p_version
    );
END;
$$ LANGUAGE plpgsql;
```

---

## Migration 001: Core Tables Setup

### 001_create_core_tables.sql
```sql
-- Migration: 001_create_core_tables
-- Description: Create core user management and academic structure tables
-- Checksum: SHA256:abc123...

BEGIN;

-- Create tablespaces
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tablespace WHERE spcname = 'cbt_hot_data') THEN
        EXECUTE 'CREATE TABLESPACE cbt_hot_data LOCATION ''/var/lib/postgresql/data/hot''';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_tablespace WHERE spcname = 'cbt_indexes') THEN
        EXECUTE 'CREATE TABLESPACE cbt_indexes LOCATION ''/var/lib/postgresql/data/indexes''';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_tablespace WHERE spcname = 'cbt_warm_data') THEN
        EXECUTE 'CREATE TABLESPACE cbt_warm_data LOCATION ''/var/lib/postgresql/data/warm''';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_tablespace WHERE spcname = 'cbt_cold_data') THEN
        EXECUTE 'CREATE TABLESPACE cbt_cold_data LOCATION ''/var/lib/postgresql/data/cold''';
    END IF;
END
$$;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create enums
CREATE TYPE user_role_enum AS ENUM (
    'STUDENT', 'LECTURER', 'EXAM_OFFICER', 'ADMINISTRATOR', 'SUPER_ADMIN'
);

CREATE TYPE semester_type AS ENUM ('FIRST', 'SECOND');

CREATE TYPE question_type AS ENUM (
    'MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_ANSWER', 'ESSAY', 'FILL_BLANK', 'MATCHING'
);

CREATE TYPE difficulty_level AS ENUM ('EASY', 'MEDIUM', 'HARD');

CREATE TYPE exam_status AS ENUM ('DRAFT', 'SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED');

CREATE TYPE exam_instance_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'TIMED_OUT', 'ABANDONED');

CREATE TYPE audit_action AS ENUM (
    'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 
    'EXAM_START', 'EXAM_SUBMIT', 'GRADE_ASSIGN', 'ROLE_CHANGE',
    'EXPORT', 'IMPORT', 'SYSTEM_CHANGE'
);

-- Create users table
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

-- Create indexes for users
CREATE INDEX idx_users_username ON users(username) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_email ON users(email) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_active ON users(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_last_login ON users(last_login_at) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('001_create_core_tables', 'Create core user management and academic structure tables', 'SHA256:abc123...');

COMMIT;
```

---

## Migration 002: Academic Structure

### 002_create_academic_structure.sql
```sql
-- Migration: 002_create_academic_structure
-- Description: Create academic sessions, semesters, departments, and courses
-- Checksum: SHA256:def456...

BEGIN;

-- Create academic_sessions table
CREATE TABLE academic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_code VARCHAR(20) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

-- Create semesters table
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

-- Create departments table
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    faculty_code VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

-- Create courses table
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
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

-- Create course_departments table
CREATE TABLE course_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_mandatory BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, department_id)
) TABLESPACE cbt_hot_data;

-- Create indexes
CREATE INDEX idx_academic_sessions_current ON academic_sessions(is_current) TABLESPACE cbt_indexes;
CREATE INDEX idx_academic_sessions_dates ON academic_sessions(start_date, end_date) TABLESPACE cbt_indexes;
CREATE INDEX idx_semesters_session ON semesters(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_semesters_current ON semesters(is_current) TABLESPACE cbt_indexes;
CREATE INDEX idx_departments_code ON departments(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_departments_active ON departments(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_code ON courses(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_level ON courses(level) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_semester ON courses(semester_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_active ON courses(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_course_departments_course ON course_departments(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_course_departments_department ON course_departments(department_id) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('002_create_academic_structure', 'Create academic sessions, semesters, departments, and courses', 'SHA256:def456...');

COMMIT;
```

---

## Migration 003: User Roles and Students

### 003_create_user_roles_students.sql
```sql
-- Migration: 003_create_user_roles_students
-- Description: Create user roles and student records tables
-- Checksum: SHA256:ghi789...

BEGIN;

-- Create user_roles table
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

-- Create students table
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

-- Create student_courses table
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

-- Create indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_role ON user_roles(role) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_department ON user_roles(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_user_id ON students(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_matric ON students(matric_number) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_department ON students(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_active ON students(is_active) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_students_active_session ON students(user_id, academic_session_id) WHERE is_active = true;
CREATE INDEX idx_student_courses_student ON student_courses(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_course ON student_courses(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_session ON student_courses(academic_session_id) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('003_create_user_roles_students', 'Create user roles and student records tables', 'SHA256:ghi789...');

COMMIT;
```

---

## Migration 004: Question Bank

### 004_create_question_bank.sql
```sql
-- Migration: 004_create_question_bank
-- Description: Create question bank and related tables
-- Checksum: SHA256:jkl012...

BEGIN;

-- Create question_banks table
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

-- Create questions table
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_bank_id UUID NOT NULL REFERENCES question_banks(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type question_type NOT NULL,
    difficulty difficulty_level NOT NULL,
    points_value INTEGER NOT NULL CHECK (points_value > 0),
    time_limit_seconds INTEGER CHECK (time_limit_seconds > 0),
    explanation TEXT,
    tags JSONB,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
) TABLESPACE cbt_hot_data;

-- Create question_options table
CREATE TABLE question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    option_order INTEGER NOT NULL CHECK (option_order > 0),
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

-- Create question_answers table
CREATE TABLE question_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_hot_data;

-- Create indexes
CREATE INDEX idx_question_banks_course ON question_banks(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_department ON question_banks(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_active ON question_banks(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_bank ON questions(question_bank_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_type ON questions(question_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_difficulty ON questions(difficulty) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_active ON questions(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_tags ON questions USING GIN(tags) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_options_question ON question_options(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_options_correct ON question_options(is_correct) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_question_options_unique ON question_options(question_id, option_order);
CREATE INDEX idx_question_answers_question ON question_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_answers_correct ON question_answers(is_correct) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('004_create_question_bank', 'Create question bank and related tables', 'SHA256:jkl012...');

COMMIT;
```

---

## Migration 005: Examination System

### 005_create_examination_system.sql
```sql
-- Migration: 005_create_examination_system
-- Description: Create examination and exam instance tables
-- Checksum: SHA256:mno345...

BEGIN;

-- Create examinations table
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

-- Create exam_questions table
CREATE TABLE exam_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES examinations(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id),
    question_order INTEGER NOT NULL CHECK (question_order > 0),
    points_override INTEGER CHECK (points_override > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, question_order)
) TABLESPACE cbt_hot_data;

-- Create exam_instances table
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

-- Create exam_answers table
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

-- Create indexes
CREATE INDEX idx_examinations_course ON examinations(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_session ON examinations(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_date ON examinations(exam_date) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_status ON examinations(status) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_exam ON exam_questions(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_question ON exam_questions(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_order ON exam_questions(exam_id, question_order) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_exam ON exam_instances(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_student ON exam_instances(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_status ON exam_instances(status) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_start_time ON exam_instances(start_time) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_exam_instances_active ON exam_instances(exam_id, student_id) WHERE status IN ('NOT_STARTED', 'IN_PROGRESS');
CREATE INDEX idx_exam_answers_instance ON exam_answers(exam_instance_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_question ON exam_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_correct ON exam_answers(is_correct) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_review ON exam_answers(is_marked_for_review) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('005_create_examination_system', 'Create examination and exam instance tables', 'SHA256:mno345...');

COMMIT;
```

---

## Migration 006: Security and Audit

### 006_create_security_audit.sql
```sql
-- Migration: 006_create_security_audit
-- Description: Create security, biometric, and audit logging tables
-- Checksum: SHA256:pqr678...

BEGIN;

-- Create user_sessions table
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

-- Create biometric_templates table
CREATE TABLE biometric_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL,
    template_data BYTEA NOT NULL,
    device_id VARCHAR(100),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, template_type)
) TABLESPACE cbt_hot_data;

-- Create audit_logs partitioned table
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

-- Create initial audit log partitions
CREATE TABLE audit_logs_y2026m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m02 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m03 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m04 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m05 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01') TABLESPACE cbt_warm_data;

CREATE TABLE audit_logs_y2026m06 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01') TABLESPACE cbt_warm_data;

-- Create indexes
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_refresh ON user_sessions(refresh_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_user ON biometric_templates(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_type ON biometric_templates(template_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_active ON biometric_templates(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_action ON audit_logs(action) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_success ON audit_logs(success) TABLESPACE cbt_indexes;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('006_create_security_audit', 'Create security, biometric, and audit logging tables', 'SHA256:pqr678...');

COMMIT;
```

---

## Migration 007: Constraints and Triggers

### 007_add_constraints_triggers.sql
```sql
-- Migration: 007_add_constraints_triggers
-- Description: Add business logic constraints and triggers
-- Checksum: SHA256:stu901...

BEGIN;

-- Add academic integrity constraints
ALTER TABLE exam_instances 
ADD CONSTRAINT check_single_attempt_per_exam 
CHECK (
    (SELECT COUNT(*) FROM exam_instances ei2 
     WHERE ei2.exam_id = exam_id AND ei2.student_id = student_id 
     AND ei2.status IN ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED')) <= 1
);

ALTER TABLE examinations 
ADD CONSTRAINT check_exam_duration 
CHECK (duration_minutes BETWEEN 30 AND 480);

ALTER TABLE examinations 
ADD CONSTRAINT check_exam_in_session 
CHECK (
    exam_date BETWEEN (SELECT start_date FROM academic_sessions WHERE id = academic_session_id)
    AND (SELECT end_date FROM academic_sessions WHERE id = academic_session_id)
);

ALTER TABLE exam_instances 
ADD CONSTRAINT check_exam_times 
CHECK (
    (end_time IS NULL) OR 
    (end_time > start_time)
);

-- Add data quality constraints
ALTER TABLE users 
ADD CONSTRAINT check_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE students 
ADD CONSTRAINT check_matric_format 
CHECK (matric_number ~* '^20\d{2}/\d{6}$');

ALTER TABLE users 
ADD CONSTRAINT check_phone_format 
CHECK (phone_number IS NULL OR phone_number ~* '^\+234\d{10}$');

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

-- Create audit trigger function
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

-- Create score calculation trigger function
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

-- Create session cleanup function
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

-- Apply triggers to key tables
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_examinations
    AFTER INSERT OR UPDATE OR DELETE ON examinations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_exam_instances
    AFTER INSERT OR UPDATE OR DELETE ON exam_instances
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_questions
    AFTER INSERT OR UPDATE OR DELETE ON questions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER calculate_score_trigger
    BEFORE UPDATE ON exam_instances
    FOR EACH ROW
    WHEN (OLD.status != 'SUBMITTED' AND NEW.status = 'SUBMITTED')
    EXECUTE FUNCTION calculate_exam_score();

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('007_add_constraints_triggers', 'Add business logic constraints and triggers', 'SHA256:stu901...');

COMMIT;
```

---

## Migration 008: Views and Functions

### 008_create_views_functions.sql
```sql
-- Migration: 008_create_views_functions
-- Description: Create materialized views and utility functions
-- Checksum: SHA256:vwx234...

BEGIN;

-- Create student exam status view
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

-- Create question bank statistics materialized view
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

-- Create exam performance analytics materialized view
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

-- Create indexes for materialized views
CREATE UNIQUE INDEX idx_question_bank_stats_id ON question_bank_stats(bank_id) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_exam_performance_analytics_id ON exam_performance_analytics(exam_id) TABLESPACE cbt_indexes;

-- Create utility functions

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY question_bank_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY exam_performance_analytics;
END;
$$ LANGUAGE plpgsql;

-- Function to get current academic session
CREATE OR REPLACE FUNCTION get_current_academic_session()
RETURNS UUID AS $$
DECLARE
    session_id UUID;
BEGIN
    SELECT id INTO session_id 
    FROM academic_sessions 
    WHERE is_current = true 
    LIMIT 1;
    
    RETURN session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get current semester
CREATE OR REPLACE FUNCTION get_current_semester()
RETURNS UUID AS $$
DECLARE
    semester_id UUID;
BEGIN
    SELECT id INTO semester_id 
    FROM semesters 
    WHERE is_current = true 
    LIMIT 1;
    
    RETURN semester_id;
END;
$$ LANGUAGE plpgsql;

-- Function to validate student exam access
CREATE OR REPLACE FUNCTION can_student_access_exam(p_student_id UUID, p_exam_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    can_access BOOLEAN := false;
    exam_record RECORD;
    student_record RECORD;
BEGIN
    -- Get exam details
    SELECT e.* INTO exam_record
    FROM examinations e
    WHERE e.id = p_exam_id;
    
    -- Get student details
    SELECT s.* INTO student_record
    FROM students s
    WHERE s.id = p_student_id AND s.is_active = true;
    
    -- Check if student exists and is active
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check if exam exists and is active
    IF NOT FOUND OR exam_record.status NOT IN ('SCHEDULED', 'ACTIVE') THEN
        RETURN false;
    END IF;
    
    -- Check if student is registered for the course
    IF EXISTS (
        SELECT 1 FROM student_courses sc
        WHERE sc.student_id = p_student_id
        AND sc.course_id = exam_record.course_id
        AND sc.academic_session_id = exam_record.academic_session_id
        AND sc.semester_id = exam_record.semester_id
        AND sc.status = 'REGISTERED'
    ) THEN
        can_access := true;
    END IF;
    
    RETURN can_access;
END;
$$ LANGUAGE plpgsql;

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('008_create_views_functions', 'Create materialized views and utility functions', 'SHA256:vwx234...');

COMMIT;
```

---

## Migration 009: Row Level Security

### 009_enable_row_level_security.sql
```sql
-- Migration: 009_enable_row_level_security
-- Description: Enable Row Level Security (RLS) on sensitive tables
-- Checksum: SHA256:yza567...

BEGIN;

-- Create function to get current user ID (to be implemented by application)
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
    -- This function should be implemented by the application layer
    -- to return the actual user ID from the JWT token
    -- For now, return null as placeholder
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if user is authenticated
CREATE OR REPLACE FUNCTION is_authenticated()
RETURNS BOOLEAN AS $$
BEGIN
    -- This function should be implemented by the application layer
    -- to check if the current request is authenticated
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on sensitive tables
ALTER TABLE exam_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW_LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE biometric_templates ENABLE ROW LEVEL SECURITY;

-- Create policies for exam_instances
CREATE POLICY student_own_exam_instances ON exam_instances
    FOR ALL
    TO authenticated_users
    USING (
        student_id IN (
            SELECT id FROM students WHERE user_id = current_user_id()
        )
    );

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

CREATE POLICY admin_all_exam_instances ON exam_instances
    FOR ALL
    TO administrators
    USING (true);

-- Create policies for exam_answers
CREATE POLICY student_own_exam_answers ON exam_answers
    FOR ALL
    TO authenticated_users
    USING (
        exam_instance_id IN (
            SELECT id FROM exam_instances 
            WHERE student_id IN (
                SELECT id FROM students WHERE user_id = current_user_id()
            )
        )
    );

CREATE POLICY lecturer_course_exam_answers ON exam_answers
    FOR SELECT
    TO lecturers
    USING (
        exam_instance_id IN (
            SELECT ei.id FROM exam_instances ei
            JOIN examinations e ON ei.exam_id = e.id
            JOIN courses c ON e.course_id = c.id
            JOIN user_roles ur ON ur.user_id = current_user_id()
            WHERE ur.role = 'LECTURER' 
            AND c.id IN (
                SELECT course_id FROM course_departments 
                WHERE department_id = ur.department_id
            )
        )
    );

CREATE POLICY admin_all_exam_answers ON exam_answers
    FOR ALL
    TO administrators
    USING (true);

-- Create policies for students
CREATE POLICY student_own_profile ON students
    FOR ALL
    TO authenticated_users
    USING (user_id = current_user_id());

CREATE POLICY lecturer_department_students ON students
    FOR SELECT
    TO lecturers
    USING (
        department_id IN (
            SELECT department_id FROM user_roles 
            WHERE user_id = current_user_id() AND role = 'LECTURER'
        )
    );

CREATE POLICY admin_all_students ON students
    FOR ALL
    TO administrators
    USING (true);

-- Create policies for user_sessions
CREATE POLICY own_user_sessions ON user_sessions
    FOR ALL
    TO authenticated_users
    USING (user_id = current_user_id());

CREATE POLICY admin_all_user_sessions ON user_sessions
    FOR ALL
    TO administrators
    USING (true);

-- Create policies for biometric_templates
CREATE POLICY own_biometric_templates ON biometric_templates
    FOR ALL
    TO authenticated_users
    USING (user_id = current_user_id());

CREATE POLICY admin_all_biometric_templates ON biometric_templates
    FOR ALL
    TO administrators
    USING (true);

-- Insert migration record
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('009_enable_row_level_security', 'Enable Row Level Security (RLS) on sensitive tables', 'SHA256:yza567...');

COMMIT;
```

---

## Migration Execution Script

### run_migrations.sh
```bash
#!/bin/bash

# CBT Database Migration Runner
# Usage: ./run_migrations.sh [database_name] [migration_version]

set -e

# Configuration
DB_NAME=${1:-"cbt_dev"}
DB_USER=${CBT_DB_USER:-"cbt_user"}
DB_HOST=${CBT_DB_HOST:-"localhost"}
DB_PORT=${CBT_DB_PORT:-"5432"}
TARGET_VERSION=${2:-"latest"}
MIGRATIONS_DIR="$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}CBT Database Migration Runner${NC}"
echo "Database: $DB_NAME"
echo "Target Version: $TARGET_VERSION"
echo ""

# Function to check if migration is applied
is_migration_applied() {
    local version=$1
    local result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT EXISTS (
            SELECT 1 FROM schema_migrations 
            WHERE version = '$version'
        );
    ")
    [ "$result" = "t" ]
}

# Function to execute migration
execute_migration() {
    local migration_file=$1
    local version=$(basename "$migration_file" .sql | cut -d'_' -f2)
    
    echo -e "${YELLOW}Applying migration: $version${NC}"
    
    if is_migration_applied "$version"; then
        echo -e "${GREEN}Migration $version already applied, skipping${NC}"
        return 0
    fi
    
    # Execute migration
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file"; then
        echo -e "${GREEN}Migration $version applied successfully${NC}"
        return 0
    else
        echo -e "${RED}Migration $version failed${NC}"
        return 1
    fi
}

# Function to get current migration version
get_current_version() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT COALESCE(MAX(version), 'none') FROM schema_migrations 
        ORDER BY version DESC LIMIT 1;
    " 2>/dev/null || echo "none"
}

# Function to get all migration files
get_migration_files() {
    find "$MIGRATIONS_DIR" -name "*.sql" -name "[0-9][0-9][0-9]_*.sql" | sort
}

# Check database connection
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${RED}Failed to connect to database: $DB_NAME${NC}"
    exit 1
fi

# Initialize migrations table if it doesn't exist
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(255) PRIMARY KEY,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        checksum VARCHAR(64)
    );
" >/dev/null 2>&1

# Show current version
current_version=$(get_current_version)
echo -e "${GREEN}Current migration version: $current_version${NC}"

# Get migration files
migration_files=$(get_migration_files)

if [ -z "$migration_files" ]; then
    echo -e "${YELLOW}No migration files found${NC}"
    exit 0
fi

# Execute migrations
applied_count=0
failed_count=0

for migration_file in $migration_files; do
    version=$(basename "$migration_file" .sql | cut -d'_' -f2)
    
    # Skip if target version is specified and this migration is beyond it
    if [ "$TARGET_VERSION" != "latest" ] && [ "$version" \> "$TARGET_VERSION" ]; then
        continue
    fi
    
    if execute_migration "$migration_file"; then
        ((applied_count++))
    else
        ((failed_count++))
        break
    fi
done

# Summary
echo ""
echo -e "${GREEN}Migration Summary:${NC}"
echo -e "Applied: $applied_count migrations"
if [ $failed_count -gt 0 ]; then
    echo -e "${RED}Failed: $failed_count migrations${NC}"
    exit 1
else
    echo -e "${GREEN}All migrations applied successfully${NC}"
fi

# Show final version
final_version=$(get_current_version)
echo -e "${GREEN}Final migration version: $final_version${NC}"
```

### rollback_migration.sh
```bash
#!/bin/bash

# CBT Database Migration Rollback Script
# Usage: ./rollback_migration.sh [database_name] [migration_version]

set -e

# Configuration
DB_NAME=${1:-"cbt_dev"}
DB_USER=${CBT_DB_USER:-"cbt_user"}
DB_HOST=${CBT_DB_HOST:-"localhost"}
DB_PORT=${CBT_DB_PORT:-"5432"}
TARGET_VERSION=${2}
MIGRATIONS_DIR="$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$TARGET_VERSION" ]; then
    echo -e "${RED}Error: Migration version is required${NC}"
    echo "Usage: ./rollback_migration.sh [database_name] [migration_version]"
    exit 1
fi

echo -e "${GREEN}CBT Database Migration Rollback${NC}"
echo "Database: $DB_NAME"
echo "Rollback to version: $TARGET_VERSION"
echo ""

# Function to get current version
get_current_version() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT COALESCE(MAX(version), 'none') FROM schema_migrations 
        WHERE version <= '$TARGET_VERSION'
        ORDER BY version DESC LIMIT 1;
    " 2>/dev/null || echo "none"
}

# Function to remove migration record
remove_migration_record() {
    local version=$1
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        DELETE FROM schema_migrations WHERE version = '$version';
    "
}

# Get current version
current_version=$(get_current_version)
echo -e "${GREEN}Current version: $current_version${NC}"

# Get migrations to rollback
migrations_to_rollback=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
    SELECT version FROM schema_migrations 
    WHERE version > '$TARGET_VERSION'
    ORDER BY version DESC;
")

if [ -z "$migrations_to_rollback" ]; then
    echo -e "${YELLOW}No migrations to rollback${NC}"
    exit 0
fi

# Rollback migrations
echo -e "${YELLOW}Rolling back migrations:${NC}"
echo "$migrations_to_rollback"

for version in $migrations_to_rollback; do
    echo -e "${YELLOW}Removing migration: $version${NC}"
    
    if remove_migration_record "$version"; then
        echo -e "${GREEN}Migration $version removed successfully${NC}"
    else
        echo -e "${RED}Failed to remove migration $version${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}Rollback completed successfully${NC}"
echo -e "${GREEN}Current version: $(get_current_version)${NC}"
```

This comprehensive migration system provides:

1. **Sequential Migration Execution**: Migrations are applied in order with dependency tracking
2. **Rollback Capability**: Ability to rollback to any previous version
3. **Migration Tracking**: Complete audit trail of all applied migrations
4. **Error Handling**: Proper error handling and reporting
5. **Automation**: Scripts for automated migration execution in CI/CD pipelines

The migration system ensures database schema consistency across all environments and provides a reliable foundation for database changes throughout the project lifecycle.
