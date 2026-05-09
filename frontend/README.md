# CUSTECH GST Examination System - Frontend

A world-class, accessible, and user-friendly web application for computer-based testing at Confluence University of Science and Technology (CUSTECH), Osara.

## 🎨 Design Philosophy

**"Calm Authority"** - Every pixel communicates two things simultaneously:
- **Authority:** Secure, fair, and institutionally backed
- **Calm:** Safe, predictable, and focused on the examination experience

## 🛠 Technology Stack

- **Framework:** React 18 with TypeScript
- **Styling:** TailwindCSS with custom design system
- **Icons:** Phosphor Icons
- **State Management:** React Hooks (with future Redux integration)
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **Build Tool:** Create React App with TypeScript

## 🎯 Key Features Implemented

### Authentication System
- **Login Page:** Split-screen design with institutional branding
- **Error Handling:** Shake animation for invalid credentials
- **Accessibility:** Full WCAG 2.1 AA compliance

### Student Dashboard
- **Responsive Design:** Mobile-first approach
- **Real-time Updates:** Live countdown for upcoming exams
- **Progress Tracking:** Visual indicators for exam progress
- **Results Display:** Color-coded performance metrics

### Examination Interface
- **Timer Component:** Multi-state (normal/warning/critical) with psychological design
- **Question Navigation Grid:** 5-column grid with visual state indicators
- **Auto-save:** Every 30 seconds with visual confirmation
- **Answer Selection:** Card-based radio buttons with tactile feedback
- **Accessibility:** Full keyboard navigation and screen reader support

### Lecturer Question Bank
- **Bulk Operations:** Multi-select with keyboard shortcuts
- **Filter System:** Topic, difficulty, and status filtering
- **Review Interface:** Split-screen for efficient question approval
- **Import/Export:** CSV support for bulk question management

### Invigilator Dashboard
- **Real-time Monitoring:** Live student status updates
- **Proctoring Events:** Visual timeline of suspicious activities
- **Alert System:** Color-coded severity indicators
- **Student Actions:** Message, pause, and terminate capabilities

## 🎨 Design System

### Color Palette
```css
/* Primary Blue */
--primary-blue-50: #F0F4F8;
--primary-blue-800: #1A3A5C;
--primary-blue-900: #0F2440;

/* Surface Colors */
--surface-white: #FFFFFF;
--surface-grey: #F5F7FA;
--surface-grey-dark: #E8ECF1;

/* Semantic Colors */
--success: #2E7D32;
--warning: #F59E0B;
--danger: #DC2626;
--info: #2563EB;
```

### Typography
- **Primary Font:** Inter (UI elements)
- **Secondary Font:** Lora (Question content)
- **Type Scale:** Modular scale 1.25 (12px to 39px)

### Spacing System
- **Base Grid:** 4px
- **Scale:** 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px

### Elevation & Shadows
- **Elevation 0:** none (Page backgrounds)
- **Elevation 1:** 0 1px 3px rgba(0,0,0,0.08) (Cards)
- **Elevation 2:** 0 4px 12px rgba(0,0,0,0.10) (Dropdowns)
- **Elevation 3:** 0 8px 24px rgba(0,0,0,0.14) (Modals)

## 📱 Responsive Breakpoints

| Breakpoint | Min Width | Target Device |
|------------|-----------|---------------|
| `sm` | 640px | Large phones landscape |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large monitors |

## ♿ Accessibility Features

### WCAG 2.1 Level AA Compliance
- **Keyboard Navigation:** Full tab order and arrow key support
- **Screen Readers:** ARIA labels and live regions
- **Color Contrast:** Minimum 4.5:1 for normal text
- **Focus Indicators:** Clear 2px ring with offset
- **Skip Links:** "Skip to main content" for keyboard users

### Examination Interface Accessibility
- **Timer Announcements:** ARIA live region for time warnings
- **Question Navigation:** Keyboard-operable grid with spoken feedback
- **Answer Selection:** Large touch targets (44x44px minimum)
- **Status Updates:** Non-intrusive banners for connection issues

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cbt-system/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Start development server**
   ```bash
   npm start
   ```

