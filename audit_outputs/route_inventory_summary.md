# Route Inventory Summary (Static Extraction)

**Date:** 2026-05-20  
**Method:** Grep of `@router.(get|post|put|patch|delete)` in `src/cbt/api/*.py` + `main.py` app routes.  
**Live OpenAPI:** Not exported — backend/MongoDB/Redis unavailable in audit environment (no Docker, no pip/venv).

## Counts

| Source | Count |
|--------|------:|
| API router decorators | 275 |
| App-level routes (`/`, `/health`, `/metrics`) | 3 |
| **Total HTTP operations** | **278** |

## Router prefixes (`/api/v1` + prefix)

| Router file | Prefix | Endpoints |
|-------------|--------|----------:|
| auth.py | /auth | 12 |
| users.py | /users | 9 (no `require_permission` on router) |
| students.py | /students | 17 |
| courses.py | /courses | 20 |
| academics.py | /academics | 22 |
| venues.py | /venues | 8 |
| examinations.py | /examinations | 28 |
| questions.py | /questions | 18 |
| exam_blueprint.py | /exam-blueprint | 18 |
| question_security.py | /question-security | 17 |
| biometric.py | /biometric | 16 |
| proctoring.py | /proctoring | 15 |
| webcam_proctoring.py | /webcam-proctoring | 15 |
| invigilator_dashboard.py | /invigilator-dashboard | 16 |
| audit.py | /audit | 3 |
| security_hardening.py | /security | 14 |
| pilot_examination.py | /pilot-examination | 19 |
| deployment.py | /deployment | 18 |

## Frontend routes (`frontend/src/App.tsx`)

| Path | Guard | Component |
|------|-------|-----------|
| `/` | Public | LoginPage |
| `/dashboard` | student | StudentDashboard |
| `/exam/:examId` | Protected (any auth) | ExaminationInterface |
| `/lecturer/dashboard` | lecturer + admins | LecturerDashboard |
| `/lecturer/questions` | lecturer + admins | LecturerQuestionBank |
| `/invigilator/dashboard` | invigilator + admins | InvigilatorDashboard |
| `/officer` | officer + admins | ExamOfficerDashboard |
| `/admin/dashboard` | admin roles | AdminDashboard |
| `/implementation-roadmap` | Protected | ImplementationRoadmap |
| `*` | Redirect | role home or login |

## Global middleware (`src/cbt/api/middleware.py`)

- CORSMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware, SessionValidationMiddleware, AuditMiddleware

Session exempt paths (no `/api/v1` prefix): `/health`, `/docs`, `/openapi.json`, `/auth/login`, `/auth/register`, `/static`
