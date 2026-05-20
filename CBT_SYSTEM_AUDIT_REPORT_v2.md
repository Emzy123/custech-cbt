# CBT System Comprehensive Audit Report (v2)

**Date:** 20 May 2026  
**System:** CUSTECH GST Computer-Based Examination System  
**Repository:** custech-cbt  
**Audit method:** Static code analysis, route inventory, schema/contract cross-reference. Live HTTP verification **blocked** (no running backend/MongoDB/Redis in audit environment).  
**Supersedes:** [CBT_SYSTEM_AUDIT_REPORT.md](CBT_SYSTEM_AUDIT_REPORT.md) (May 2026 — inaccurate stack and completion claims)

**Supporting artifacts:**
- [audit_outputs/route_inventory_summary.md](audit_outputs/route_inventory_summary.md)
- [audit_outputs/live_http_matrix.md](audit_outputs/live_http_matrix.md)
- [audit_outputs/frontend_api_contract_mismatches.md](audit_outputs/frontend_api_contract_mismatches.md)
- [audit_outputs/deps_and_tooling.md](audit_outputs/deps_and_tooling.md)

---

## 11.1 Executive Summary

| Metric | Value |
|--------|------:|
| **Critical issues** | 12 |
| **High priority** | 14 |
| **Medium priority** | 18 |
| **Low priority** | 12 |
| **Backend routes (static count)** | 278 |
| **Frontend pages** | 9 routed + catch-all |
| **Overall health** | **Not production-ready** for core student exam workflow |

### Verdict

The codebase is a **substantial FastAPI + MongoDB (Beanie) + React** implementation with broad API surface area (~275 versioned endpoints), RBAC permissions on most routers, Argon2 password hashing, and server-side exam clock logic. However, the **student exam path is broken at the API contract layer** between React and FastAPI, and several **admin/invigilator/officer UIs call non-existent endpoints**. Venue persistence is misconfigured at the ODM layer. The prior audit report describing PostgreSQL/SQLAlchemy and “85% fully functional” is **not supported by the repository**.

**Deployability:** Fixable with **moderate effort** focused on phase-4 runtime alignment ([`.cursor/plans/full_workflow_fastapi_cbt_fc009a9f.plan.md`](.cursor/plans/full_workflow_fastapi_cbt_fc009a9f.plan.md)). Non-MVP modules (security hardening scans, pilot examination, deployment automation) are largely scaffolded.

---

## 1. Route Audit (Section 1)

### 1.1 Inventory

- **Backend:** 275 `@router.*` handlers under `/api/v1` + 3 app routes (`/`, `/health`, `/metrics`). See [audit_outputs/route_inventory_summary.md](audit_outputs/route_inventory_summary.md).
- **Frontend:** 9 role dashboards + login + roadmap; guards in [`frontend/src/App.tsx`](frontend/src/App.tsx).

### 1.2 Checklist mapping (functional equivalence)

Most audit-prompt paths exist under different names:

| Prompt route | Implemented as |
|--------------|----------------|
| `POST /api/login` | `POST /api/v1/auth/login` |
| `POST /api/logout` | `POST /api/v1/auth/logout` |
| `GET /api/user` | `GET /api/v1/auth/me`, `/profile` |
| Student exam lifecycle | `/api/v1/examinations/{id}/start`, `.../instances/{id}/paper`, `.../answers`, `.../clock`, `.../submit` |
| Lecturer questions | `/api/v1/questions/*` |
| Officer exams / allocation | `/api/v1/examinations/*`, `POST .../allocate-venues`, `/api/v1/exam-blueprint/*` |
| Invigilator control | `/api/v1/invigilator-dashboard/examination/{e}/student/{s}/*` |
| Admin CRUD | `/api/v1/users`, `/api/v1/academics`, `/api/v1/audit/logs` |
| Proctoring | `/api/v1/proctoring`, `/webcam-proctoring`, `.../proctoring/events` |
| Health | `GET /health` |

**Absent by design or gap:** `/api/student/*` namespaces; per-question `GET .../questions/{n}`; `GET .../timer` (use `.../clock`); separate `Result`/`ProctoringLog` collections; `GET /api/system/ping`; dedicated student result-review page.

### 1.3 Route protection