4. **Open browser**
   Navigate to `http://localhost:3000`

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## 📁 Project Structure

```
src/
├── components/
│   └── ui/                 # Reusable UI components
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Input.tsx
│       ├── OptionCard.tsx
│       ├── QuestionNavigationGrid.tsx
│       └── Timer.tsx
├── pages/                  # Page components
│   ├── ExaminationInterface.tsx
│   ├── InvigilatorDashboard.tsx
│   ├── LecturerQuestionBank.tsx
│   ├── LoginPage.tsx
│   └── StudentDashboard.tsx
├── App.tsx                 # Main application component
├── index.css              # Global styles with Tailwind
└── index.tsx              # Application entry point
```

## 🧪 Testing

### Run Tests
```bash
npm test
```

### Build for Production
```bash
npm run build
```

### Lint Code
```bash
npm run lint  # (if configured)
```

## 🔧 Configuration

### TailwindCSS Configuration

The `tailwind.config.js` file contains:
- Custom color palette
- Typography scale
- Spacing system
- Animation keyframes
- Responsive breakpoints

### TypeScript Configuration

Strict TypeScript setup with:
- No implicit any
- Strict null checks
- Proper component typing
- Interface definitions for all data structures

## 🎯 Performance Optimizations

### Code Splitting
- Route-based code splitting with React.lazy
- Component-level lazy loading for large components

### Image Optimization
- WebP format support
- Responsive image sizing
- Lazy loading for non-critical images

### Bundle Optimization
- Tree shaking for unused code
- Minification in production
- Source maps for debugging

## 🔐 Security Features

### Authentication
- JWT token management
- Secure HTTP-only cookies
- CSRF protection
- Session timeout handling

### Data Protection
- Input sanitization
- XSS prevention
- Secure API communication
- Rate limiting considerations

## 🌐 Browser Support

- **Chrome 90+**
- **Firefox 88+**
- **Safari 14+**
- **Edge 90+

## 📊 Monitoring & Analytics

### Error Tracking
- Global error boundaries
- Console error logging
- User feedback collection

### Performance Monitoring
- Core Web Vitals tracking
- Load time monitoring
- User interaction analytics

## 🔄 Integration with Backend

### API Endpoints

The frontend is designed to integrate with the existing FastAPI backend:

```typescript
// Authentication
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me

// Examinations
GET  /api/v1/exams/student/upcoming
GET  /api/v1/exams/:examId
POST /api/v1/exams/:examId/submit

// Questions
GET  /api/v1/questions/bank
POST /api/v1/questions
PUT  /api/v1/questions/:id
DELETE /api/v1/questions/:id

// Monitoring
GET  /api/v1/invigilator/dashboard
GET  /api/v1/invigilator/students
POST /api/v1/invigilator/action
```

### WebSocket Integration

Real-time features use WebSocket connections:
- Live exam monitoring
- Real-time alerts
- Synchronized timer updates
- Connection status monitoring

## 🎨 Design Deliverables

### Component Library
All UI components are:
- Fully documented with TypeScript
- Accessibility compliant
- Responsive by design
- Consistent with design system

### Interactive Prototype
Complete user flows implemented:
- Login → Dashboard → Exam → Results
- Lecturer question management
- Invigilator monitoring

### Style Guide
Comprehensive design system documentation:
- Color usage guidelines
- Typography rules
- Component specifications
- Animation principles

## 🚀 Deployment

### Build Process
```bash
# Build for production
npm run build

# Test build locally
serve -s build
```

### Environment Configuration
- Production: Optimized build with minification
- Staging: Development build with production data
- Development: Hot reload with detailed logging

## 🤝 Contributing

### Code Style
- Use TypeScript for all new code
- Follow TailwindCSS utility-first approach
- Implement accessibility features
- Write meaningful commit messages

### Pull Request Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation
4. Submit pull request with description

## 📞 Support

### Help Resources
- Component documentation in code
- Design system guidelines
- Accessibility checklist
- Performance optimization guide

### Contact
- **Development Team:** dev@custech.edu.ng
- **ICT Helpdesk:** ict@custech.edu.ng

---

**CUSTECH GST Examination Portal** - Transforming assessment through thoughtful design and technology.
