# Contextual Inquiry and Accessibility Audit Framework

## Research Overview
**Objective:** Understand user behavior in natural contexts and ensure accessibility for all students
**Duration:** 2 weeks observation + 1 week analysis
**Participants:** Students with diverse abilities, disability support unit staff
**Method:** Ethnographic observation, contextual interviews, accessibility testing

---

## Part 1: Contextual Inquiry Protocol

### Observation Sessions at Existing CBT Institutions

#### Site Visit Preparation
**Pre-Visit Checklist:**
- [ ] Obtain permission from partner institution
- [ ] Prepare observation protocols and consent forms
- [ ] Schedule observation during actual exam periods
- [ ] Arrange observer positioning for minimal disruption
- [ ] Prepare video/audio recording equipment (with permission)

#### Observation Focus Areas

**Student Behavior Analysis:**
1. **Pre-Exam Anxiety Indicators**
   - Physical manifestations (finger tapping, leg shaking)
   - Verbal cues (nervous conversations, self-talk)
   - Preparation rituals (multiple logins, interface exploration)
   - Social dynamics (group vs. individual behavior)

2. **Interface Interaction Patterns**
   - Navigation strategies (linear vs. random question access)
   - Answer changing frequency and patterns
   - Time management behaviors (frequent time checking)
   - Help-seeking actions (asking invigilators, looking for instructions)

3. **Stress Response Behaviors**
   - Technical difficulty reactions (frustration, panic)
   - Time pressure responses (rushed answering, skipping)
   - Uncertainty handling (re-reading questions, second-guessing)
   - Completion behaviors (early submission vs. last-minute)

**Invigilator Observations:**
1. **Common Student Issues**
   - Technical problems and resolution time
   - Authentication difficulties
   - Interface confusion points
   - Accessibility accommodation requests

2. **Workflow Patterns**
   - Student check-in processes
   - Issue resolution procedures
   - Communication methods with students
   - Exam security monitoring

#### Data Collection Methods

**Structured Observation Template:**
```
Session ID: [Unique identifier]
Date/Time: [Observation period]
Location: [Venue details]
Number of Students: [Count]
Observer: [Name]

Student Behaviors Noted:
- [Behavior 1]: [Frequency], [Context], [Impact]
- [Behavior 2]: [Frequency], [Context], [Impact]

Technical Issues:
- [Issue 1]: [Number affected], [Resolution time], [Student reaction]
- [Issue 2]: [Number affected], [Resolution time], [Student reaction]

Interface Observations:
- [Screen/Element]: [User interaction], [Success rate], [Comments]

Environmental Factors:
- [Factor 1]: [Description], [Impact on students]
- [Factor 2]: [Description], [Impact on students]
```

**Interview Protocol for Post-Exam Debrief:**
1. "Walk me through your experience from when you first sat down until you submitted"
2. "What was the most stressful part of the exam for you?"
3. "What part of the computer interface was most confusing?"
4. "What would have made this experience less stressful?"
5. "Did you feel you had enough time? Why or why not?"
6. "What technical problems, if any, did you experience?"

### CUSTECH Campus Context Analysis

#### Computer Lab Environment Assessment
**Physical Environment:**
1. **Layout and Space**
   - Desk spacing and privacy
   - Lighting conditions and glare
   - Noise levels and distractions
   - Temperature and ventilation

2. **Equipment Assessment**
   - Computer specifications and age
   - Monitor sizes and resolution
   - Keyboard/mouse quality
   - Internet connection stability

3. **Accessibility Features**
   - Adjustable desk heights
   - Screen reader availability
   - Alternative input devices
   - Accessibility software installed

#### Network Infrastructure Context
**Connectivity Analysis:**
1. **Bandwidth Testing**
   - Speed tests during peak hours
   - Stability under load
   - Wireless vs. wired performance
   - Coverage across campus

2. **Device Access Patterns**
   - Student device ownership rates
   - Lab utilization patterns
   - Peak usage times
   - Device type distribution

---

## Part 2: Accessibility Audit Framework

### Disability Support Unit Consultation

#### Staff Interviews
**Key Personnel:**
- Disability Support Coordinator
- Accessibility Specialist
- Student Counselors
- Assistive Technology Technician

**Interview Topics:**
1. **Student Population Analysis**
   - Types of disabilities represented
   - Current accommodation methods
   - Success rates with current systems
   - Common barriers faced

2. **Technology Accommodations**
   - Screen reader usage and preferences
   - Alternative input device requirements
   - Visual accommodation needs
   - Cognitive accessibility considerations

3. **Process Integration**
   - Current accommodation request workflow
   - Documentation requirements
   - Testing and verification procedures
   - Emergency accommodation protocols

#### Student Accessibility Interviews

