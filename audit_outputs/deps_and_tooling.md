# Dependencies, Tooling, and Config Audit

**Date:** 2026-05-20

## Compile / build / tests

| Check | Result |
|-------|--------|
| `python3 -m compileall -q src` | **PASS** (exit 0) |
| `pytest tests/unit` | **NOT RUN** — FastAPI/pytest not installed in audit environment |
| `frontend npm run build` | **NOT RUN** — `node_modules` absent; `npm` not on PATH |
| `pip audit` / `npm audit` | **NOT RUN** — pip/npm unavailable |

## Test suite status

| File | Status |
|------|--------|
| `tests/functional/test_exam_flow.py` | **Skipped** at module import (`pytest.skip` line 6-8) |
| `tests/unit/test_smoke.py` | Imports `app` only — requires deps to execute |
| `tests/unit/test_auth_service_current.py` | Requires deps |

Functional tests reference obsolete paths (`/api/v1/exam-blueprints`, etc.).

## `.env.example` vs `Settings` ([config.py](src/cbt/core/config.py))

**Documented in `.env.example`:** DATABASE_*, REDIS_*, JWT_*, APP_*, SECRET_KEY, RANDOMISATION_SECRET, BIOMETRIC_*, SMTP_*, UPLOAD_*, LOG_*, SESSION_*, RATE_LIMIT_*, HEALTH/METRICS, SEED_ADMIN_*.

**In Settings but missing or incomplete in `.env.example`:**
- `JWT_ISSUER`, `JWT_AUDIENCE`
- `DATABASE_USER`, `DATABASE_PASSWORD` (optional auth to Mongo)
- `ALLOWED_HOSTS`
- `PORT` (documented indirectly via run script)
- `RATE_LIMIT_BURST`
- `FACIAL_THRESHOLD`, `VOICE_THRESHOLD`
- `API_V1_STR` (has default)

**Placeholder risk:** `CHANGE_ME_*` values in `.env.example` will fail production if copied verbatim.

## Unused / declared dependencies

| Package | Declared | Used in src |
|---------|----------|-------------|
| `axios` (frontend) | package.json | **No imports** |
| `passlib[bcrypt]` | requirements.txt | Auth uses **argon2** via `argon2-cffi` |
| `aiohttp` | requirements.txt | Verify usage — likely low |

## Documentation drift

| Document | Claims | Code reality |
|----------|--------|--------------|
| `CBT_SYSTEM_AUDIT_REPORT.md` | SQLAlchemy, PostgreSQL, 85% complete | MongoDB/Beanie |
| `docs/phase1/database-schema.md` | PostgreSQL DDL | Not used at runtime |
| `frontend/README.md` | `/api/v1/exams/student/upcoming` | `/api/v1/examinations` |
