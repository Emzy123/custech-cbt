# CUSTECH CBT System

A comprehensive Computer-Based Testing (CBT) platform for Confluence University of Science and Technology (CUSTECH). This system features multi-factor authentication, biometric integration, role-based access control, and secure examination management.

## 🚀 Features

### Core Functionality
- **Role-Based Access Control**: Dashboards for Students, Lecturers, Examination Officers, and Administrators.
- **Academic Management**: Manage courses, departments, academic sessions, and semesters.
- **Examination System**: Question banks, blueprint editors, randomized exam generation, and automatic grading.
- **Examination Runtime**: Real-time monitoring, offline-aware answer queueing, and secure lockdown gateways.
- **Analytics & Results**: Item analysis (P-value, discrimination), result embargo policies, and CSV exports.

### Security
- **Multi-Factor Authentication**: Password, TOTP, and biometric templates.
- **Proctoring**: Real-time strikes for focus loss and webcam events.
- **Secure Sessions**: JWT tokens with Redis caching, device fingerprinting, and concurrent limits.
- **Audit Logging**: Comprehensive tracking of all security events and academic changes.

## 📋 System Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   FastAPI App   │    │    MongoDB      │
│   (React/TS)    │◄──►│  (Python 3.11)  │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      Redis      │
                       │  (Cache/Queue)  │
                       └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+, Beanie ODM (Motor)
- **Frontend**: React 18, TypeScript, TailwindCSS, Phosphor Icons
- **Database**: MongoDB 7+
- **Cache & Session**: Redis 7+
- **Security**: Argon2, Fernet Encryption, JWT

---

## 💻 How to Start the Application Locally

The project consists of a Python FastAPI backend and a React frontend. You need **MongoDB** and **Redis** running locally (or available via cloud URIs).

### 1. Prerequisites
- **Python 3.11+**
- **Node.js** (v16+)
- **MongoDB** (running on `localhost:27017` by default)
- **Redis** (running on `localhost:6379` by default)

### 2. Environment Setup

If you haven't already, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `.env` has valid values for:
- `DATABASE_URL` (e.g. `mongodb://localhost:27017`)
- `REDIS_URL` (e.g. `redis://localhost:6379/0`)
- `JWT_SECRET`, `SECRET_KEY`, `BIOMETRIC_ENCRYPTION_KEY`, `RANDOMISATION_SECRET`

### 3. Start the Backend

Open a terminal in the root of the project:

```bash
# 1. Activate the Python virtual environment
source .venv/bin/activate

# 2. Install dependencies (if you haven't already)
pip install -r requirements.txt

# 3. Start the FastAPI server
python3 run_backend.py
```
> The backend will start on **http://localhost:8000**.
> You can view the interactive API documentation at **http://localhost:8000/docs**.

### 4. Start the Frontend

Open a **second terminal window**, and navigate to the `frontend` directory:

```bash
# 1. Change to the frontend directory
cd frontend

# 2. Install Node dependencies (if you haven't already)
npm install

# 3. Start the React development server
npm start
```
> The frontend will start on **http://localhost:3000** and automatically proxy API requests to port 8000.

---

## 👥 Role Dashboards

Once both the frontend and backend are running, go to **http://localhost:3000**. You can log in to explore different interfaces. The app will automatically route you to your appropriate dashboard based on your role:

- **Student** (`/dashboard`): View upcoming exams, start active exams, view released results.
- **Lecturer** (`/lecturer/questions`): Manage question banks, create questions, review questions.
- **Exam Officer** (`/officer`): Schedule exams, generate blueprints, allocate venues, print slips, and manage result embargoes.
- **Invigilator** (`/invigilator/dashboard`): Monitor active exam sessions, view live proctoring alerts, pause/terminate sessions.
- **Admin** (`/admin/dashboard`): Manage academics, sessions, venues, and bulk-import students.

*(Note: During local development, you may need to seed the database with mock users to test different roles. Check the `seed_admin.py` or create users via the API).*

---

## 🔒 Security Information

### Security API and permissions (operators)

All security-hardening routes are under **`/api/v1/security`** (see OpenAPI at `/docs` when `ENVIRONMENT=development`).

| Area | Example endpoints | Permission strings |
|------|-------------------|-------------------|
| In-app SAST | `POST /security/sast/scan` | `security.scan` |
| Scan listing and detail | `GET /security/scans`, `GET /security/scan/{scan_id}` | `security.read` |
| Dashboard | `GET /security/dashboard` | `security.read` |
| Other controls | DAST, WAF, penetration test, remediation | `security.scan`, `security.penetration_test`, `security.harden`, `security.configure`, `security.audit`, `security.remediate`, `security.acknowledge`, `security.manage` |

Scans persist to MongoDB collections **`security_scans`** and findings to **`vulnerabilities`**. CLI SAST (e.g. Bandit) is separate from the in-app scan endpoint; you can run Bandit in CI or locally against `src/cbt`.

**Roles:** Users with the **`ADMINISTRATOR`** role receive the security, biometric, pilot, deployment, and question-security permissions used by these routers. **`SUPER_ADMIN`** still implies all permissions (`*`). If an endpoint returns 403, confirm the user’s role assignments in `user_roles`.

**Metrics:** When `METRICS_ENABLED=true`, Prometheus can scrape **`GET /metrics`** (plain-text exposition format).

**Integration tests:** Set `CBT_INTEGRATION_MONGO_URL` (e.g. `mongodb://localhost:27017`) so `tests/conftest.py` can point Beanie at a real Mongo before import; run `pytest tests/integration -m integration`. Default `pytest` excludes integration tests (see `pyproject.toml`).

- **Keys**: Never commit `.env` containing real secrets.
- **Biometrics**: The system stores encrypted templates, not raw biometric images.
- **Audit Logs**: Administrators can query security summaries and export compliance logs via `/api/v1/audit/logs`.