| Area | Finding |
|------|---------|
| Most API routers | `Depends(require_permission("..."))` on routes |
| **`/api/v1/users`** | **JWT only** — no permission checks on list/create/update/delete/roles |
| Exam instance routes | Permission only; **no instance ownership** check |
| Public auth | Login/register/forgot-password public via JWT path (session middleware exempt paths misaligned — see §4) |

### 1.4 Live response verification

**Not executed.** Predictions in [audit_outputs/live_http_matrix.md](audit_outputs/live_http_matrix.md). Re-verify when MongoDB, Redis, and backend are running.

---

## 2. Controller & Handler Audit (Section 2)

Handlers are `async def` in `src/cbt/api/*.py`; business logic in `src/cbt/services/*.py`. No orphan “controller classes.”

### Critical handler issues

| ID | File | Lines | Issue | Impact |
|----|------|-------|-------|--------|
| C-01 | `examinations.py` | 339-349 | `start_exam` uses `start_request.student_id` from body | Frontend omits field → 422; wrong ID if spoofed |
| C-02 | `exam_service.py` | 957-967 | `_calculate_answer_points` compares `selected_option_id` to option **UUID** | UI sends "A"/"B" labels → **all MCQ scored 0** |
| C-03 | `exam_service.py` | 481-548 | `submit_exam` grades **request body** answers only | Empty `{}` submit ignores autosaved `ExamAnswer` rows |
| C-04 | `schemas/exam.py` | 151-163, 178-186 | Strict `ExamSubmissionRequest` / `ExamStartRequest` | Mismatch with UI payloads |
| H-01 | `examinations.py` | 365-394 | `get_paper`, `save_answer` — no `student_id == current_user` check | IDOR across instances |
| H-02 | `users.py` | 69-274 | No `require_permission` on admin mutations | Privilege escalation |

---

## 3. Model & Database Audit (Section 3)

### Runtime stack

- **Actual:** MongoDB + Beanie ([`src/cbt/core/database.py`](src/cbt/core/database.py))
- **Docs only:** PostgreSQL schema in [`docs/phase1/database-schema.md`](docs/phase1/database-schema.md) — **not connected**

### Required entities

| Entity | Status |
|--------|--------|
| User, Student, Department, Course, AcademicSession, Semester | OK |
| QuestionBank, Question, QuestionOption | OK |
| Examination, ExamInstance, ExamAnswer | OK |
| Result | Fields on `ExamInstance` — no `results` collection |
| ProctoringLog | Redis + `AuditLog` / strikes on instance — no dedicated model |
| AuditLog | OK |
| Venue | Model exists — **not registered in `init_beanie`** |

### C-05: Venue Beanie registration

**File:** [`src/cbt/core/database.py`](src/cbt/core/database.py) lines 62-71  
**Issue:** `Venue`, `ExamVenueAssignment` omitted from `document_models` but used in [`venues.py`](src/cbt/api/venues.py) (`Venue.find`, `Venue.insert`).  
**Impact:** Venue CRUD and officer/admin venue UI fail at runtime.  
**Fix:** Register both models in `init_beanie` and export from `models/__init__.py`.

---

## 4. Middleware Audit (Section 4)

| Middleware | Present | Notes |
|------------|---------|-------|
| JWT auth (`deps.py`) | Yes | HTTPBearer |
| RBAC `require_permission` | Yes | Most routers |
| Exam access / timer / proctoring | Partial | Logic in `ExamService.sync_clock`, not dedicated middleware |
| CSRF | N/A | Bearer tokens |
| Rate limit | Yes | `RateLimitMiddleware` |
| CORS / CSP | Yes | `SecurityHeadersMiddleware` |
| Session cookie validation | Yes | Exempt paths use `/auth/login` not `/api/v1/auth/login` — **likely ineffective** for real login URL |

---

## 5. Business Logic Audit — Critical Paths (Section 5)

### 5.1 Exam start ([`exam_service.start_exam`](src/cbt/services/exam_service.py) 229-365)

| Step | Status |
|------|--------|
| Authenticated | Yes (JWT + permission) |
| Exam ACTIVE + time window | Yes |
| Max attempts | Yes |
| Enrollment / course check | **No** |
| Biometric completed | **No** (`biometric_required=False`) |
| Blueprint question selection | **No** — `_get_exam_questions` only |
| Secure per-student seed | Partial — `uuid.uuid4()` on instance, not `QuestionRandomisationService` HKDF |
| Return first question | Via separate `get_paper` call |

