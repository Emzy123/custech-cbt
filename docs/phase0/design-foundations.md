# CBT Design Foundations

## Design Philosophy

### Core Design Principles
1. **Trust Through Transparency:** Every interface element should build confidence and reduce anxiety
2. **Calm Under Pressure:** Design elements that remain functional and reassuring during stressful exam situations
3. **Universal Accessibility:** Design that works for all users regardless of ability, device, or context
4. **Institutional Pride:** Visual identity that reflects CUSTECH's academic excellence and values

---

## Visual Design System

### Color Palette

#### Primary Colors (Trust & Professionalism)
```
Primary Blue: #1E3A8A (Deep Trust Blue)
- Usage: Primary buttons, headers, important actions
- Psychology: Conveys trust, stability, and academic authority
- Accessibility: WCAG AAA compliant with white text

Secondary Blue: #3B82F6 (Confidence Blue)
- Usage: Secondary actions, links, interactive elements
- Psychology: Friendly, approachable, reliable
- Accessibility: WCAG AA compliant with white text

Accent Blue: #60A5FA (Calm Sky Blue)
- Usage: Background elements, subtle highlights
- Psychology: Calm, open, peaceful
- Accessibility: Decorative use only
```

#### Supporting Colors (Calm & Focus)
```
Sage Green: #059669 (Academic Green)
- Usage: Success states, progress indicators, confirmations
- Psychology: Growth, harmony, correctness
- Accessibility: WCAG AA compliant with white text

Neutral Gray: #6B7280 (Professional Gray)
- Usage: Secondary text, borders, inactive elements
- Psychology: Neutral, professional, unobtrusive
- Accessibility: WCAG AA compliant with white text
```

#### Alert Colors (Clear & Action-Oriented)
```
Warning Amber: #F59E0B (Attention Amber)
- Usage: Time warnings, caution messages
- Psychology: Alert but not alarming
- Accessibility: WCAG AA compliant with dark text

Error Red: #DC2626 (Critical Red)
- Usage: Errors, final submission warnings, critical alerts
- Psychology: Urgency, importance, stop action
- Accessibility: WCAG AA compliant with white text
- Usage Rule: Reserved ONLY for irreversible actions
```

#### Background Colors
```
Primary Background: #FFFFFF (Pure White)
- Usage: Main content areas, exam interface
- Psychology: Clean, focused, distraction-free

Secondary Background: #F9FAFB (Soft Gray)
- Usage: Sidebars, panels, non-content areas
- Psychology: Subtle, professional, easy on eyes

Tertiary Background: #F3F4F6 (Warm Gray)
- Usage: Cards, sections, content grouping
- Psychology: Structured, organized, clear hierarchy
```

### Typography System

#### Font Families
```
Primary Font: Inter (Modern Sans-serif)
- Usage: UI elements, buttons, navigation, labels
- Characteristics: High readability, screen-optimized, professional
- Weights: 400 (Regular), 500 (Medium), 600 (Semi-bold), 700 (Bold)

Secondary Font: Lora (Serif)
- Usage: Long question passages, reading content
- Characteristics: Excellent readability for long text, academic feel
- Weights: 400 (Regular), 500 (Medium), 600 (Semi-bold)

Monospace Font: JetBrains Mono
- Usage: Code snippets, technical content, special characters
- Characteristics: Clear character distinction, technical precision
- Weights: 400 (Regular)
```

#### Type Scale
```
Display Sizes (Headings)
H1: 2.5rem (40px) - 48px line height - 600 weight
- Usage: Page titles, exam titles
H2: 2rem (32px) - 40px line height - 600 weight
- Usage: Section headers, main navigation
H3: 1.5rem (24px) - 32px line height - 600 weight
- Usage: Subsection headers, card titles
H4: 1.25rem (20px) - 28px line height - 500 weight
- Usage: Question titles, form section headers

Body Text
Body Large: 1.125rem (18px) - 28px line height - 400 weight
- Usage: Question text, important content
Body Regular: 1rem (16px) - 24px line height - 400 weight
- Usage: General content, descriptions
Body Small: 0.875rem (14px) - 20px line height - 400 weight
- Usage: Labels, captions, help text

UI Elements
Button Text: 1rem (16px) - 24px line height - 500 weight
Label Text: 0.875rem (14px) - 20px line height - 500 weight
Input Text: 1rem (16px) - 24px line height - 400 weight
```

