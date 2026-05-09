# CBT Requirements Elicitation Plan

## Multi-Stakeholder Research Approach

### Student Requirements Research

#### Anonymous Survey Instrument
**Target Population:** 100-level students across all faculties
**Sample Size:** Minimum 200 students (20% of target population)
**Methodology:** Online anonymous survey with incentive participation

**Key Questions:**
1. **Current Exam Experience**
   - Rate your anxiety level during paper-based exams (1-10 scale)
   - What aspects of traditional exams cause you the most stress?
   - Have you experienced technical difficulties during previous CBT attempts?

2. **CBT-Specific Concerns**
   - "What is your biggest fear about taking exams on a computer?"
   - "What would make you trust an automated grading system?"
   - How confident are you with typing speed vs. handwriting speed?

3. **Accessibility & Device Needs**
   - Do you have access to a personal computer/laptop?
   - What devices do you feel comfortable using for exams?
   - Do you require any accessibility accommodations?

4. **Security & Fairness**
   - How important is it to see your questions randomized?
   - What would prevent you from cheating during a CBT?
   - How quickly do you expect to see your results?

#### Focus Group Protocol
**Group Size:** 6-8 students per session
**Number of Sessions:** 4 sessions (mixed by faculty)
**Duration:** 90 minutes per session

**Discussion Guide:**
1. Icebreaker: "Describe your best and worst exam experience"
2. Anxiety Exploration: Deep dive into specific fears and stressors
3. Technology Comfort: Assess digital literacy and device preferences
4. Trust Building: What creates confidence in automated systems
5. Ideal Experience: Vision of perfect CBT experience

### GST Lecturer Requirements Research

#### Workflow Mapping Interview
**Target:** All GST course coordinators and lecturers
**Method:** One-on-one 60-minute interviews + observation sessions

**Current Workflow Analysis:**
1. **Question Setting Phase**
   - How do you create questions currently?
   - What tools do you use for question banks?
   - How do you ensure question difficulty balance?

2. **Moderation Process**
   - Who reviews questions before exams?
   - What are the quality criteria?
   - How do you track question versions?

3. **Printing & Distribution**
   - What are the security concerns during printing?
   - How do you handle last-minute changes?
   - What are the logistics of paper distribution?

4. **Marking & Collation**
   - How long does marking typically take?
   - What are the challenges with handwriting?
   - How do you ensure marking consistency?

5. **Senate Submission**
   - What are the administrative requirements?
   - How do you handle grade appeals?
   - What reporting is needed?

#### Pain Point Identification
**Structured Questions:**
- "What takes the most time in your current process?"
- "Where do errors most frequently occur?"
- "What keeps you awake at night during exam periods?"
- "If you could change one thing, what would it be?"

### Examination Officers Requirements Research

#### Logistics Process Mapping
**Target:** Examination Officers from each faculty
**Method:** Process walkthrough + time measurement

**Key Process Areas:**
1. **Venue Allocation**
   - How do you currently assign exam venues?
   - What are the capacity constraints?
   - How do you handle special accommodations?

2. **Invigilator Scheduling**
   - What is the current invigilator-to-student ratio?
   - How do you train invigilators?
   - What are the common issues during exams?

3. **Attendance Tracking**
   - How do you currently track student attendance?
   - How do you handle late arrivals?
   - What are the procedures for exam misconduct?

4. **Material Distribution**
   - How long does it take to distribute papers?
   - What are the security protocols?
   - How do you handle emergency situations?

**Time Metrics Collection:**
- Seat number generation time per student
- Material distribution time per venue
- Attendance marking time per student
- Result collation time per course

### ICT Unit Infrastructure Assessment

#### Technical Infrastructure Audit
**Target:** ICT Director and technical team
**Method:** Technical assessment + capacity testing

**Hardware Inventory:**
- Server specifications and age
- Network switch capacity and configuration
- Backup power systems (UPS, generators)
- Computer lab specifications and availability

**Network Capacity Analysis:**
- Current bandwidth utilization patterns
- Peak usage times and bottlenecks
- Wireless coverage across campus
- Network security configurations

**Software & Systems:**
- Existing authentication systems
- Student information system integration points
- Current learning management systems
- Database infrastructure capacity

**Stress Testing Scenarios:**
- Concurrent user capacity testing
- Network load testing during peak hours
- Database performance under exam load
- Failover and recovery testing

## Requirements Documentation Framework

### Functional Requirements Categories
1. **User Management & Authentication**
2. **Question Bank Management**
3. **Exam Creation & Scheduling**
4. **Exam Delivery & Proctoring**
5. **Automated Grading & Results**
6. **Reporting & Analytics**
7. **System Administration**

### Non-Functional Requirements
1. **Security Requirements**
2. **Performance Requirements**
3. **Availability & Reliability**
4. **Scalability Requirements**
5. **Usability Requirements**
6. **Accessibility Requirements**
7. **Integration Requirements**

### Emotional Requirements
1. **Trust & Confidence**
2. **Anxiety Reduction**
3. **Fairness Perception**
4. **Transparency**
5. **Support & Help**

## Validation Process

### Requirements Review Cycle
1. **Initial Draft:** Based on elicitation findings
2. **Stakeholder Review:** Each stakeholder group validates their requirements
3. **Cross-Functional Review:** Identify conflicts and dependencies
4. **Prioritization:** MoSCoW analysis (Must, Should, Could, Won't)
5. **Final Sign-off:** Steering committee approval

### Acceptance Criteria Template
For each functional requirement:
```
Feature: [User Story Title]
  As a [user type]
  I want [functionality]
  So that [benefit]

  Scenario 1: [Happy path]
    Given [precondition]
    When [action]
    Then [expected outcome]

  Scenario 2: [Edge case]
    Given [precondition]
    When [action]
    Then [expected outcome]

  Scenario 3: [Error condition]
    Given [precondition]
    When [action]
    Then [expected outcome]
```

## Timeline & Resources

### Research Phase Schedule
- **Week 1:** Survey design and validation
- **Week 2:** Student survey deployment and focus groups
- **Week 3:** Lecturer interviews and workflow observation
- **Week 4:** Exam officer process mapping
- **Week 5:** ICT infrastructure assessment
- **Week 6:** Requirements analysis and documentation

### Required Resources
- **Research Team:** Project Manager + UX Designer + 1 Engineer
- **Tools:** Survey platform, recording devices, observation templates
- **Incentives:** Student participation vouchers, staff recognition
- **Access:** Time with stakeholders, system access for technical assessment