### 5.2 Answer save (418-436)

Upsert works; **no option-id validation**; flag stored as `is_marked_for_review`.

### 5.3 Submit (481-588)

Locks instance to SUBMITTED; does **not** mark unanswered; duplicate submit returns failure message — OK. **Does not load autosaved answers** when body empty.

### 5.4 Randomisation ([`get_paper`](src/cbt/services/exam_service.py) 367-416)

Uses `random.Random(instance.server_seed)` — deterministic but not CSPRNG; **no `option_mapping` persisted** for audit/regrading (contrast `question_randomisation_service.py`).

### 5.5 Grading

Compares option IDs only — **broken with shuffled labels from UI**.

### 5.6 Timer ([`sync_clock`](src/cbt/services/exam_service.py) 438-458)

Server authoritative `ends_at`; auto `timeout_exam` when expired — **Good**.

---

## 6. Frontend Audit (Section 6)

### Pages

| Required | Status |
|----------|--------|
| Login | Yes |
| Password reset page | Partial (prompt only) |
| Student dashboard / exam | Yes — **contract broken** |
| Result detail/review | **Missing** route |
| Lecturer / officer / invigilator / admin | Yes — **several API mismatches** |
| 404 / 500 | Redirect only |

Full mismatch table: [audit_outputs/frontend_api_contract_mismatches.md](audit_outputs/frontend_api_contract_mismatches.md).

### Invigilator data mapping bug

**File:** [`InvigilatorDashboard.tsx`](frontend/src/pages/InvigilatorDashboard.tsx) line 94  
**Issue:** `id: String(s.id || s.student_id)` prefers **exam instance id**.  
**Impact:** Pause/terminate/message target wrong resource.

---

## 7. Error & Exception Audit (Section 7)

| Check | Result |
|-------|--------|
| Python compileall | Pass |
| Global 500 handler | Yes — generic message ([`main.py`](src/cbt/main.py) 96-108) |
| Functional tests | **Module skipped** |
| Unhandled promise patterns | Frontend catch blocks often swallow errors (invigilator) |

---

## 8. Security Audit (Section 8)

| Check | Result |
|-------|--------|
| Password hashing | **Argon2** ([`core/security.py`](src/cbt/core/security.py)) |
| Hardcoded secrets in repo | Test scripts only; `.env.example` placeholders |
| Users API RBAC | **Missing** — critical |
| Instance IDOR | **Likely** on exam routes |
| JWT expiry | 15 min access ([config](src/cbt/core/config.py)) |
| SQL injection | N/A (MongoDB) |
| XSS | Not audited live — question text rendered in React; sanitize/escape recommended |

---

## 9. Configuration Audit (Section 9)

See [audit_outputs/deps_and_tooling.md](audit_outputs/deps_and_tooling.md). `DEBUG=true` default in `.env.example` — inappropriate for production.

---

## 10. Dependency Audit (Section 10)

- **compileall:** pass  
- **pip/npm audit:** not run (tooling unavailable)  
- **axios:** unused in frontend  
- **passlib[bcrypt]:** declared; Argon2 used in code  

---

## 11.2 Critical Issues (system cannot function without fixes)

| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| C-01 | `ExaminationInterface.tsx` + `ExamStartRequest` | Start payload/response mismatch | Derive `student_id` from auth; return `attempt_id` alias or fix UI to use `instance_id`; send `device_fingerprint` |
| C-02 | `ExaminationInterface.tsx` + `exam_service._calculate_answer_points` | Option labels vs UUIDs | Send `QuestionOption.id` from paper; or map label→id server-side using instance seed |
| C-03 | `ExaminationInterface.tsx` + `ExamSubmissionRequest` | Empty submit body | Submit persisted `ExamAnswer` rows or build `answers` + `submission_time` client-side |
| C-04 | `database.py` | Venue models not in Beanie | Add to `document_models` |
| C-05 | `users.py` | No RBAC on user admin API | Add `require_permission("admin.*")` or equivalent |
| C-06 | `ExamOfficerDashboard.tsx` | Blueprint/venues/allocate/settings URLs | Wire to `/exam-blueprint`, `/allocate-venues`, examination `PUT` |
| C-07 | `InvigilatorDashboard.tsx` | Wrong intervention URLs + instance/student id | Use invigilator-dashboard paths; key students by `student_id` |
| C-08 | `LecturerDashboard.tsx` | `/submit` vs `/submit-for-review` | Fix path |

