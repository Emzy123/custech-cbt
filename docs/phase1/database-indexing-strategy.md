# CBT Database Indexing Strategy

## Overview

This document defines the comprehensive indexing strategy for the CBT system, designed to optimize performance for high-concurrency examination scenarios while maintaining data integrity and supporting complex analytical queries.

## Indexing Philosophy

### Performance Requirements
- **Concurrent Users:** Support 2,000+ simultaneous exam takers
- **Query Response Time:** < 100ms for exam delivery queries
- **Write Performance:** Handle 1,000+ answer submissions per minute
- **Analytical Queries:** Support real-time reporting without impacting exam performance

### Indexing Principles
1. **Read-Write Balance:** Optimize for read-heavy exam delivery with write-heavy answer submission
2. **Covering Indexes:** Use INCLUDE clauses to eliminate table access where possible
3. **Partial Indexes:** Index only relevant data to reduce storage and maintenance overhead
4. **Composite Indexes:** Optimize for common query patterns
5. **Index Maintenance:** Monitor and optimize index usage over time

---

## Core Indexing Strategy

### 1. User Management Indexes

#### Primary Performance Indexes
```sql
-- Users table indexes
CREATE INDEX idx_users_username ON users(username) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_email ON users(email) TABLESPACE cbt_indexes;
CREATE INDEX idx_users_active ON users(is_active) TABLESPACE cbt_indexes;

-- Composite index for login queries
CREATE INDEX idx_users_login_lookup ON users(username, is_active, failed_login_attempts) 
TABLESPACE cbt_indexes;

-- Covering index for user profile retrieval
CREATE INDEX idx_users_profile_covering ON users(id) 
INCLUDE (username, email, first_name, last_name, is_active) 
TABLESPACE cbt_indexes;

-- Partial index for locked accounts
CREATE INDEX idx_users_locked ON users(locked_until) 
WHERE locked_until > CURRENT_TIMESTAMP 
TABLESPACE cbt_indexes;
```

#### User Roles Indexes
```sql
-- Role-based access queries
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_role ON user_roles(role) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_roles_department ON user_roles(department_id) TABLESPACE cbt_indexes;

-- Composite index for permission checks
CREATE INDEX idx_user_roles_permission_check ON user_roles(user_id, role, is_active) 
INCLUDE (department_id, expires_at) 
TABLESPACE cbt_indexes;

-- Partial index for active roles only
CREATE INDEX idx_user_roles_active ON user_roles(user_id, role) 
WHERE is_active = true AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP) 
TABLESPACE cbt_indexes;
```

### 2. Academic Structure Indexes

#### Academic Sessions and Semesters
```sql
-- Current session lookup
CREATE INDEX idx_academic_sessions_current ON academic_sessions(is_current) TABLESPACE cbt_indexes;

-- Date range queries for academic calendar
CREATE INDEX idx_academic_sessions_dates ON academic_sessions(start_date, end_date) TABLESPACE cbt_indexes;

-- Semester hierarchy queries
CREATE INDEX idx_semesters_session ON semesters(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_semesters_current ON semesters(is_current) TABLESPACE cbt_indexes;

-- Composite index for current academic period
CREATE INDEX idx_semesters_current_period ON semesters(academic_session_id, semester_type, is_current) 
TABLESPACE cbt_indexes;
```

#### Departments and Courses
```sql
-- Department lookups
CREATE INDEX idx_departments_code ON departments(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_departments_active ON departments(is_active) TABLESPACE cbt_indexes;

-- Course catalog queries
CREATE INDEX idx_courses_code ON courses(code) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_level ON courses(level) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_semester ON courses(semester_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_courses_active ON courses(is_active) TABLESPACE cbt_indexes;

-- Composite index for course enrollment
CREATE INDEX idx_courses_enrollment_lookup ON courses(level, semester_type, is_active) 
INCLUDE (code, title, credit_units) 
TABLESPACE cbt_indexes;

-- Course-department relationship
CREATE INDEX idx_course_departments_course ON course_departments(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_course_departments_department ON course_departments(department_id) TABLESPACE cbt_indexes;

-- Composite index for department course catalog
CREATE INDEX idx_course_departments_dept_catalog ON course_departments(department_id, is_mandatory) 
TABLESPACE cbt_indexes;
```

### 3. Student Records Indexes

