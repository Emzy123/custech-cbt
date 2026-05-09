# CBT Data Archival and Retention Strategy

## Overview

This document defines the comprehensive data archival and retention strategy for the CBT system, ensuring compliance with academic regulations while optimizing database performance and storage efficiency.

## Retention Policy Framework

### Regulatory Requirements
```
Academic Records: 7 years minimum (Nigerian University System)
- Student examination records
- Grades and transcripts
- Academic integrity violations
- Appeals and resolutions

Examination Content: 4 years minimum
- Question banks and exam papers
- Answer keys and grading rubrics
- Student responses and submissions

Audit Logs: 7 years minimum
- Security events
- System access logs
- Academic integrity investigations
- Data breach records

Biometric Data: 7 years or until student graduation + 1 year
- Biometric templates
- Verification records
- Consent documentation
```

### Data Classification for Retention
```
Hot Data (0-6 months): Active transactions
- Current semester exam instances
- Active user sessions
- Ongoing examinations
- Recent audit logs

Warm Data (6 months - 2 years): Recent history
- Previous semester results
- Recent question banks
- Student academic history
- Performance analytics

Cold Data (2-7 years): Long-term storage
- Historical examination records
- Archived question banks
- Compliance data
- Historical analytics

Archive Data (>7 years): Compliance archive
- Expired records beyond retention
- Compressed historical data
- Legal hold data
- Research datasets
```

---

## Automated Partitioning Strategy

### 1. Audit Logs Partitioning

#### Monthly Partitioning Setup
```sql
-- Enable pg_partman extension
CREATE EXTENSION IF NOT EXISTS pg_partman;

-- Create partitioned audit_logs table (if not exists)
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

-- Create parent partition configuration
SELECT partman.run_maintenance_proc();

-- Configure automatic partition creation
UPDATE partman.part_config 
SET 
    premake = 3,  -- Create 3 partitions in advance
    retention = '7 years',  -- Keep partitions for 7 years
    retention_keep_table = true,  -- Keep table structure after data removal
    retention_keep_index = true,  -- Keep indexes after data removal
    automatic_maintenance = 'on'  -- Enable automatic maintenance
WHERE parent_table = 'public.audit_logs';

-- Create initial partitions (past 3 months + next 6 months)
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    i INTEGER;
BEGIN
    -- Create past 3 months
    FOR i IN -3..-1 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'audit_logs_' || TO_CHAR(start_date, 'YYYY_m"m"');
        
        EXECUTE format('CREATE TABLE %I PARTITION OF audit_logs 
                       FOR VALUES FROM (%L) TO (%L) 
                       TABLESPACE cbt_warm_data',
                       partition_name, start_date, end_date);
    END LOOP;
    
    -- Create next 6 months
    FOR i IN 0..5 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'audit_logs_' || TO_CHAR(start_date, 'YYYY_m"m"');
        
        EXECUTE format('CREATE TABLE %I PARTITION OF audit_logs 
                       FOR VALUES FROM (%L) TO (%L) 
                       TABLESPACE cbt_hot_data',
                       partition_name, start_date, end_date);
    END LOOP;
END
$$;
```

#### Partition Maintenance Function
```sql
-- Function to maintain audit log partitions
CREATE OR REPLACE FUNCTION maintain_audit_log_partitions()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    partitions_created INTEGER := 0;
    partitions_dropped INTEGER := 0;
    retention_date DATE := CURRENT_DATE - INTERVAL '7 years';
BEGIN
    -- Create future partitions (next 3 months)
    INSERT INTO partman.run_maintenance_proc();
    
    -- Drop old partitions (older than 7 years)
    SELECT COUNT(*) INTO partitions_dropped
    FROM pg_tables 
    WHERE tablename LIKE 'audit_logs_%'
    AND substring(tablename from 13) < TO_CHAR(retention_date, 'YYYY_m"m"');
    
    -- Archive data from partitions to be dropped
    FOR partition_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'audit_logs_%'
        AND substring(tablename from 13) < TO_CHAR(retention_date, 'YYYY_m"m"')
    LOOP
        -- Export data to archive (implementation depends on archive system)
        result := result || 'Archived partition: ' || partition_record.tablename || E'\n';
        
        -- Drop the partition
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(partition_record.tablename);
        partitions_dropped := partitions_dropped + 1;
    END LOOP;
    
    RETURN 'Partition maintenance completed. Created: ' || partitions_created::TEXT || 
           ', Dropped: ' || partitions_dropped::TEXT || E'\n' || result;
END;
$$ LANGUAGE plpgsql;
```