---

## 11.3 High-Priority Issues

- IDOR on exam instance endpoints (no ownership check)
- Submit ignores autosaved answers
- `get_my_results` uses `current_user.id` not `Student` document id
- Invigilator lists instances API but maps fields incorrectly; should use `/invigilator-dashboard/.../dashboard`
- Functional test suite skipped; obsolete endpoint paths
- Prior audit report and PostgreSQL docs mislead operators
- Biometric gate not enforced on start
- Blueprint / `QuestionRandomisationService` not wired into live exam paper
- `random.Random` vs `secrets` for exam shuffle
- Proctoring events not persisted to dedicated store (audit only)
- Session middleware exempt path prefix mismatch

---

## 11.4 Medium-Priority Issues

- Missing pages: register, biometric enrolment, security dashboard, student result review
- No dedicated 404/500 UI
- `features/*` stale endpoint catalogs
- Duplicate academic APIs (`/courses` vs `/academics`)
- Officer slip/export via raw `<a>` + token query (works but inconsistent)
- Email/SMTP optional — password reset may no-op in dev
- N+1 queries in review/statistics paths

---

## 11.5 Low-Priority Issues

- Unused `axios` dependency
- Naming: `attempt_id` vs `instance_id` inconsistency in schemas vs comments
- `reset_lecturer_password.py` hardcoded password in repo script
- Implementation roadmap page (internal) exposed to any authenticated user
- Pilot/deployment/security-scan routers beyond GST MVP scope

---

## Prioritized Remediation Plan

Aligned with [full_workflow FastAPI CBT plan](.cursor/plans/full_workflow_fastapi_cbt_fc009a9f.plan.md):

### Wave 1 — Unblock student exam (1–3 days)

1. Fix exam start/submit/answer contract (UI + API or adapter layer).
2. Register `Venue` / `ExamVenueAssignment` in Beanie.
3. Lock down `/api/v1/users` with admin permissions.
4. Map option IDs correctly for grading.

### Wave 2 — Officer & invigilator (2–4 days)

5. Rewire `ExamOfficerDashboard` to `exam-blueprint` and `allocate-venues`.
6. Rewire `InvigilatorDashboard` to `invigilator-dashboard` API; fix student vs instance IDs.
7. Fix lecturer `submit-for-review` path.

### Wave 3 — Quality & security (3–5 days)

8. Instance ownership checks on all instance-scoped routes.
9. Submit from DB autosaves; idempotent submit.
10. Re-enable functional tests against real paths.
11. Wire `QuestionRandomisationService` + blueprint into `start_exam` / `get_paper`.
12. Biometric gate when exam settings require it.

### Wave 4 — Product completeness

13. Student result review page + route.
14. Replace misleading docs; archive v1 audit report.
15. Admin student CSV import UI (if required by SRS).

---

## Re-run live verification

When infrastructure is available:

```bash
# Terminal 1 — data stores (docker compose or local mongo/redis)
# Terminal 2
source .venv/bin/activate && python3 run_backend.py
# Terminal 3
cd frontend && npm install && npm start
# Export OpenAPI
curl -s http://localhost:8000/openapi.json -o audit_outputs/openapi.json
# Run tests
pytest tests/unit -v
```

---

*End of report — evidence from repository state on 2026-05-20; live HTTP matrix pending environment.*

---

## Post-audit remediation (Wave 1) — applied 2026-05-20

The following fixes were implemented after this report:

| Issue | Fix |
|-------|-----|
| Exam start/submit contract | Optional `ExamStartRequest` fields; resolve `student_id` from profile; `attempt_id` on response; empty submit loads autosaved answers |
| Option grading | Frontend sends option UUIDs; server resolves letter labels when needed |
| Venue Beanie | `Venue`, `ExamVenueAssignment` registered in `database.py` |
| Users API RBAC | `require_permission` on all `/api/v1/users` admin routes |
| Instance IDOR | `_ensure_instance_access` on instance-scoped exam routes |
| Officer dashboard | `exam-blueprint`, `allocate-venues`, `PUT` examination for results |
| Invigilator dashboard | Correct invigilator-dashboard URLs; `student_id` for actions |
| Lecturer submit | `submit-for-review` path |
| Session middleware | Exempt `/api/v1/auth/*` public paths |
| Student results | `/my/results` uses `Student` document id |