#### Student Management
```sql
-- Student identification
CREATE INDEX idx_students_user_id ON students(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_matric ON students(matric_number) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_department ON students(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_active ON students(is_active) TABLESPACE cbt_indexes;

-- Composite index for active student lookup
CREATE INDEX idx_students_active_lookup ON students(is_active, academic_session_id) 
INCLUDE (matric_number, current_level, department_id) 
TABLESPACE cbt_indexes;

-- Unique constraint for active session
CREATE UNIQUE INDEX idx_students_active_session ON students(user_id, academic_session_id) 
WHERE is_active = true 
TABLESPACE cbt_indexes;

-- Partial index for graduated students
CREATE INDEX idx_students_graduated ON students(graduated, graduation_year) 
WHERE graduated = true 
TABLESPACE cbt_indexes;
```

#### Student Course Registration
```sql
-- Course enrollment queries
CREATE INDEX idx_student_courses_student ON student_courses(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_course ON student_courses(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_student_courses_session ON student_courses(academic_session_id) TABLESPACE cbt_indexes;

-- Composite index for student course lookup
CREATE INDEX idx_student_courses_lookup ON student_courses(student_id, academic_session_id, semester_id) 
INCLUDE (course_id, status) 
TABLESPACE cbt_indexes;

-- Partial index for active registrations
CREATE INDEX idx_student_courses_active ON student_courses(student_id, course_id) 
WHERE status = 'REGISTERED' 
TABLESPACE cbt_indexes;

-- Composite index for exam eligibility
CREATE INDEX idx_student_courses_exam_eligibility ON student_courses(course_id, academic_session_id, semester_id, status) 
WHERE status = 'REGISTERED' 
TABLESPACE cbt_indexes;
```

### 4. Question Bank Indexes

#### Question Bank Management
```sql
-- Question bank organization
CREATE INDEX idx_question_banks_course ON question_banks(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_department ON question_banks(department_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_banks_active ON question_banks(is_active) TABLESPACE cbt_indexes;

-- Composite index for question bank discovery
CREATE INDEX idx_question_banks_discovery ON question_banks(is_active, course_id, level) 
INCLUDE (title, description) 
TABLESPACE cbt_indexes;

-- Partial index for public question banks
CREATE INDEX idx_question_banks_public ON question_banks(is_public, is_active) 
WHERE is_public = true AND is_active = true 
TABLESPACE cbt_indexes;
```

#### Question Content Indexes
```sql
-- Question retrieval
CREATE INDEX idx_questions_bank ON questions(question_bank_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_type ON questions(question_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_difficulty ON questions(difficulty) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_active ON questions(is_active) TABLESPACE cbt_indexes;

-- GIN index for tag searches
CREATE INDEX idx_questions_tags ON questions USING GIN(tags) TABLESPACE cbt_indexes;

-- Composite index for question selection
CREATE INDEX idx_questions_selection ON questions(question_bank_id, is_active, difficulty) 
INCLUDE (question_type, points_value, time_limit_seconds) 
TABLESPACE cbt_indexes;

-- Covering index for exam question delivery
CREATE INDEX idx_questions_exam_delivery ON questions(id) 
INCLUDE (question_text, question_type, points_value, time_limit_seconds) 
WHERE is_active = true 
TABLESPACE cbt_indexes;

-- Partial index for specific question types
CREATE INDEX idx_questions_mcq ON questions(question_bank_id, difficulty) 
WHERE question_type = 'MULTIPLE_CHOICE' AND is_active = true 
TABLESPACE cbt_indexes;

CREATE INDEX idx_questions_essay ON questions(question_bank_id, difficulty) 
WHERE question_type = 'ESSAY' AND is_active = true 
TABLESPACE cbt_indexes;
```

#### Question Options and Answers
```sql
-- Option retrieval for MCQ questions
CREATE INDEX idx_question_options_question ON question_options(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_options_correct ON question_options(is_correct) TABLESPACE cbt_indexes;
CREATE UNIQUE INDEX idx_question_options_unique ON question_options(question_id, option_order) TABLESPACE cbt_indexes;

-- Covering index for option display
CREATE INDEX idx_question_options_display ON question_options(question_id) 
INCLUDE (option_text, is_correct, option_order) 
TABLESPACE cbt_indexes;

-- Answer key for grading
CREATE INDEX idx_question_answers_question ON question_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_question_answers_correct ON question_answers(is_correct) TABLESPACE cbt_indexes;

-- Covering index for answer validation
CREATE INDEX idx_question_answers_validation ON question_answers(question_id) 
INCLUDE (answer_text, is_correct) 
TABLESPACE cbt_indexes;
```