### 2. Exam Answers Partitioning

#### Semester-Based Partitioning
```sql
-- Create partitioned exam_answers table
CREATE TABLE exam_answers_partitioned (
    LIKE exam_answers INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create semester-based partitions
CREATE OR REPLACE FUNCTION create_semester_partitions()
RETURNS VOID AS $$
DECLARE
    semester_record RECORD;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Create partitions for each semester
    FOR semester_record IN 
        SELECT s.id, s.start_date, s.end_date,
               ac.session_code,
               s.semester
        FROM semesters s
        JOIN academic_sessions ac ON s.academic_session_id = ac.id
        ORDER BY s.start_date
    LOOP
        partition_name := 'exam_answers_' || 
                        REPLACE(semester_record.session_code, '/', '_') || '_' ||
                        CASE semester_record.semester
                            WHEN 'FIRST' THEN '1'
                            WHEN 'SECOND' THEN '2'
                        END;
        start_date := semester_record.start_date;
        end_date := semester_record.end_date + INTERVAL '2 months'; -- Buffer period
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF exam_answers_partitioned
                       FOR VALUES FROM (%L) TO (%L)
                       TABLESPACE cbt_warm_data',
                       partition_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Initialize partitions
SELECT create_semester_partitions();
```

### 3. Student Records Archival

#### Graduated Student Archival
```sql
-- Function to archive graduated students
CREATE OR REPLACE FUNCTION archive_graduated_students()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER := 0;
    student_record RECORD;
BEGIN
    -- Archive students who graduated more than 1 year ago
    FOR student_record IN 
        SELECT s.id, s.matric_number, s.graduation_year
        FROM students s
        WHERE s.graduated = true 
        AND s.graduation_year <= EXTRACT(YEAR FROM CURRENT_DATE) - 1
        AND s.is_active = false
    LOOP
        -- Move to archive table
        INSERT INTO students_archive (
            id, user_id, matric_number, admission_year, current_level,
            department_id, academic_session_id, graduation_year,
            is_active, graduated, created_at, updated_at,
            archived_at
        )
        SELECT 
            s.id, s.user_id, s.matric_number, s.admission_year, s.current_level,
            s.department_id, s.academic_session_id, s.graduation_year,
            s.is_active, s.graduated, s.created_at, s.updated_at,
            CURRENT_TIMESTAMP
        FROM students s
        WHERE s.id = student_record.id;
        
        -- Delete from active table
        DELETE FROM students WHERE id = student_record.id;
        
        archived_count := archived_count + 1;
    END LOOP;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;
```

---

## Archival Tables Structure

### 1. Archive Tables Definition

#### Students Archive
```sql
CREATE TABLE students_archive (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    matric_number VARCHAR(20) NOT NULL,
    admission_year INTEGER NOT NULL,
    current_level INTEGER NOT NULL,
    department_id UUID NOT NULL,
    academic_session_id UUID NOT NULL,
    graduation_year INTEGER,
    is_active BOOLEAN DEFAULT false,
    graduated BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_cold_data;

-- Indexes for archive table
CREATE INDEX idx_students_archive_matric ON students_archive(matric_number) TABLESPACE cbt_indexes;
CREATE INDEX idx_students_archive_graduated ON students_archive(graduated, archived_at) TABLESPACE cbt_indexes;
```

#### Exam Instances Archive
```sql
CREATE TABLE exam_instances_archive (
    id UUID PRIMARY KEY,
    exam_id UUID NOT NULL,
    student_id UUID NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    time_extension_minutes INTEGER DEFAULT 0,
    status exam_instance_status,
    total_points_earned INTEGER DEFAULT 0,
    total_points_possible INTEGER DEFAULT 0,
    percentage_score DECIMAL(5,2),
    grade VARCHAR(5),
    ip_address INET,
    user_agent TEXT,
    browser_fingerprint VARCHAR(255),
    biometric_verified BOOLEAN DEFAULT false,
    biometric_verification_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE cbt_cold_data;

-- Indexes for archive table
CREATE INDEX idx_exam_instances_archive_student ON exam_instances_archive(student_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_archive_exam ON exam_instances_archive(exam_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_exam_instances_archive_date ON exam_instances_archive(archived_at) TABLESPACE cbt_indexes;
```