#### Typography Rules
1. **Minimum Readability:** No text smaller than 14px for content, 16px for body text
2. **Line Height:** 1.5x for body text, 1.2x for headings
3. **Font Weight:** Minimum 500 weight for interactive elements
4. **Contrast:** All text meets WCAG AA contrast ratios (4.5:1 minimum)

### Spacing System

#### Base Grid: 8px
```
Spacing Scale (in rem)
xs: 0.25rem (4px) - Micro spacing, borders
sm: 0.5rem (8px) - Small gaps, icon spacing
md: 1rem (16px) - Standard spacing, padding
lg: 1.5rem (24px) - Section spacing, large padding
xl: 2rem (32px) - Component separation
2xl: 3rem (48px) - Page sections
3xl: 4rem (64px) - Major page divisions
```

#### Component Spacing
```
Button Padding: 0.75rem 1.5rem (12px 24px)
Card Padding: 1.5rem (24px)
Form Field Spacing: 1rem (16px)
List Item Spacing: 0.75rem (12px)
Navigation Item Spacing: 1rem (16px)
```

---

## Component Information Architecture

### Atomic Components

#### Question Card
```
Purpose: Container for individual examination questions
States: Default, Active, Answered, Flagged, Review

Structure:
├── Question Header
│   ├── Question Number
│   ├── Question Type Badge
│   ├── Points Value
│   └── Flag Button
├── Question Content
│   ├── Question Text (Lora font)
│   ├── Media (images, diagrams)
│   └── Special Instructions
├── Answer Options
│   ├── Option A
│   ├── Option B
│   ├── Option C
│   └── Option D
└── Question Footer
    ├── Answer Status
    ├── Review Button
    └── Help Button
```

#### Timer Widget
```
Purpose: Display remaining exam time with appropriate urgency
States: Normal, Warning, Critical, Expired

Structure:
├── Timer Icon
├── Time Display (MM:SS)
├── Progress Ring (visual countdown)
└── Status Message

Behavior Rules:
- Green: > 30 minutes remaining
- Yellow: 30-10 minutes remaining
- Orange: 10-5 minutes remaining
- Red: < 5 minutes remaining
- Pulsing red: < 2 minutes remaining
```

#### Confirmation Modal
```
Purpose: Prevent accidental irreversible actions
States: Warning, Information, Error

Structure:
├── Modal Overlay
├── Modal Container
│   ├── Icon (appropriate to type)
│   ├── Title (clear, action-oriented)
│   ├── Message (specific consequences)
│   ├── Action Buttons
│   │   ├── Primary (confirm action)
│   │   └── Secondary (cancel)
│   └── Checkbox (acknowledgment if required)

Behavior Rules:
- Requires explicit user action to dismiss
- Focus remains trapped until decision
- Escape key cancels (safe default)
- Click outside cancels (safe default)
```

### Molecular Components

#### Exam Navigation Panel
```
Purpose: Allow students to navigate between questions efficiently

Structure:
├── Overview Header
│   ├── Progress Summary
│   └── Time Remaining
├── Question Grid
│   ├── Question Numbers (1-50)
│   ├── Status Indicators
│   │   ├── Unanswered (gray)
│   │   ├── Answered (green)
│   │   ├── Flagged (amber)
│   │   └── Current (blue outline)
│   └── Jump-to-Question functionality
└── Action Buttons
    ├── Previous Question
    ├── Next Question
    └── Submit Exam
```

#### Answer Feedback Component
```
Purpose: Provide immediate, clear feedback on answer actions

Structure:
├── Status Icon
├── Message Text
├── Action Suggestion
└── Dismiss Option

Types:
- Success: "Answer saved successfully"
- Error: "Please select an answer"
- Warning: "You have unanswered questions"
- Info: "You can change your answer before submission"
```