### 5. Examination System Indexes

#### Exam Management
```sql
-- Examination lookup
CREATE INDEX idx_examinations_course ON examinations(course_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_session ON examinations(academic_session_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_date ON examinations(exam_date) TABLESPACE cbt_indexes;
CREATE INDEX idx_examinations_status ON examinations(status) TABLESPACE cbt_indexes;

-- Composite index for exam scheduling
CREATE INDEX idx_examinations_schedule ON examinations(course_id, academic_session_id, semester_id, status) 
INCLUDE (exam_date, start_time, duration_minutes) 
TABLESPACE cbt_indexes;

-- Partial index for active exams
CREATE INDEX idx_examinations_active ON examinations(exam_date, status) 
WHERE status IN ('SCHEDULED', 'ACTIVE') 
TABLESPACE cbt_indexes;

-- Covering index for exam details
CREATE INDEX idx_examinations_details ON examinations(id) 
INCLUDE (title, course_id, exam_date, start_time, duration_minutes, status) 
TABLESPACE cbt_indexes;
```

#### Exam Questions
```sql
-- Exam question ordering
CREATE INDEX idx_exam_questions_exam ON exam_questions(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_question ON exam_questions(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_questions_order ON exam_questions(exam_id, question_order) TABLESPACE cbt_indexes;

-- Covering index for question retrieval during exam
CREATE INDEX idx_exam_questions_exam_covering ON exam_questions(exam_id, question_order) 
INCLUDE (question_id, points_override) 
TABLESPACE cbt_indexes;
```

#### Exam Instances (Critical for Performance)
```sql
-- Exam instance tracking
CREATE INDEX idx_exam_instances_exam ON exam_instances(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_student ON exam_instances(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_status ON exam_instances(status) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_start_time ON exam_instances(start_time) TABLESPACE cbt_indexes;

-- CRITICAL: Composite index for exam delivery performance
CREATE INDEX idx_exam_instances_delivery ON exam_instances(exam_id, student_id, status) 
INCLUDE (start_time, end_time, biometric_verified) 
TABLESPACE cbt_indexes;

-- CRITICAL: Partial index for active exam instances
CREATE UNIQUE INDEX idx_exam_instances_active ON exam_instances(exam_id, student_id) 
WHERE status IN ('NOT_STARTED', 'IN_PROGRESS') 
TABLESPACE cbt_indexes;

-- Covering index for exam status monitoring
CREATE INDEX idx_exam_instances_monitoring ON exam_instances(status, start_time) 
INCLUDE (exam_id, student_id, percentage_score) 
WHERE status IN ('IN_PROGRESS', 'SUBMITTED') 
TABLESPACE cbt_indexes;

-- Composite index for student exam history
CREATE INDEX idx_exam_instances_student_history ON exam_instances(student_id, status, start_time) 
INCLUDE (exam_id, percentage_score, grade) 
TABLESPACE cbt_indexes;
```

#### Exam Answers (Write-Heavy Table)
```sql
-- Answer tracking
CREATE INDEX idx_exam_answers_instance ON exam_answers(exam_instance_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_question ON exam_answers(question_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_correct ON exam_answers(is_correct) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_answers_review ON exam_answers(is_marked_for_review) TABLESPACE cbt_indexes;

-- CRITICAL: Composite index for answer submission performance
CREATE INDEX idx_exam_answers_submission ON exam_answers(exam_instance_id, question_id) 
INCLUDE (selected_option_id, answer_text, is_marked_for_review) 
TABLESPACE cbt_indexes;

-- Partial index for unanswered questions
CREATE INDEX idx_exam_answers_unanswered ON exam_answers(exam_instance_id) 
WHERE selected_option_id IS NULL AND answer_text IS NULL 
TABLESPACE cbt_indexes;

-- Covering index for grading
CREATE INDEX idx_exam_answers_grading ON exam_answers(exam_instance_id) 
INCLUDE (question_id, selected_option_id, answer_text, points_earned, is_correct) 
WHERE is_correct IS NOT NULL 
TABLESPACE cbt_indexes;
```

### 6. Security and Audit Indexes

