# CBT Project Operational Cadence

## Definition of Ready

A user story is "Ready" when it meets ALL of these criteria:

### Content Requirements
- **Clear Business Value:** The story delivers measurable value to students, lecturers, or administrators
- **Specific User Persona:** Target user is clearly identified (e.g., "100-level student", "GST lecturer", "exam invigilator")
- **Acceptance Criteria:** Written in BDD format (Given/When/Then) with at least 3 scenarios
- **Dependencies Identified:** All technical and business dependencies are documented
- **Effort Estimated:** Story points assigned based on team consensus

### Technical Requirements
- **Technical Feasibility:** Architecture team confirms technical viability
- **Security Review:** Security engineer has reviewed and approved approach
- **Performance Requirements:** Non-functional requirements are specified
- **Test Strategy:** QA engineer has defined test approach
- **UI/UX Validation:** Designer has reviewed user experience impact

### Governance Requirements
- **Stakeholder Approval:** Relevant stakeholders have reviewed and approved
- **Compliance Check:** Story complies with university policies and regulations
- **Risk Assessment:** Potential risks are identified and mitigation planned

## Definition of Done

A user story is "Done" when ALL of these criteria are met:

### Code Quality
- **Code Complete:** All code is written and compiles without errors
- **Code Review:** Peer-reviewed by at least one senior team member
- **Unit Tests:** Minimum 80% code coverage with meaningful tests
- **Integration Tests:** All API integrations are tested end-to-end
- **Static Analysis:** No critical security vulnerabilities or code quality issues

### User Experience
- **UI Implementation:** All UI components are implemented according to design specifications
- **Accessibility:** WCAG 2.1 AA compliance verified
- **Responsive Design:** Works across all supported devices and screen sizes
- **User Testing:** Usability tested with real users
- **Documentation:** User-facing documentation is complete

### Security & Compliance
- **Security Testing:** No critical or high-severity vulnerabilities
- **Data Protection:** All PII handling meets university policies
- **Audit Trail:** All actions are properly logged and auditable
- **Performance:** Meets defined performance benchmarks
- **Load Testing:** Handles expected concurrent user load

### Deployment Readiness
- **Environment Testing:** Successfully tested in staging environment
- **Database Migrations:** All database changes are versioned and reversible
- **Configuration:** All configuration settings are externalized
- **Monitoring:** Appropriate monitoring and alerting are in place
- **Rollback Plan:** Clear rollback procedure documented and tested

## Communication Protocols

### Daily Stand-ups (15 minutes)
**Time:** 9:00 AM - 9:15 AM
**Format:** Each team member answers:
1. What did I accomplish yesterday?
2. What will I work on today?
3. What blockers or risks do I face?

**Facilitator:** Project Manager
**Notes:** Action items tracked in Jira, blockers escalated immediately

### Bi-weekly Sprint Reviews
**Time:** Friday 2:00 PM - 3:00 PM
**Attendees:** Core team + Steering Committee representatives
**Agenda:**
1. Sprint goal achievement review
2. Demo of completed features
3. Metrics and KPI discussion
4. Stakeholder feedback collection
5. Next sprint priority alignment

### Bi-weekly Sprint Planning
**Time:** Monday 9:30 AM - 11:00 AM
**Attendees:** Core team
**Agenda:**
1. Review product backlog
2. Select stories for next sprint
3. Define sprint goal
4. Task breakdown and estimation
5. Identify and mitigate risks

### Retrospectives
**Time:** Friday 3:30 PM - 4:30 PM
**Format:** Start-Stop-Continue + Action Items
**Focus:** Process improvement, team dynamics, technical debt

## Incident Response SLA

### Critical Production Issues (During Exam Periods)
- **Response Time:** 15 minutes
- **Resolution Time:** 2 hours
- **Escalation:** Immediate to Executive Sponsor
- **Communication:** Real-time status updates to all stakeholders

### High Priority Issues
- **Response Time:** 1 hour
- **Resolution Time:** 8 hours
- **Escalation:** To Steering Committee
- **Communication:** Hourly status updates

### Medium Priority Issues
- **Response Time:** 4 hours
- **Resolution Time:** 24 hours
- **Escalation:** To Project Manager
- **Communication:** Daily status updates

### Low Priority Issues
- **Response Time:** 24 hours
- **Resolution Time:** 5 business days
- **Escalation:** Team lead discretion
- **Communication:** Weekly status updates

## Quality Gates

### Pre-commit Checks
- Code linting and formatting
- Basic unit tests pass
- No sensitive data committed
- Commit message follows standards

### Pre-merge Checks
- All tests pass (unit, integration, security)
- Code coverage ≥ 80%
- No new security vulnerabilities
- Performance benchmarks met
- Documentation updated

### Pre-deployment Checks
- Staging environment validation
- Database migration testing
- Configuration validation
- Rollback procedure verification
- Stakeholder sign-off received

## Risk Management

### Risk Categories
- **Technical:** Architecture decisions, technology choices, performance
- **Security:** Data breaches, vulnerabilities, compliance
- **Operational:** Team availability, resource constraints, timeline
- **Business:** Requirement changes, stakeholder alignment, adoption

### Risk Monitoring
- Weekly risk assessment reviews
- Risk register maintenance
- Mitigation plan tracking
- Escalation protocol for high-impact risks
