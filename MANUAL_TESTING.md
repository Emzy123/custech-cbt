# Manual testing setup

Local stack for exercising the CBT UI and API without Docker or system packages (everything installs under `.local/`).

## Quick start

```bash
# One-time bootstrap (MongoDB, Redis, Python venv, Node, npm, seed users)
chmod +x scripts/*.sh
./scripts/setup-manual-test.sh

# Start all services
./scripts/start-manual-test.sh

# Stop when done
./scripts/stop-manual-test.sh
```

Open **http://localhost:3000** and sign in with any account below.

## Test accounts

| Role | Username | Password | Dashboard route |
|------|----------|----------|-----------------|
| Super Admin | `admin` | `Admin123!` | `/admin/dashboard` |
| Lecturer | `lecturer` | `Lecturer123!` | `/lecturer/questions` |
| Student | `student` | `Student123!` | `/dashboard` |
| Exam Officer | `examofficer` | `ExamOfficer123!` | `/officer` |
| Invigilator | `invigilator` | `Invigilator123!` | `/invigilator/dashboard` |

Student matric number (if prompted): `2024/001`.

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

The React dev server proxies `/api` to port 8000 (`frontend/package.json`).

## Re-seed users

```bash
rm .local/.seeded
./scripts/start-manual-test.sh
```

Or run seed scripts manually (with MongoDB and Redis running):

```bash
source .venv/bin/activate
set -a && source .env && set +a
python seed_admin.py
python seed_users.py
python seed_officers.py
```

## Logs and data

| Path | Purpose |
|------|---------|
| `.local/logs/` | mongod, redis, backend, frontend logs |
| `.local/data/mongo/` | MongoDB data files |
| `.local/pids/` | Process PID files |

## Prerequisites

- **Python 3.11+** (3.12 OK)
- **curl**, **gcc**, **make** (Redis is compiled from source)
- **Network** for first-time downloads

If `python3 -m venv` fails (missing `python3-venv`), the setup script installs **uv** under `.local/uv` and uses that to create `.venv`.

If you already have MongoDB and Redis on `localhost`, you can skip the setup script and use the README flow instead: copy `.env.example` → `.env`, `pip install`, `npm install`, `python run_backend.py`, `npm start` in `frontend/`.

## Docker alternative

If Docker is installed:

```bash
docker compose -f docker-compose.dev.yml up -d mongo redis
# Then run backend + frontend locally as in README.md
```