#### Session Management
```sql
-- Session lookup
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_refresh ON user_sessions(refresh_token) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) TABLESPACE cbt_indexes;
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at) TABLESPACE cbt_indexes;

-- Composite index for session validation
CREATE INDEX idx_user_sessions_validation ON user_sessions(session_token, is_active, expires_at) 
INCLUDE (user_id, ip_address, biometric_verified) 
TABLESPACE cbt_indexes;

-- Partial index for active sessions
CREATE INDEX idx_user_sessions_active_partial ON user_sessions(user_id, last_activity_at) 
WHERE is_active = true 
TABLESPACE cbt_indexes;

-- Covering index for session cleanup
CREATE INDEX idx_user_sessions_cleanup ON user_sessions(expires_at, is_active) 
INCLUDE (id, user_id) 
WHERE expires_at < CURRENT_TIMESTAMP 
TABLESPACE cbt_indexes;
```

#### Biometric Templates
```sql
-- Biometric lookup
CREATE INDEX idx_biometric_templates_user ON biometric_templates(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_type ON biometric_templates(template_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_biometric_templates_active ON biometric_templates(is_active) TABLESPACE cbt_indexes;

-- Composite index for biometric verification
CREATE INDEX idx_biometric_templates_verification ON biometric_templates(user_id, template_type, is_active) 
INCLUDE (template_data, enrollment_date) 
TABLESPACE cbt_indexes;
```

#### Audit Logs (Partitioned Table)
```sql
-- Audit log queries (these will be created on each partition)
-- Example for current month partition
CREATE INDEX idx_audit_logs_user ON audit_logs_y2026m04(user_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_action ON audit_logs_y2026m04(action) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_resource ON audit_logs_y2026m04(resource_type, resource_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_created ON audit_logs_y2026m04(created_at) TABLESPACE cbt_indexes;
CREATE INDEX idx_audit_logs_success ON audit_logs_y2026m04(success) TABLESPACE cbt_indexes;

-- Composite index for security monitoring
CREATE INDEX idx_audit_logs_security_monitoring ON audit_logs_y2026m04(action, created_at, success) 
INCLUDE (user_id, resource_type, ip_address) 
WHERE action IN ('LOGIN', 'EXAM_START', 'EXAM_SUBMIT', 'ROLE_CHANGE') 
TABLESPACE cbt_indexes;

-- Partial index for failed security events
CREATE INDEX idx_audit_logs_security_failures ON audit_logs_y2026m04(action, created_at, user_id) 
WHERE success = false AND action IN ('LOGIN', 'EXAM_START', 'EXAM_SUBMIT') 
TABLESPACE cbt_indexes;
```

---

## Specialized Indexes for Performance

### 1. Exam Delivery Optimization

#### High-Concurrency Exam Access
```sql
-- Critical index for exam start validation
CREATE INDEX CONCURRENTLY idx_exam_instances_start_validation 
ON exam_instances(exam_id, student_id, status, biometric_verified) 
INCLUDE (start_time, time_extension_minutes) 
WHERE status IN ('NOT_STARTED', 'IN_PROGRESS') 
TABLESPACE cbt_indexes;

-- Index for question retrieval during exam
CREATE INDEX CONCURRENTLY idx_exam_questions_retrieval 
ON exam_questions(exam_id, question_order) 
INCLUDE (question_id, points_override) 
TABLESPACE cbt_indexes;

-- Index for answer submission performance
CREATE INDEX CONCURRENTLY idx_exam_answers_submission_performance 
ON exam_answers(exam_instance_id, question_id) 
INCLUDE (selected_option_id, answer_text, time_spent_seconds) 
TABLESPACE cbt_indexes;
```

### 2. Real-time Analytics

#### Performance Monitoring
```sql
-- Index for active exam monitoring
CREATE INDEX idx_exam_instances_active_monitoring 
ON exam_instances(status, start_time) 
INCLUDE (exam_id, student_id, percentage_score, ip_address) 
WHERE status IN ('IN_PROGRESS', 'SUBMITTED') 
TABLESPACE cbt_indexes;

-- Index for completion rate tracking
CREATE INDEX idx_exam_instances_completion_tracking 
ON exam_instances(exam_id, status) 
INCLUDE (student_id, start_time, end_time, percentage_score) 
TABLESPACE cbt_indexes;
```

### 3. Search and Discovery

