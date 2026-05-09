# CBT System Software Requirements Specification

## Document Information
- **Version:** 1.0
- **Date:** April 2026
- **Author:** CBT Project Team
- **Status:** Draft for Review

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for the CUSTECH Computer-Based Testing (CBT) System. It serves as the foundation for system design, development, and testing.

### 1.2 Scope
The CBT system will replace paper-based examinations for GST courses at CUSTECH, providing:
- Secure online examination delivery
- Automated grading and result processing
- Comprehensive administration and reporting
- Accessibility compliance and user-friendly interface

### 1.3 Definitions
- **CBT:** Computer-Based Testing
- **GST:** General Studies
- **SRS:** Software Requirements Specification
- **BDD:** Behavior-Driven Development
- **PII:** Personally Identifiable Information

---

## 2. Functional Requirements

### 2.1 User Authentication and Access Control

#### REQ-AUTH-001: Student Login
**Priority:** Must Have

**Description:** Students must securely authenticate to access the CBT system using their institutional credentials.

**Acceptance Criteria:**
```
Scenario: Successful student login
  Given a registered student with valid credentials
  When they enter correct matric number and password
  Then they are granted access to the student dashboard
  And their login activity is logged

Scenario: Invalid credentials
  Given a registered student
  When they enter incorrect password 3 times
  Then their account is locked for 30 minutes
  And they receive an account locked notification

Scenario: First-time login
  Given a newly enrolled student
  When they first log into the system
  Then they are prompted to change their temporary password
  And they must accept the academic integrity policy
```

#### REQ-AUTH-002: Multi-Factor Authentication
**Priority:** Should Have

**Description:** Additional authentication layer for high-privilege users and exam periods.

**Acceptance Criteria:**
```
Scenario: Lecturer MFA setup
  Given a lecturer accessing administrative functions
  When they enable MFA
  Then they must register at least one authentication factor
  And backup codes are provided for account recovery

Scenario: Exam period MFA enforcement
  Given an exam in progress
  When any user attempts to access exam functions
  Then MFA is required regardless of user role
  And failed MFA attempts trigger security alerts
```

### 2.2 Question Bank Management

#### REQ-QBANK-001: Question Creation
**Priority:** Must Have

**Description:** Lecturers can create, edit, and organize examination questions in a centralized question bank.

**Acceptance Criteria:**
```
Scenario: Creating multiple choice questions
  Given a logged-in lecturer with question creation permissions
  When they create a new multiple choice question
  Then they can specify question text, options, and correct answer
  And they can assign difficulty level and topic tags
  And the question is saved with version control

Scenario: Question validation
  Given a lecturer submitting a new question
  When the question has missing required fields
  Then the system displays validation errors
  And the question cannot be saved until all fields are complete

Scenario: Question versioning
  Given an existing question being edited
  When changes are saved
  Then a new version is created
  And the previous version remains archived
  And the change history is tracked with user attribution
```

#### REQ-QBANK-002: Question Import/Export
**Priority:** Should Have

**Description:** Support for bulk question operations through standard file formats.

**Acceptance Criteria:**
```
Scenario: Bulk question import
  Given a lecturer with a valid question file
  When they upload the file for import
  Then the system validates the file format
  And successfully imports valid questions
  And reports any import errors with line numbers

Scenario: Question export
  Given a lecturer selecting questions for export
  When they choose export format and confirm
  Then the system generates a downloadable file
  And the file contains all selected questions with metadata
  And the export is logged for audit purposes
```

### 2.3 Examination Management

#### REQ-EXAM-001: Exam Creation
**Priority:** Must Have

**Description:** Lecturers can create examinations by selecting questions from the question bank and configuring exam parameters.

**Acceptance Criteria:**
```
Scenario: Creating a new examination
  Given a lecturer with exam creation permissions
  When they create a new exam
  Then they can set exam title, duration, and availability window
  And they can select questions by topic, difficulty, or randomization
  And they can configure question randomization per student
  And the exam is saved in draft status

Scenario: Exam configuration validation
  Given a lecturer configuring exam settings
  When they set invalid parameters (negative duration, past dates)
  Then the system displays validation errors
  And prevents exam creation until corrections are made

Scenario: Question randomization
  Given an exam with randomization enabled
  When students take the exam
  Then each student receives questions in random order
  And multiple choice options are randomized per question
  And the randomization pattern is recorded for grading
```

#### REQ-EXAM-002: Exam Scheduling
**Priority:** Must Have