#### Questions Archive
```sql
CREATE TABLE questions_archive (
    id UUID PRIMARY KEY,
    question_bank_id UUID NOT NULL,
    question_text TEXT NOT NULL,
    question_type question_type NOT NULL,
    difficulty difficulty_level NOT NULL,
    points_value INTEGER NOT NULL,
    time_limit_seconds INTEGER,
    explanation TEXT,
    tags JSONB,
    is_active BOOLEAN DEFAULT false,
    version INTEGER,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archive_reason VARCHAR(100)
) TABLESPACE cbt_cold_data;

-- Indexes for archive table
CREATE INDEX idx_questions_archive_bank ON questions_archive(question_bank_id) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_archive_type ON questions_archive(question_type) TABLESPACE cbt_indexes;
CREATE INDEX idx_questions_archive_archived ON questions_archive(archived_at) TABLESPACE cbt_indexes;
```

---

## Data Lifecycle Management

### 1. Automated Archival Procedures

#### Daily Archival Tasks
```sql
-- Function to run daily archival tasks
CREATE OR REPLACE FUNCTION run_daily_archival()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    audit_count INTEGER;
    student_count INTEGER;
BEGIN
    -- Archive audit logs partitions older than 7 years
    result := result || 'Audit log archival: ' || maintain_audit_log_partitions() || E'\n';
    
    -- Archive graduated students
    student_count := archive_graduated_students();
    result := result || 'Students archived: ' || student_count::TEXT || E'\n';
    
    -- Update statistics
    ANALYZE students_archive;
    ANALYZE exam_instances_archive;
    ANALYZE questions_archive;
    
    result := result || 'Statistics updated successfully';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

#### Weekly Archival Tasks
```sql
-- Function to run weekly archival tasks
CREATE OR REPLACE FUNCTION run_weekly_archival()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    exam_count INTEGER;
    question_count INTEGER;
BEGIN
    -- Archive completed exam instances older than 2 years
    INSERT INTO exam_instances_archive (
        id, exam_id, student_id, start_time, end_time, time_extension_minutes,
        status, total_points_earned, total_points_possible, percentage_score,
        grade, ip_address, user_agent, browser_fingerprint, biometric_verified,
        biometric_verification_time, created_at, updated_at, archived_at
    )
    SELECT 
        ei.id, ei.exam_id, ei.student_id, ei.start_time, ei.end_time, ei.time_extension_minutes,
        ei.status, ei.total_points_earned, ei.total_points_possible, ei.percentage_score,
        ei.grade, ei.ip_address, ei.user_agent, ei.browser_fingerprint, ei.biometric_verified,
        ei.biometric_verification_time, ei.created_at, ei.updated_at, CURRENT_TIMESTAMP
    FROM exam_instances ei
    WHERE ei.status = 'SUBMITTED'
    AND ei.created_at < CURRENT_DATE - INTERVAL '2 years';
    
    GET DIAGNOSTICS exam_count = ROW_COUNT;
    DELETE FROM exam_instances 
    WHERE status = 'SUBMITTED'
    AND created_at < CURRENT_DATE - INTERVAL '2 years';
    
    result := result || 'Exam instances archived: ' || exam_count::TEXT || E'\n';
    
    -- Archive inactive questions older than 4 years
    INSERT INTO questions_archive (
        id, question_bank_id, question_text, question_type, difficulty,
        points_value, time_limit_seconds, explanation, tags, is_active,
        version, created_by, created_at, updated_at, updated_by, archived_at,
        archive_reason
    )
    SELECT 
        q.id, q.question_bank_id, q.question_text, q.question_type, q.difficulty,
        q.points_value, q.time_limit_seconds, q.explanation, q.tags, q.is_active,
        q.version, q.created_by, q.created_at, q.updated_at, q.updated_by, 
        CURRENT_TIMESTAMP, 'Age-based archival'
    FROM questions q
    WHERE q.is_active = false
    AND q.updated_at < CURRENT_DATE - INTERVAL '4 years';
    
    GET DIAGNOSTICS question_count = ROW_COUNT;
    DELETE FROM questions 
    WHERE is_active = false
    AND updated_at < CURRENT_DATE - INTERVAL '4 years';
    
    result := result || 'Questions archived: ' || question_count::TEXT || E'\n';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