#### Full-Text Search (if needed)
```sql
-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Trigram index for fuzzy name matching
CREATE INDEX idx_students_name_trgm 
ON students USING GIN (first_name, last_name) 
TABLESPACE cbt_indexes;

-- Trigram index for question text search
CREATE INDEX idx_questions_text_trgm 
ON questions USING GIN (question_text) 
TABLESPACE cbt_indexes;
```

---

## Index Maintenance Strategy

### 1. Index Usage Monitoring

#### Monitoring Query
```sql
-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

#### Index Bloat Detection
```sql
-- Check for index bloat
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size,
    pg_size_pretty(pg_relation_size(indexrelid) - (
        SELECT sum(pg_relation_size(heapid))
        FROM pg_heap WHERE heapid = pg_index.indexrelid
    )) AS bloat
FROM pg_index 
JOIN pg_stat_user_indexes ON pg_index.indexrelid = pg_stat_user_indexes.indexrelid
WHERE schemaname = 'public';
```

### 2. Index Optimization

#### Rebuild Strategy
```sql
-- Function to rebuild fragmented indexes
CREATE OR REPLACE FUNCTION rebuild_fragmented_indexes(threshold_percent INTEGER DEFAULT 30)
RETURNS TEXT AS $$
DECLARE
    index_record RECORD;
    rebuild_count INTEGER := 0;
    result_text TEXT := '';
BEGIN
    FOR index_record IN 
        SELECT 
            n.nspname as schema_name,
            c.relname as table_name,
            i.relname as index_name,
            pg_stat_get_live_tuples(i.oid) as live_tuples,
            pg_stat_get_dead_tuples(i.oid) as dead_tuples
        FROM pg_class i
        JOIN pg_index ix ON i.oid = ix.indexrelid
        JOIN pg_class c ON ix.indrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE i.relkind = 'i'
        AND n.nspname = 'public'
        AND pg_stat_get_live_tuples(i.oid) > 0
    LOOP
        IF index_record.dead_tuples > 0 THEN
            DECLARE
                bloat_percent DECIMAL;
            BEGIN
                bloat_percent := (index_record.dead_tuples::DECIMAL / 
                               (index_record.live_tuples + index_record.dead_tuples)) * 100;
                
                IF bloat_percent > threshold_percent THEN
                    EXECUTE 'REINDEX INDEX CONCURRENTLY ' || 
                           quote_ident(index_record.schema_name) || '.' || 
                           quote_ident(index_record.index_name);
                    rebuild_count := rebuild_count + 1;
                    result_text := result_text || 'Rebuilt: ' || 
                                   index_record.schema_name || '.' || 
                                   index_record.index_name || ' (' || 
                                   bloat_percent::TEXT || '% bloat)' || E'\n';
                END IF;
            END;
        END IF;
    END LOOP;
    
    RETURN 'Rebuilt ' || rebuild_count::TEXT || ' indexes.' || E'\n' || result_text;
END;
$$ LANGUAGE plpgsql;
```

### 3. Automated Maintenance

#### Scheduled Tasks
```sql
-- Function to update table statistics
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS VOID AS $$
BEGIN
    -- Update statistics for high-traffic tables
    ANALYZE exam_instances;
    ANALYZE exam_answers;
    ANALYZE user_sessions;
    ANALYZE questions;
    ANALYZE examinations;
    
    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY question_bank_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY exam_performance_analytics;
END;
$$ LANGUAGE plpgsql;

-- Schedule for daily statistics update (using pg_cron)
-- SELECT cron.schedule('update-stats', '0 2 * * *', 'SELECT update_table_statistics();');
```

---

## Performance Testing and Validation

### 1. Benchmark Queries

#### Exam Delivery Benchmark
```sql
-- Query: Get next question for student
EXPLAIN (ANALYZE, BUFFERS) 
SELECT q.id, q.question_text, q.question_type, q.points_value, q.time_limit_seconds,
       qo.option_id, qo.option_text, qo.is_correct
FROM exam_instances ei
JOIN exam_questions eq ON ei.exam_id = eq.exam_id
JOIN questions q ON eq.question_id = q.id
LEFT JOIN question_options qo ON q.id = qo.question_id
WHERE ei.id = 'exam-instance-uuid' 
  AND eq.question_order = (
    SELECT COALESCE(MAX(question_order), 0) + 1 
    FROM exam_answers ea 
    WHERE ea.exam_instance_id = ei.id
  );