**Recruitment Strategy:**
- Partner with disability support unit
- Ensure diverse disability representation
- Provide appropriate compensation
- Guarantee confidentiality and accommodation

**Interview Protocol:**
1. **Technology Experience**
   - "What assistive technology do you currently use?"
   - "How comfortable are you with computers and technology?"
   - "What has been your experience with online testing before?"

2. **Accessibility Needs**
   - "What accommodations do you typically need for exams?"
   - "What barriers do you face with current computer systems?"
   - "What would make an online exam system accessible for you?"

3. **Ideal Experience**
   - "Describe your ideal accessible exam experience"
   - "What features would be most helpful for you?"
   - "How should the system adapt to different needs?"

### Technical Accessibility Assessment

#### WCAG 2.1 AA Compliance Audit
**Testing Framework:**

**1. Perceivable**
- **Text Alternatives:** All images have meaningful alt text
- **Captions and Transcripts:** Audio content has alternatives
- **Color and Contrast:** Meet 4.5:1 ratio for normal text
- **Resize and Reflow:** Content works at 200% zoom
- **Distinguishable:** Visual indicators not color-only

**2. Operable**
- **Keyboard Accessible:** All functions work with keyboard only
- **No Keyboard Traps:** Focus can be moved away from all elements
- **Timing Adjustable:** Users can control time limits
- **Motion and Animation:** Can be disabled or paused
- **Navigation:** Multiple ways to find content

**3. Understandable**
- **Readable:** Text is legible and understandable
- **Predictable:** Functionality is predictable
- **Input Assistance:** Error prevention and correction
- **Language Identification:** Page language is programmatically identified

**4. Robust**
- **Compatible:** Works with assistive technologies
- **Semantic Markup:** Proper HTML structure
- **ARIA Implementation:** Correct ARIA labels and roles
- **Error Handling:** Graceful degradation

#### Assistive Technology Testing
**Screen Reader Testing:**
1. **JAWS/NVDA/VoiceOver Compatibility**
   - Logical reading order
   - Meaningful link descriptions
   - Form field labeling
   - Table navigation
   - Dynamic content announcements

2. **Keyboard Navigation Testing**
   - Tab order logic
   - Focus indicators
   - Skip links functionality
   - Modal dialog handling
   - Form navigation

**Visual Accessibility Testing:**
1. **Color Blindness Simulation**
   - Deuteranopia, Protanopia, Tritanopia testing
   - Information not conveyed by color alone
   - Sufficient contrast ratios

2. **Low Vision Testing**
   - High contrast mode compatibility
   - Text scaling to 200%
   - Reflow maintenance
   - Magnifier compatibility

**Motor Accessibility Testing:**
1. **Alternative Input Testing**
   - Voice control compatibility
   - Switch device support
   - Head mouse functionality
   - Touch screen accessibility

2. **Fine Motor Considerations**
   - Large click targets (minimum 44x44 pixels)
   - No time-critical responses
   - Error prevention for accidental actions
   - Adjustable timing requirements

### Cognitive Accessibility Assessment

#### Cognitive Load Analysis
**Design Principles:**
1. **Simplicity and Clarity**
   - Clear, simple language
   - Consistent terminology
   - Minimal distractions
   - Progressive disclosure

2. **Memory Support**
   - Persistent information display
   - Clear progress indicators
   - Contextual help
   - Action confirmations

3. **Attention Management**
   - Focus on essential information
   - Minimal competing stimuli
   - Predictable layouts
   - Error recovery options

#### Testing with Cognitive Disabilities
**Participant Groups:**
- Students with ADHD
- Students with learning disabilities
- Students with anxiety disorders
- Students with executive function challenges

**Testing Scenarios:**
1. **Complex Task Navigation**
   - Multi-step processes
   - Information recall requirements
   - Decision-making under time pressure
   - Error recovery procedures

2. **Stress Testing**
   - Time pressure scenarios
   - Complex question formats
   - Technical failure simulation
   - Distraction resistance

---

## Part 3: Usability Testing Framework

### System Usability Scale (SUS) Implementation

#### SUS Questionnaire
**Standard 10-Question Survey:**
1. I think that I would like to use this system frequently
2. I found the system unnecessarily complex
3. I thought the system was easy to use
4. I think that I would need the support of a technical person to be able to use this system
5. I found the various functions in this system were well integrated
6. I thought there was too much inconsistency in this system
7. I would imagine that most people would learn to use this system very quickly
8. I found the system very cumbersome to use
9. I felt very confident using the system
10. I needed to learn a lot of things before I could get going with this system

**Scoring Interpretation:**
- 80-100: Excellent
- 68-80: Good
- 50-68: OK
- 20-50: Poor
- 0-20: Awful

#### Target Metrics
**Success Criteria:**
- Overall SUS score: ≥ 75 (Good)
- Students with disabilities: ≥ 70
- First-time users: ≥ 65
- Expert users: ≥ 80