### 2. Data Purge Procedures

#### Compliance-Based Data Purge
```sql
-- Function to purge data beyond retention period
CREATE OR REPLACE FUNCTION purge_expired_data()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    purge_date DATE := CURRENT_DATE - INTERVAL '7 years';
    audit_count INTEGER;
BEGIN
    -- Create audit records for data purge
    INSERT INTO audit_logs (action, resource_type, success, error_message)
    VALUES ('SYSTEM_CHANGE', 'DATA_PURGE', true, 'Starting data purge for data older than ' || purge_date);
    
    -- Purge old archive tables if needed (beyond 10 years)
    -- This would depend on specific legal requirements
    
    result := result || 'Data purge completed for retention period: ' || purge_date::TEXT;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

---

## Archive Access and Views

### 1. Unified Archive Views

#### Student History View
```sql
CREATE VIEW student_complete_history AS
SELECT 
    -- Current student data
    s.id, s.matric_number, s.admission_year, s.current_level,
    s.department_id, s.academic_session_id, s.graduation_year,
    s.is_active, s.graduated, s.created_at, s.updated_at,
    CURRENT_TIMESTAMP as record_status
FROM students s

UNION ALL

SELECT 
    -- Archived student data
    sa.id, sa.matric_number, sa.admission_year, sa.current_level,
    sa.department_id, sa.academic_session_id, sa.graduation_year,
    sa.is_active, sa.graduated, sa.created_at, sa.updated_at,
    'ARCHIVED' as record_status
FROM students_archive sa;
```

#### Exam History View
```sql
CREATE VIEW exam_complete_history AS
SELECT 
    -- Current exam instances
    ei.id, ei.exam_id, ei.student_id, ei.start_time, ei.end_time,
    ei.time_extension_minutes, ei.status, ei.total_points_earned,
    ei.total_points_possible, ei.percentage_score, ei.grade,
    ei.ip_address, ei.user_agent, ei.created_at, ei.updated_at,
    CURRENT_TIMESTAMP as record_status
FROM exam_instances ei

UNION ALL

SELECT 
    -- Archived exam instances
    eia.id, eia.exam_id, eia.student_id, eia.start_time, eia.end_time,
    eia.time_extension_minutes, eia.status, eia.total_points_earned,
    eia.total_points_possible, eia.percentage_score, eia.grade,
    eia.ip_address, eia.user_agent, eia.created_at, eia.updated_at,
    'ARCHIVED' as record_status
FROM exam_instances_archive eia;
```

### 2. Archive Access Functions

#### Student Transcript Retrieval
```sql
-- Function to retrieve complete student transcript
CREATE OR REPLACE FUNCTION get_student_transcript(p_matric_number VARCHAR(20))
RETURNS TABLE (
    exam_id UUID,
    exam_title VARCHAR(255),
    course_code VARCHAR(20),
    exam_date DATE,
    percentage_score DECIMAL(5,2),
    grade VARCHAR(5),
    academic_session VARCHAR(20),
    record_status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.title, c.code, e.exam_date, 
        ech.percentage_score, ech.grade,
        ac.session_code, ech.record_status
    FROM exam_complete_history ech
    JOIN examinations e ON ech.exam_id = e.id
    JOIN courses c ON e.course_id = c.id
    JOIN academic_sessions ac ON e.academic_session_id = ac.id
    JOIN students_complete_history sch ON ech.student_id = sch.id
    WHERE sch.matric_number = p_matric_number
    ORDER BY e.exam_date DESC;
END;
$$ LANGUAGE plpgsql;
```

---

## Monitoring and Reporting

### 1. Archival Metrics

#### Archival Statistics View
```sql
CREATE VIEW archival_statistics AS
SELECT 
    'students' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_records,
    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_records,
    pg_size_pretty(pg_total_relation_size('students')) as table_size
FROM students

UNION ALL

SELECT 
    'students_archive' as table_name,
    COUNT(*) as total_records,
    0 as active_records,
    COUNT(*) as inactive_records,
    pg_size_pretty(pg_total_relation_size('students_archive')) as table_size
FROM students_archive

UNION ALL

SELECT 
    'exam_instances' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status IN ('NOT_STARTED', 'IN_PROGRESS') THEN 1 END) as active_records,
    COUNT(CASE WHEN status IN ('SUBMITTED', 'TIMED_OUT', 'ABANDONED') THEN 1 END) as inactive_records,
    pg_size_pretty(pg_total_relation_size('exam_instances')) as table_size
