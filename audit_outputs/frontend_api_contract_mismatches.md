# Frontend API Contract Mismatches

Static cross-reference of `apiRequest` / `fetch` calls in `frontend/src` vs backend routes.

## Critical — breaks core exam flow

| File | Line(s) | Client call | Backend reality | Predicted HTTP |
|------|---------|-------------|-----------------|----------------|
| ExaminationInterface.tsx | 110-114 | `POST .../start` body `{rules_accepted:true}` | `ExamStartRequest` requires `student_id`, `device_fingerprint` | 422 |
| ExaminationInterface.tsx | 114 | reads `started.attempt_id` | Response field `instance_id` ([exam.py:203-213](src/cbt/schemas/exam.py)) | `undefined` instance → subsequent 404 |
| ExaminationInterface.tsx | 237, 243 | `selected_option_id: label` ("A"-"D") | Grading uses `QuestionOption.id` UUID | Saves OK; score 0 on submit |
| ExaminationInterface.tsx | 324-326 | `POST .../submit` body `{}` | `ExamSubmissionRequest`: non-empty `answers`, `submission_time` | 422 |

## Critical — officer / invigilator / lecturer dashboards

| File | Line(s) | Client call | Backend reality | Predicted HTTP |
|------|---------|-------------|-----------------|----------------|
| ExamOfficerDashboard.tsx | 158 | `PUT .../examinations/{id}/blueprint` | `POST/PUT /api/v1/exam-blueprint/{blueprint_id}` | 404 |
| ExamOfficerDashboard.tsx | 183 | `POST .../examinations/{id}/venues` | Venues: `/api/v1/venues`; allocation: `POST .../allocate-venues` | 404 |
| ExamOfficerDashboard.tsx | 191 | `POST .../examinations/{id}/allocate` | `POST .../allocate-venues` | 404 |
| ExamOfficerDashboard.tsx | 212 | `PUT .../examinations/{id}/settings` | **No route** | 404 |
| InvigilatorDashboard.tsx | 156 | `POST .../instances/{studentId}/{action}` | `/api/v1/invigilator-dashboard/examination/{e}/student/{s}/{action}` | 404 |
| InvigilatorDashboard.tsx | 94 | `id: String(s.id \|\| s.student_id)` | Uses **instance id** as student id for actions | Wrong target on pause/terminate |
| LecturerDashboard.tsx | 293 | `POST .../questions/{id}/submit` | `POST .../submit-for-review` | 404 |

## Medium

| File | Line(s) | Issue |
|------|---------|-------|
| LoginPage.tsx | 213 | `POST forgot-password?email=` query string; API expects `email` as parameter (works as query in FastAPI) — OK |
| LoginPage.tsx | 44-66 | Login flow OK for `/api/v1/auth/login`, `/api/v1/auth/me` |
| StudentDashboard.tsx | 94, 121 | `/api/v1/examinations`, `/my/results` — routes exist |
| AdminDashboard.tsx | venues POST | `/api/v1/venues` exists; **Venue Beanie not registered** — runtime failure |
| features/exams/index.ts | all | Legacy `/api/v1/exams`, `/attempts` — **unused** by pages |

## Unused dependencies

- `axios` in `frontend/package.json` — no imports in `frontend/src`