### Task-Based Usability Testing

#### Core Task Scenarios
**Student Tasks:**
1. **Login and Dashboard Navigation**
   - Time to complete: < 2 minutes
   - Error rate: < 5%
   - Success rate: > 95%

2. **Exam Taking Workflow**
   - Time to understand interface: < 1 minute
   - Navigation efficiency: Direct path to completion
   - Error recovery: Successful recovery from common errors

3. **Result Viewing**
   - Time to locate results: < 30 seconds
   - Understanding of results: 90% comprehension rate
   - Help-seeking: Minimal assistance required

**Lecturer Tasks:**
1. **Question Creation**
   - Time to create basic question: < 3 minutes
   - Error rate: < 10%
   - Template usage: High adoption rate

2. **Exam Setup**
   - Time to configure basic exam: < 5 minutes
   - Understanding of options: 85% correct interpretation
   - Confidence in configuration: High

#### Performance Metrics
**Quantitative Measures:**
- Task completion rate
- Time on task
- Error frequency
- Help requests
- Click/interaction efficiency

**Qualitative Measures:**
- User satisfaction ratings
- Confidence levels
- Perceived difficulty
- Emotional response
- Recommendation likelihood

---

## Part 4: Accessibility Success Metrics

### Key Performance Indicators

#### Accessibility Compliance Metrics
1. **WCAG 2.1 AA Compliance**
   - Automated testing: 100% Level A and AA success criteria
   - Manual testing: 95% compliance rate
   - User testing: 90% success rate with assistive technology users

2. **Assistive Technology Compatibility**
   - Screen reader compatibility: 95% task completion rate
   - Keyboard navigation: 100% functionality access
   - Voice control: 80% core task completion

#### User Experience Metrics
1. **Disability User Satisfaction**
   - SUS score for users with disabilities: ≥ 70
   - Task completion rate: ≥ 85%
   - Help request frequency: ≤ 2 per session

2. **Cognitive Load Reduction**
   - Task completion time: Within 20% of non-disabled users
   - Error recovery time: < 30 seconds
   - Learning curve: < 15 minutes for basic tasks

### Monitoring and Continuous Improvement

#### Accessibility Testing Protocol
**Regular Testing Schedule:**
- **Automated Testing:** Weekly during development
- **Manual Testing:** Bi-weekly with accessibility experts
- **User Testing:** Monthly with disability users
- **Comprehensive Audit:** Quarterly

#### Issue Tracking and Resolution
**Accessibility Bug Classification:**
1. **Critical:** Blocks access for disability users
2. **High:** Significantly impacts usability
3. **Medium:** Creates workarounds or difficulties
4. **Low:** Minor inconvenience

**Resolution SLA:**
- Critical: 24 hours
- High: 72 hours
- Medium: 1 week
- Low: 2 weeks

---

## Part 5: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Conduct site visits to existing CBT institutions
- Perform contextual observations
- Interview disability support unit staff
- Establish testing protocols

### Phase 2: Assessment (Weeks 3-4)
- Conduct accessibility audits
- Perform user testing with diverse participants
- Complete WCAG compliance assessment
- Analyze contextual inquiry data

### Phase 3: Analysis (Week 5)
- Synthesize findings from all research
- Identify accessibility requirements
- Create user personas and journey maps
- Develop accessibility success metrics

### Phase 4: Integration (Week 6)
- Incorporate findings into design requirements
- Update SRS with accessibility specifications
- Create accessibility testing framework
- Establish continuous monitoring protocols

---

## Deliverables

### Research Documentation
1. **Contextual Inquiry Report**
   - Observation summaries and patterns
   - Student behavior analysis
   - Environmental impact assessment
   - Technical issue documentation

2. **Accessibility Audit Report**
   - WCAG compliance assessment
   - Assistive technology testing results
   - Disability user interview summaries
   - Accessibility gap analysis

3. **Usability Testing Report**
   - SUS score analysis
   - Task completion metrics
   - User satisfaction ratings
   - Performance benchmarking

### Design Requirements
1. **Accessibility Requirements Specification**
   - WCAG compliance requirements
   - Assistive technology compatibility
   - Cognitive accessibility considerations
   - Customization and adaptation features

2. **User Experience Guidelines**
   - Anxiety reduction strategies
   - Trust-building design elements
   - Error prevention and recovery
   - Help and support systems

### Implementation Framework
1. **Testing Protocols**
   - Accessibility testing procedures
   - User testing methodologies
   - Performance measurement tools
   - Continuous monitoring framework

2. **Success Metrics Dashboard**
   - KPI definitions and targets
   - Measurement frequency and methods
   - Reporting templates
   - Improvement tracking mechanisms