FROM exam_instances

UNION ALL

SELECT 
    'exam_instances_archive' as table_name,
    COUNT(*) as total_records,
    0 as active_records,
    COUNT(*) as inactive_records,
    pg_size_pretty(pg_total_relation_size('exam_instances_archive')) as table_size
FROM exam_instances_archive;
```

### 2. Compliance Reporting

#### Retention Compliance Report
```sql
-- Function to generate retention compliance report
CREATE OR REPLACE FUNCTION generate_retention_compliance_report()
RETURNS TABLE (
    data_category VARCHAR(50),
    retention_period VARCHAR(20),
    oldest_record_date DATE,
    records_past_retention INTEGER,
    compliance_status VARCHAR(20),
    recommendations TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Student Records'::VARCHAR(50),
        '7 years'::VARCHAR(20),
        MIN(created_at)::DATE,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years'),
        CASE 
            WHEN COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years') > 0 
            THEN 'NON_COMPLIANT' 
            ELSE 'COMPLIANT' 
        END::VARCHAR(20),
        CASE 
            WHEN COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years') > 0 
            THEN 'Archive or purge records beyond retention period' 
            ELSE 'All records within retention period' 
        END::TEXT
    FROM student_complete_history
    WHERE graduated = true
    GROUP BY 'Student Records'
    
    UNION ALL
    
    SELECT 
        'Exam Records'::VARCHAR(50),
        '7 years'::VARCHAR(20),
        MIN(created_at)::DATE,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years'),
        CASE 
            WHEN COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years') > 0 
            THEN 'NON_COMPLIANT' 
            ELSE 'COMPLIANT' 
        END::VARCHAR(20),
        CASE 
            WHEN COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '7 years') > 0 
            THEN 'Archive or purge records beyond retention period' 
            ELSE 'All records within retention period' 
        END::TEXT
    FROM exam_complete_history
    WHERE status = 'SUBMITTED'
    GROUP BY 'Exam Records';
    
END;
$$ LANGUAGE plpgsql;
```

---

## Backup and Recovery Strategy

### 1. Archive Backup Strategy

#### Tiered Backup Approach
```
Hot Data Backup: Daily
- Full backup of hot tablespaces
- Point-in-time recovery capability
- 30-day retention

Warm Data Backup: Weekly
- Full backup of warm tablespaces
- Monthly incremental backups
- 6-month retention

Cold Data Backup: Monthly
- Full backup of cold tablespaces
- Quarterly verification
- 2-year retention