**Description:** Examinations can be scheduled for specific time windows with automatic availability management.

**Acceptance Criteria:**
```
Scenario: Scheduling exam availability
  Given a lecturer creating an exam
  When they set start and end times
  Then the exam becomes available exactly at start time
  And the exam becomes unavailable exactly at end time
  And students receive countdown notifications

Scenario: Exam extension
  Given an exam in progress
  When technical issues require time extension
  Then authorized staff can extend the exam duration
  And affected students receive notification of extension
  And the original end time is logged for audit
```

### 2.4 Exam Delivery

#### REQ-DELIVERY-001: Secure Exam Interface
**Priority:** Must Have

**Description:** Students can take examinations through a secure, distraction-free interface.

**Acceptance Criteria:**
```
Scenario: Starting an exam
  Given a student with scheduled exam access
  When they click "Start Exam"
  Then they must accept the exam integrity pledge
  And the exam interface opens in secure mode
  And the timer starts counting down
  And questions are displayed according to randomization

Scenario: Navigation during exam
  Given a student taking an exam
  When they navigate between questions
  Then answered questions are marked as complete
  And they can review and change answers before submission
  And the timer continues running during navigation

Scenario: Exam submission
  Given a student completing an exam
  When they click "Submit Exam"
  Then they see a confirmation dialog with unanswered question warnings
  And upon confirmation, answers are securely transmitted
  And the exam session is terminated
  And they receive submission confirmation
```

#### REQ-DELIVERY-002: Time Management
**Priority:** Must Have

**Description:** Real-time timer management with automatic submission and time warnings.

**Acceptance Criteria:**
```
Scenario: Timer warnings
  Given a student taking an exam with 60-minute duration
  When 30 minutes remain
  Then a yellow warning appears
  When 10 minutes remain
  Then an orange warning appears
  When 5 minutes remain
  Then a red warning appears
  And warnings are non-intrusive but noticeable

Scenario: Automatic submission
  Given a student taking an exam
  When the timer reaches zero
  Then all current answers are automatically submitted
  And the exam session is terminated
  And the student receives automatic submission notification
```

### 2.5 Automated Grading

#### REQ-GRADING-001: Objective Question Grading
**Priority:** Must Have

**Description:** Automatic grading for objective question types with immediate result calculation.

**Acceptance Criteria:**
```
Scenario: Multiple choice grading
  Given a completed multiple choice question
  When the grading system processes the answer
  Then the answer is compared against the correct answer
  And full points are awarded for correct answers
  And zero points are awarded for incorrect answers
  And the result is recorded immediately

Scenario: True/False grading
  Given a completed true/false question
  When the grading system processes the answer
  Then the boolean response is validated
  And appropriate points are awarded based on correctness
  And partial points are not awarded for this question type
```

#### REQ-GRADING-002: Subjective Question Grading
**Priority:** Should Have

**Description:** Support for lecturer grading of subjective questions with rubric-based evaluation.

**Acceptance Criteria:**
```
Scenario: Essay question grading
  Given a completed essay question
  When a lecturer accesses the grading interface
  Then they can view the student's response
  And they can apply a grading rubric
  And they can provide feedback comments
  And the score is calculated based on rubric criteria

Scenario: Grading consistency
  Given multiple graders for the same question
  When grading is completed
  Then the system flags score variations above 20%
  And a moderation workflow is initiated
  And final grades require consensus or senior approval
```

### 2.6 Results and Reporting

#### REQ-RESULTS-001: Result Processing
**Priority:** Must Have

**Description:** Automated result compilation and distribution according to university policies.

**Acceptance Criteria:**
```
Scenario: Immediate result availability
  Given a student completing an exam with objective questions only
  When the grading is complete
  Then the student can view their results immediately
  And they see total score and per-question breakdown
  And they can review their submitted answers

Scenario: Delayed result release
  Given an exam with subjective questions
  When all grading is complete
  Then results are released according to configured release schedule
  And students receive notification of result availability
  And lecturers can review results before student release
```

#### REQ-RESULTS-002: Grade Reporting
**Priority:** Must Have

**Description:** Comprehensive reporting for lecturers, administrators, and university compliance.

**Acceptance Criteria:**
```
Scenario: Lecturer grade report
  Given a lecturer accessing exam results
  When they generate a grade report
  Then the report includes individual student scores
  And question-level statistics
  And class performance analytics
  And the report is exportable in multiple formats

Scenario: Senate submission report
  Given an administrator generating official reports
  When they create a Senate submission report
  Then the report meets university formatting requirements
  And includes all required statistical data
  And is digitally signed for authenticity
```