### Organism Components

#### Exam Interface
```
Purpose: Complete examination environment

Layout Structure:
┌─────────────────────────────────────────────────────┐
│ Header Bar                                          │
│ ├── Logo │ Exam Title │ Timer │ Help │ Exit         │
├─────────────────────────────────────────────────────┤
│ Main Content Area                                   │
│ ┌─────────────┐ ┌─────────────────────────────────┐ │
│ │ Navigation │ │ Question Card                   │ │
│ │ Panel      │ │                                 │ │
│ │             │ │ [Question Content]              │ │
│ │             │ │ [Answer Options]                │ │
│ │             │ │                                 │ │
│ │             │ └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
│ Footer Bar                                          │
│ ├── Progress Bar │ Previous │ Next │ Submit Exam    │
└─────────────────────────────────────────────────────┘
```

#### Dashboard Interface
```
Purpose: Student and lecturer home base

Structure:
├── Welcome Header
│   ├── User Profile
│   ├── Quick Stats
│   └── Notifications
├── Main Navigation
│   ├── Dashboard
│   ├── Exams
│   ├── Results
│   ├── Profile
│   └── Help
├── Content Area
│   ├── Upcoming Exams
│   ├── Recent Results
│   ├── Announcements
│   └── Quick Actions
└── Support Footer
    ├── Help Center
    ├── Contact Support
    └── System Status
```

---

## Interaction Design Patterns

### Micro-interactions

#### Button States
```
Default: Primary color, solid fill
Hover: Slightly darker shade, subtle shadow
Active: Darker shade, pressed appearance
Disabled: Muted color, reduced opacity
Loading: Spinner icon, disabled state
```

#### Form Field Interactions
```
Empty: Border gray, placeholder text
Focus: Border blue, blue glow, label rises
Filled: Border green, checkmark appears
Error: Border red, error message below
Disabled: Gray background, reduced contrast
```

#### Question Selection
```
Hover: Subtle highlight, cursor pointer
Selected: Blue background, checkmark appears
Flagged: Amber flag icon appears
Reviewed: Green checkmark overlay
```

### Animation Principles

#### Timing and Duration
```
Fast: 150ms - Immediate feedback
Standard: 250ms - UI transitions
Slow: 350ms - Complex animations
Very Slow: 500ms - Major state changes
```

#### Easing Functions
```
Ease Out: Natural deceleration (most common)
Ease In Out: Smooth acceleration and deceleration
Ease Out Back: Subtle overshoot for emphasis
Linear: Constant speed (loading animations only)
```

#### Animation Rules
1. **Purposeful:** Every animation serves a functional purpose
2. **Subtle:** Never distract from exam focus
3. **Fast:** Respect user time and attention
4. **Accessible:** Respect prefers-reduced-motion settings

---

## Accessibility Design Guidelines

### Visual Accessibility

#### Color and Contrast
```
Text Contrast: Minimum 4.5:1 (AA), 7:1 preferred (AAA)
Interactive Elements: Minimum 3:1 contrast
Color Independence: Information not conveyed by color alone
Color Blindness Safe: Test with deuteranopia/protanopia filters
```

#### Typography Accessibility
```
Font Size: Minimum 16px for body text
Line Height: Minimum 1.5x for readability
Letter Spacing: 0.05em for improved readability
Text Alignment: Left-aligned for readability
```

#### Layout Accessibility
```
Consistent Navigation: Same order across pages
Predictable Layout: Similar elements in similar positions
Clear Headings: Proper heading hierarchy (H1-H6)
Focus Indicators: Visible 2px outline on focus
```

### Motor Accessibility

#### Touch Targets
```
Minimum Size: 44px x 44px for touch targets
Spacing: Minimum 8px between interactive elements
Click Areas: Expanded beyond visual boundaries
Gesture Alternatives: Button alternatives to gestures
```

#### Keyboard Navigation
```
Tab Order: Logical, predictable sequence
Skip Links: "Skip to main content" links
Focus Trapping: Modals keep focus within
Keyboard Shortcuts: Standard shortcuts where possible
```