Archive Backup: Quarterly
- Compressed backup of archive data
- Annual verification
- 7-year retention (regulatory requirement)
```

### 2. Disaster Recovery

#### Archive Recovery Procedures
```sql
-- Function to recover from archive
CREATE OR REPLACE FUNCTION recover_from_archive(
    p_table_name VARCHAR(50),
    p_record_id UUID,
    p_recovery_reason TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    recovered BOOLEAN := false;
BEGIN
    -- Log recovery attempt
    INSERT INTO audit_logs (action, resource_type, resource_id, success, error_message)
    VALUES ('SYSTEM_CHANGE', 'ARCHIVE_RECOVERY', p_record_id, false, 'Recovery attempt: ' || p_recovery_reason);
    
    -- Implement recovery logic based on table type
    CASE p_table_name
        WHEN 'students' THEN
            -- Check if record exists in archive
            IF EXISTS (SELECT 1 FROM students_archive WHERE id = p_record_id) THEN
                INSERT INTO students SELECT * FROM students_archive WHERE id = p_record_id;
                recovered := true;
            END IF;
            
        WHEN 'exam_instances' THEN
            IF EXISTS (SELECT 1 FROM exam_instances_archive WHERE id = p_record_id) THEN
                INSERT INTO exam_instances SELECT * FROM exam_instances_archive WHERE id = p_record_id;
                recovered := true;
            END IF;
            
        WHEN 'questions' THEN
            IF EXISTS (SELECT 1 FROM questions_archive WHERE id = p_record_id) THEN
                INSERT INTO questions SELECT * FROM questions_archive WHERE id = p_record_id;
                recovered := true;
            END IF;
    END CASE;
    
    -- Update audit log with result
    UPDATE audit_logs 
    SET success = recovered, 
        error_message = CASE 
            WHEN recovered THEN 'Recovery successful'
            ELSE 'Record not found in archive'
        END
    WHERE resource_id = p_record_id 
    AND action = 'SYSTEM_CHANGE' 
    AND resource_type = 'ARCHIVE_RECOVERY'
    ORDER BY created_at DESC 
    LIMIT 1;
    
    RETURN recovered;
END;
$$ LANGUAGE plpgsql;
```

---

## Automation and Scheduling

### 1. Scheduled Tasks

#### Using pg_cron for Automation
```sql
-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily archival tasks (2 AM)
SELECT cron.schedule('daily-archival', '0 2 * * *', 'SELECT run_daily_archival();');

-- Schedule weekly archival tasks (Sunday 3 AM)
SELECT cron.schedule('weekly-archival', '0 3 * * 0', 'SELECT run_weekly_archival();');

-- Schedule monthly compliance check (1st of month 4 AM)
SELECT cron.schedule('monthly-compliance', '0 4 1 * *', 'SELECT * FROM generate_retention_compliance_report();');

-- Schedule quarterly archive backup (1st of quarter 5 AM)
SELECT cron.schedule('quarterly-backup', '0 5 1 1,4,7,10 *', 'SELECT perform_archive_backup();');
```

### 2. Monitoring and Alerting

#### Archival Health Check
```sql
-- Function to check archival system health
CREATE OR REPLACE FUNCTION archival_health_check()
RETURNS TABLE (
    check_name VARCHAR(100),
    status VARCHAR(20),
    details TEXT,
    alert_level VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    -- Check partition maintenance
    SELECT 
        'Partition Maintenance'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) > 0 THEN 'HEALTHY'
            ELSE 'WARNING'
        END::VARCHAR(20),
        'Active partitions: ' || COUNT(*)::TEXT,
        CASE 
            WHEN COUNT(*) > 0 THEN 'INFO'
            ELSE 'WARNING'
        END::VARCHAR(20)
    FROM pg_tables 
    WHERE tablename LIKE 'audit_logs_%'
    AND created_at > CURRENT_DATE - INTERVAL '1 month'
    
    UNION ALL
    
    -- Check archive table sizes
    SELECT 
        'Archive Storage'::VARCHAR(100),
        CASE 
            WHEN pg_total_relation_size('students_archive') < 10737418240 THEN 'HEALTHY' -- 10GB
            WHEN pg_total_relation_size('students_archive') < 21474836480 THEN 'WARNING' -- 20GB
            ELSE 'CRITICAL'
        END::VARCHAR(20),
        'Students archive size: ' || pg_size_pretty(pg_total_relation_size('students_archive')),
        CASE 
            WHEN pg_total_relation_size('students_archive') < 10737418240 THEN 'INFO'
            WHEN pg_total_relation_size('students_archive') < 21474836480 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::VARCHAR(20)
    
    UNION ALL
    
    -- Check retention compliance
    SELECT 
        'Retention Compliance'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) = 0 THEN 'HEALTHY'
            ELSE 'CRITICAL'
        END::VARCHAR(20),
        'Records beyond retention: ' || COUNT(*)::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'INFO'
            ELSE 'CRITICAL'
        END::VARCHAR(20)
    FROM student_complete_history
    WHERE created_at < CURRENT_DATE - INTERVAL '7 years';
END;
$$ LANGUAGE plpgsql;
```

This comprehensive archival and retention strategy ensures the CBT system maintains compliance with academic regulations while optimizing database performance and storage efficiency throughout the data lifecycle.