### 2.7 System Administration

#### REQ-ADMIN-001: User Management
**Priority:** Must Have

**Description:** Administrative functions for user account management and role assignment.

**Acceptance Criteria:**
```
Scenario: Student account creation
  Given an administrator with user management permissions
  When they create a new student account
  Then they can assign matric number and initial password
  And the account is linked to the student information system
  And the student receives account activation notification

Scenario: Role assignment
  Given an administrator managing user permissions
  When they assign roles to users
  Then permissions are granted immediately upon save
  And the user must re-authenticate to activate new permissions
  And all role changes are logged for audit
```

---

## 3. Non-Functional Requirements

### 3.1 Security Requirements

#### REQ-SEC-001: Authentication Security
**Priority:** Must Have

**Description:** Robust authentication mechanisms with protection against common attacks.

**Acceptance Criteria:**
```
Scenario: Password policy enforcement
  Given a user setting or changing password
  When they enter a weak password
  Then the system rejects passwords not meeting complexity requirements
  And provides specific feedback on password requirements
  And prevents common dictionary words and patterns

Scenario: Session security
  Given a logged-in user
  When their session is inactive for 15 minutes
  Then they are automatically logged out
  And must re-authenticate to continue
  And session tokens are invalidated on logout
```

#### REQ-SEC-002: Data Protection
**Priority:** Must Have

**Description:** Encryption and protection of sensitive data at rest and in transit.

**Acceptance Criteria:**
```
Scenario: Data transmission encryption
  Given any data transmission between client and server
  When the transmission occurs
  Then all data is encrypted using TLS 1.3 or higher
  And certificate validation is enforced
  And insecure connections are rejected

Scenario: Data storage encryption
  Given sensitive data stored in the database
  When the data is at rest
  Then PII is encrypted using AES-256 encryption
  And encryption keys are managed securely
  And data access requires proper authentication
```

### 3.2 Performance Requirements

#### REQ-PERF-001: Response Time
**Priority:** Must Have

**Description:** System response times for all user interactions.

**Acceptance Criteria:**
```
Scenario: Page load performance
  Given a user requesting any system page
  When the request is processed
  Then the page loads within 3 seconds under normal load
  And within 5 seconds under peak load (1000 concurrent users)
  And critical functions (exam submission) load within 2 seconds

Scenario: Database query performance
  Given any database operation
  When the query is executed
  Then 95% of queries complete within 500ms
  And no query takes longer than 5 seconds
  And slow queries are logged for optimization
```

#### REQ-PERF-002: Concurrent User Support
**Priority:** Must Have

**Description:** System capacity to support simultaneous examination sessions.

**Acceptance Criteria:**
```
Scenario: Peak load handling
  Given 2000 concurrent users taking exams
  When the system is under peak load
  Then all users maintain stable connections
  And response times remain within acceptable limits
  And no users experience session disconnection
  And system resources remain below 80% utilization
```

### 3.3 Availability Requirements

#### REQ-AVAIL-001: System Uptime
**Priority:** Must Have

**Description:** High availability during critical examination periods.

**Acceptance Criteria:**
```
Scenario: Exam period availability
  Given scheduled examination periods
  When the system is monitored
  Then uptime is maintained at 99.9% or higher
  And planned maintenance is scheduled outside exam periods
  And automatic failover occurs within 30 seconds
  And degraded performance alerts are generated immediately
```

### 3.4 Usability Requirements

#### REQ-USE-001: User Interface Standards
**Priority:** Should Have

**Description:** Intuitive, accessible user interface following modern design principles.

**Acceptance Criteria:**
```
Scenario: Interface consistency
  Given any user navigating the system
  When they interact with different screens
  Then all elements follow consistent design patterns
  And navigation is intuitive without training
  And help is contextually available
  And response to user actions is immediate

Scenario: Accessibility compliance
  Given users with disabilities
  When they access the system
  Then the interface meets WCAG 2.1 AA standards
  And screen readers can navigate all functions
  And keyboard-only navigation is supported
  And color contrast meets accessibility guidelines
```

---

## 4. Emotional Requirements

### 4.1 Trust and Confidence

#### REQ-TRUST-001: System Transparency
**Priority:** Should Have

**Description:** Build user trust through transparent processes and clear communication.

