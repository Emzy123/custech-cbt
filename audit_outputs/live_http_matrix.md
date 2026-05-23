# Live HTTP Matrix

**Status:** Not executed against a running server.

**Blockers observed during audit:**
- `curl http://localhost:8000/health` — connection failed
- Docker not installed; `python3-venv` / `pip3` unavailable; FastAPI not importable without dependencies
- MongoDB/Redis CLI unreachable from audit shell

## Predicted results (static contract analysis)

These predictions are from Pydantic schemas, route existence, and frontend request shapes. Re-run with `audit_outputs/run_http_matrix.sh` when stack is up.

| Endpoint | No auth | Wrong role | Expected with valid student JWT | Notes |
|----------|---------|------------|----------------------------------|-------|
| `POST /api/v1/auth/login` | 422/401 | N/A | 200 + tokens | OK if credentials valid |
| `GET /api/v1/auth/me` | 401 | 401 | 200 | OK |
| `POST /api/v1/examinations/{id}/start` body `{rules_accepted:true}` | 401 | 403 | **422** | Missing `student_id`, `device_fingerprint` ([exam.py:178-186](src/cbt/schemas/exam.py)) |
| `GET .../instances/{id}/paper` | 401 | 403 | 200 if instance IN_PROGRESS | No ownership check on instance |
| `POST .../answers` with `selected_option_id: "A"` | 401 | 403 | 200 save | Grading compares to option **UUID**, not label |
| `POST .../submit` body `{}` | 401 | 403 | **422** | Requires `answers` + `submission_time` |
| `GET /api/v1/examinations/my/results` | 401 | 403 | 200 | Uses `current_user.id` not student profile id — may return empty |
| `PUT /api/v1/examinations/{id}/blueprint` | 401 | 403 | **404** | No such route; use `/api/v1/exam-blueprint/` |
| `POST /api/v1/examinations/{id}/venues` | 401 | 403 | **404** | No such route |
| `POST /api/v1/examinations/{id}/allocate` | 401 | 403 | **404** | Actual: `POST .../allocate-venues` |
| `POST .../instances/{studentId}/pause` (invigilator UI) | 401 | 403 | **404** | Actual: `/api/v1/invigilator-dashboard/examination/{e}/student/{s}/pause` |
| `POST /api/v1/venues` | 401 | 403 | **500/validation** if Beanie | `Venue` not in `init_beanie` ([database.py:62-71](src/cbt/core/database.py)) |
| `GET /api/v1/users/` | 401 | **200** (any authed user) | 200 | No `require_permission` — IDOR/privilege issue |
| `POST /api/v1/users/` | 401 | **201** (any authed user) | 201 | Any logged-in user can create accounts |