-- Expected: Index-only scan using idx_exam_instances_delivery and idx_exam_questions_exam_covering
```

#### Bulk Answer Submission Benchmark
```sql
-- Query: Batch insert exam answers
EXPLAIN (ANALYZE, BUFFERS)
INSERT INTO exam_answers (exam_instance_id, question_id, selected_option_id, time_spent_seconds)
SELECT 
    'exam-instance-uuid',
    question_id,
    selected_option_id,
    time_spent_seconds
FROM UNNEST(ARRAY['q1-uuid', 'q2-uuid', 'q3-uuid']) AS question_id,
     UNNEST(ARRAY['opt1-uuid', 'opt2-uuid', 'opt3-uuid']) AS selected_option_id,
     UNNEST(ARRAY[30, 45, 60]) AS time_spent_seconds;

-- Expected: Fast insert with minimal index overhead
```

### 2. Load Testing Scenarios

#### Concurrent Exam Simulation
```sql
-- Simulate 1000 concurrent exam starts
CREATE OR REPLACE FUNCTION simulate_concurrent_exams(num_students INTEGER DEFAULT 1000)
RETURNS VOID AS $$
DECLARE
    i INTEGER;
    exam_id UUID := 'sample-exam-uuid';
    student_id UUID;
BEGIN
    FOR i IN 1..num_students LOOP
        -- Get random student
        SELECT id INTO student_id 
        FROM students 
        TABLESAMPLE SYSTEM(0.1) 
        LIMIT 1;
        
        -- Insert exam instance
        INSERT INTO exam_instances (exam_id, student_id, start_time, status)
        VALUES (exam_id, student_id, CURRENT_TIMESTAMP, 'IN_PROGRESS');
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

---

## Index Size and Storage Planning

### Estimated Index Sizes
```sql
-- Query to estimate index sizes
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size,
    pg_size_pretty(pg_total_relation_size(indexrelid)) AS total_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Total index size for the database
SELECT 
    pg_size_pretty(sum(pg_relation_size(indexrelid))) AS total_index_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';
```

### Storage Planning
```
Estimated Index Sizes (for 10,000 students, 500 exams):
- User indexes: ~50MB
- Academic structure indexes: ~20MB
- Question bank indexes: ~100MB
- Examination indexes: ~200MB (critical for performance)
- Security indexes: ~80MB
- Audit log indexes: ~150MB (grows with time)

Total estimated: ~600MB
Recommended storage: 2GB for indexes (including growth)
```

---

## Index Performance Metrics

### Key Performance Indicators

#### Index Hit Ratios
```sql
-- Monitor index hit ratios
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_scan > 0 THEN 
            ROUND((idx_tup_read::DECIMAL / idx_scan), 2)
        ELSE 0 
    END AS avg_tuples_per_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

#### Target Metrics
- **Index Hit Ratio:** > 95% for critical indexes
- **Avg Tuples per Scan:** < 10 for selective queries
- **Index Usage:** All indexes should have > 0 scans (except unused indexes)
- **Bloat:** < 20% for frequently updated indexes

### Performance Alerts
```sql
-- Function to check index performance
CREATE OR REPLACE FUNCTION check_index_performance()
RETURNS TABLE(issue_type TEXT, description TEXT, severity TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Unused Index'::TEXT,
        'Index ' || quote_ident(idx.indexname) || ' on table ' || 
        quote_ident(idx.tablename) || ' has never been used',
        'MEDIUM'::TEXT
    FROM pg_stat_user_indexes idx
    WHERE idx.idx_scan = 0 
    AND idx.schemaname = 'public'
    AND idx.indexname NOT LIKE '%_pkey';
    
    RETURN QUERY
    SELECT 
        'Low Hit Ratio'::TEXT,
        'Index ' || quote_ident(idx.indexname) || ' has low hit ratio: ' || 
        ROUND((idx.idx_tup_read::DECIMAL / NULLIF(idx.idx_scan, 0)), 2)::TEXT,
        'LOW'::TEXT
    FROM pg_stat_user_indexes idx
    WHERE idx.idx_scan > 0 
    AND idx.idx_tup_read::DECIMAL / idx.idx_scan < 5 
    AND idx.schemaname = 'public';
END;
$$ LANGUAGE plpgsql;
```

This comprehensive indexing strategy ensures optimal performance for the CBT system's most critical operations while maintaining data integrity and supporting the complex analytical requirements of an educational examination system.