**Acceptance Criteria:**
```
Scenario: Grading transparency
  Given a student viewing their results
  When they access the result details
  Then they can see how each answer was graded
  And the grading rubric is clearly explained
  And any automated grading decisions are justified
  And they have a clear path for grade appeals

Scenario: System status communication
  Given any system maintenance or issues
  When users access the system
  Then they see clear status notifications
  And estimated resolution times are provided
  And alternative arrangements are communicated
```

### 4.2 Anxiety Reduction

#### REQ-ANXIETY-001: Stress-Free Interface
**Priority:** Should Have

**Description:** Design elements that reduce examination anxiety and stress.

**Acceptance Criteria:**
```
Scenario: Calming interface design
  Given a student taking an exam
  When they interact with the exam interface
  Then colors are calming and professional
  And time remaining is clearly but non-threateningly displayed
  And progress indicators show achievement rather than deficit
  And emergency help is easily accessible

Scenario: Error prevention
  Given a student interacting with the system
  When they make potentially destructive actions
  Then the system provides clear warnings
  And actions are reversible where possible
  And confirmation dialogs prevent accidental submissions
```

---

## 5. Integration Requirements

### 5.1 Student Information System Integration

#### REQ-INT-001: Student Data Synchronization
**Priority:** Must Have

**Description:** Real-time synchronization with the university's student information system.

**Acceptance Criteria:**
```
Scenario: Student enrollment sync
  Given new student enrollment in the SIS
  When the synchronization process runs
  Then the student account is automatically created in CBT
  And course enrollments are updated
  And any conflicts are flagged for manual resolution

Scenario: Grade transfer
  Given completed exam grading
  When grades are finalized
  Then grades are automatically transferred to SIS
  And grade format meets SIS requirements
  And transfer confirmation is logged
```

---

## 6. Compliance Requirements

### 6.1 Data Privacy Compliance

#### REQ-COMPL-001: Data Protection
**Priority:** Must Have

**Description:** Compliance with data protection regulations and university policies.

**Acceptance Criteria:**
```
Scenario: Data retention policy
  Given student examination data
  When the retention period expires
  Then data is automatically archived or deleted
  And the process follows university retention policies
  And deletion certificates are generated

Scenario: Right to access
  Given a student requesting their data
  When they submit a data access request
  Then their personal data is provided within legal timeframes
  And the data format is readable and complete
  And the request is logged for compliance auditing
```

---

## 7. Requirements Prioritization Matrix

| Requirement ID | Priority | User Impact | Technical Complexity | Risk Level |
|---------------|----------|-------------|---------------------|------------|
| REQ-AUTH-001 | Must | High | Medium | Low |
| AUTH-002 | Should | Medium | High | Medium |
| QBANK-001 | Must | High | Medium | Low |
| QBANK-002 | Should | Medium | Medium | Low |
| EXAM-001 | Must | High | High | Medium |
| EXAM-002 | Must | High | Medium | Low |
| DELIVERY-001 | Must | High | High | High |
| DELIVERY-002 | Must | High | Medium | Medium |
| GRADING-001 | Must | High | Medium | Low |
| GRADING-002 | Should | Medium | High | Medium |
| RESULTS-001 | Must | High | Medium | Low |
| RESULTS-002 | Must | Medium | Medium | Low |
| ADMIN-001 | Must | Medium | Low | Low |

---

## 8. Assumptions and Constraints

### 8.1 Assumptions
- University's student information system provides API access
- Network infrastructure can support required concurrent users
- Students have basic computer literacy
- Lecturers will receive adequate training
- Exam venues have reliable power and internet connectivity

### 8.2 Constraints
- System must comply with university IT security policies
- Budget limitations require cost-effective solutions
- Implementation timeline cannot exceed academic calendar
- Must integrate with existing university systems
- Limited internet bandwidth in some campus areas

---

## 9. Success Criteria

### 9.1 Technical Success Metrics
- System availability > 99.9% during exam periods
- Response time < 3 seconds for all functions
- Support for 2000 concurrent users
- Zero critical security vulnerabilities
- 100% automated grading for objective questions

### 9.2 User Success Metrics
- Student satisfaction score > 80%
- Lecturer adoption rate > 90%
- System Usability Scale (SUS) score > 75
- Training completion rate > 95%
- Support ticket reduction > 50% compared to paper exams

### 9.3 Business Success Metrics
- Exam processing time reduction > 75%
- Administrative overhead reduction > 60%
- Grade turnaround time < 24 hours for objective exams
- Cost per exam reduction > 40%
- Zero examination irregularities due to system issues