### Cognitive Accessibility

#### Content Organization
```
Clear Language: Simple, direct instructions
Progress Disclosure: Information revealed progressively
Consistent Terminology: Same terms throughout
Error Prevention: Confirmations for destructive actions
```

#### Help and Support
```
Contextual Help: Help available where needed
Error Messages: Clear, actionable error descriptions
Instructions: Step-by-step guidance for complex tasks
Examples: Sample responses and formats
```

---

## Mood Board and Visual Direction

### Emotional Design Goals

#### Primary Emotions to Evoke
1. **Trust:** Through consistent, professional design
2. **Calm:** Through harmonious colors and gentle transitions
3. **Confidence:** Through clear feedback and intuitive interactions
4. **Focus:** Through minimal distractions and clear hierarchy
5. **Pride:** Through institutional branding and quality presentation

#### Visual Metaphors
```
Academic Excellence: Clean, structured layouts
Reliability: Solid, stable visual elements
Growth: Upward progress indicators and positive feedback
Security: Locked icons and secure visual cues
Success: Checkmarks and progress completion
```

### Brand Integration

#### Institutional Identity
```
Logo Usage: Consistent placement and sizing
Brand Colors: Integration with CUSTECH brand guidelines
Typography: Alignment with institutional standards
Imagery: Campus photos and academic iconography
Voice: Professional, supportive, encouraging
```

#### Cultural Considerations
```
Local Context: Nigerian educational environment
Language: Clear English with local academic terminology
Symbols: Culturally appropriate icons and imagery
Values: Academic integrity, excellence, community
```

---

## Responsive Design Strategy

### Breakpoint System
```
Mobile: 320px - 767px
Tablet: 768px - 1023px
Desktop: 1024px - 1439px
Large Desktop: 1440px+
```

### Mobile-First Approach
```
Core Functionality: Available on all screen sizes
Touch Optimization: Larger touch targets on mobile
Content Priority: Essential content first
Navigation: Simplified mobile navigation
Performance: Optimized for mobile networks
```

### Adaptive Layouts
```
Flexible Grids: Percentage-based layouts
Flexible Images: Responsive image techniques
Flexible Typography: Responsive font sizes
Component Adaptation: Components reconfigure for screen size
```

---

## Design System Documentation

### Component Library Structure
```
/components
  /atoms
    /button
    /input
    /timer
    /badge
  /molecules
    /question-card
    /navigation-panel
    /feedback-message
  /organisms
    /exam-interface
    /dashboard
    /results-page
```

### Design Token System
```
/tokens
  /colors
  /typography
  /spacing
  /shadows
  /animations
  /breakpoints
```

### Usage Guidelines
```
Do's and Don'ts for each component
Accessibility requirements for each component
Performance considerations
Content guidelines
Error states and edge cases
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- Finalize color palette and typography
- Create basic component library
- Establish design tokens
- Set up component documentation

### Phase 2: Components (Week 3-4)
- Build atomic components
- Create molecular components
- Develop interaction patterns
- Test accessibility compliance

### Phase 3: Templates (Week 5-6)
- Design key page templates
- Create responsive layouts
- Implement design system
- Conduct usability testing

### Phase 4: Refinement (Week 7-8)
- User testing and feedback
- Accessibility audit
- Performance optimization
- Final documentation

---

## Success Metrics

### Design Quality Metrics
```
Accessibility Score: 100% WCAG 2.1 AA compliance
Usability Score: SUS score ≥ 75
Performance Score: Page load < 3 seconds
Consistency Score: 100% design system adherence
```

### User Experience Metrics
```
Task Completion Rate: ≥ 95%
Time on Task: Within 20% of optimal
Error Rate: ≤ 5%
Satisfaction Score: ≥ 4.0/5.0
Learnability: < 15 minutes for basic tasks
```

### Business Impact Metrics
```
Adoption Rate: ≥ 90% within first semester
Support Requests: ≤ 2 per 100 users
Training Time: < 1 hour for basic functions
User Confidence: ≥ 80% feel confident using system
Trust Score: ≥ 85% trust in system fairness
