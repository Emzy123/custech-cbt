# CI/CD Pipeline with Git Flow, SAST, Linting, and Dependency Vulnerability Scanning

## Pipeline Architecture Overview

### CI/CD Strategy
```
Branch Strategy: Git Flow
Integration: Continuous Integration
Deployment: Continuous Deployment to Dev/Staging
Production: Manual Approval Required
Quality Gates: Automated testing and security scanning
```

### Pipeline Stages
```
1. Code Commit → Feature Branch
2. Automated Tests → Unit, Integration, Security
3. Code Quality → Linting, Formatting, Coverage
4. Security Scanning → SAST, Dependency Scanning
5. Build → Container Image, Artifacts
6. Deploy → Development Environment
7. Integration Tests → End-to-End Testing
8. Deploy → Staging Environment
9. User Acceptance Testing → QA Validation
10. Deploy → Production (Manual Approval)
```

---

## 1. Git Flow Implementation

### Branch Structure
```
Main Branches:
- main: Production-ready code
- develop: Integration branch for features
- release/*: Release preparation branches
- hotfix/*: Emergency fixes for production

Supporting Branches:
- feature/*: New feature development
- bugfix/*: Bug fixes for current release
- support/*: Long-term support branches
```

### Git Workflow Rules
```
main Branch:
- Protected branch, no direct commits
- Only via pull requests from release branches
- Always deployable to production
- Tags for releases (v1.0.0, v1.1.0, etc.)

develop Branch:
- Integration branch for features
- Automatic deployment to development
- Must always be buildable
- Pull requests target this branch

feature/* Branches:
- Created from develop
- Feature development work
- Pull requests to develop
- Deleted after merge

release/* Branches:
- Created from develop when preparing release
- Bug fixes and final testing
- Pull requests to main and develop
- Tagged and deployed to production

hotfix/* Branches:
- Created from main for emergency fixes
- Critical bug fixes only
- Pull requests to main and develop
- Immediate deployment to production
```

### Branch Protection Rules
```
main Branch Protection:
- Require pull request reviews (2 reviewers)
- Require status checks to pass
- Require up-to-date branches before merge
- Include administrators in required reviews
- Restrict force pushes

develop Branch Protection:
- Require pull request reviews (1 reviewer)
- Require status checks to pass
- Allow force pushes for maintainers
- Include administrators in required reviews

feature/* Branches:
- No protection rules
- Allow force pushes
- Optional reviews
```

---

## 2. CI Pipeline Configuration

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ develop, main, release/*, hotfix/* ]
  pull_request:
    branches: [ develop, main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: cbt-app

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Code formatting check
        run: |
          black --check .
          isort --check-only .

      - name: Linting
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

      - name: Type checking
        run: mypy .

  unit-tests:
    runs-on: ubuntu-latest
    needs: code-quality
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Check coverage threshold
        run: |
          coverage=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); print(root.attrib.get('line-rate', '0'))")
          if (( $(echo "$coverage < 0.8" | bc -l) )); then
            echo "Coverage $coverage is below threshold 0.8"
            exit 1
          fi

  security-scan:
    runs-on: ubuntu-latest
    needs: code-quality
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety bandit semgrep

      - name: Run Bandit SAST
        run: |
          bandit -r src/ -f json -o bandit-report.json || true
          bandit -r src/ -f txt -o bandit-report.txt

      - name: Run Safety dependency scan
        run: |
          safety check --json --output safety-report.json || true
          safety check --output safety-report.txt

      - name: Run Semgrep SAST
        run: |
          semgrep --config=auto --json --output=semgrep-report.json src/ || true
          semgrep --config=auto --output=semgrep-report.txt src/

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            bandit-report.txt
            safety-report.json
            safety-report.txt
            semgrep-report.json
            semgrep-report.txt

      - name: Security gate check
        run: |
          # Check for high-severity vulnerabilities
          if [ -f bandit-report.json ]; then
            high_issues=$(cat bandit-report.json | jq '.results | map(select(.issue_severity == "HIGH")) | length')
            if [ "$high_issues" -gt 0 ]; then
              echo "Found $high_issues high-severity security issues"
              exit 1
            fi
          fi

  build:
    runs-on: ubuntu-latest
    needs: [unit-tests, security-scan]
    if: github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/release/')
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-dev:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: development
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy to development
        run: |
          echo "Deploying to development environment"
          # Add deployment commands here
          # kubectl apply -f k8s/dev/
          # helm upgrade --install cbt-dev ./helm/cbt -f helm/values-dev.yaml

  integration-tests:
    runs-on: ubuntu-latest
    needs: deploy-dev
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run integration tests
        run: |
          pytest tests/integration/ --base-url=https://dev.cbt.custech.edu.ng

      - name: Run API tests
        run: |
          pytest tests/api/ --base-url=https://api-dev.cbt.custech.edu.ng
```

### Release Pipeline Workflow
```yaml
# .github/workflows/release.yml
name: Release Pipeline

on:
  push:
    tags:
      - 'v*'

jobs:
  create-release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Create Release
        id: create_release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false

  deploy-staging:
    runs-on: ubuntu-latest
    needs: create-release
    environment: staging
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment"
          # Add staging deployment commands

  staging-tests:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: staging
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run end-to-end tests
        run: |
          pytest tests/e2e/ --base-url=https://staging.cbt.custech.edu.ng

      - name: Run performance tests
        run: |
          pytest tests/performance/ --base-url=https://staging.cbt.custech.edu.ng

  deploy-production:
    runs-on: ubuntu-latest
    needs: staging-tests
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy to production
        run: |
          echo "Deploying to production environment"
          # Add production deployment commands

  production-smoke-tests:
    runs-on: ubuntu-latest
    needs: deploy-production
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run smoke tests
        run: |
          pytest tests/smoke/ --base-url=https://cbt.custech.edu.ng

      - name: Notify deployment success
        if: success()
        run: |
          echo "Deployment to production successful"
          # Add notification logic (Slack, email, etc.)
```

---

## 3. Static Application Security Testing (SAST)

### Bandit Configuration
```yaml
# .bandit
targets:
  - src/
exclude_dirs:
  - tests/
  - migrations/
  - venv/

plugins:
  - bandit.plugins.audit
  - bandit.plugins.builtins
  - bandit.plugins.crypto
  - bandit.plugins.discovery
  - bandit.plugins.injection
  - bandit.plugins.insecure_default
  - bandit.plugins.insecure_deserialization
  - bandit.plugins.insecure_hash
  - bandit.plugins.insecure_imports
  - bandit.plugins.insecure_pickle
  - bandit.plugins.insecure_random
  - bandit.plugins.insecure_shell
  - bandit.plugins.insecure_ssl
  - bandit.plugins.jinja2
  - bandit.plugins.logging
  - bandit.plugins.misc
  - bandit.plugins.python_debug
  - bandit.plugins.try_except
  - bandit.plugins weakness

tests:
  - B101: assert_used
  - B102: exec_used
  - B103: set_bad_file_permissions
  - B104: hardcoded_bind_all_interfaces
  - B105: hardcoded_password_string
  - B106: hardcoded_password_funcarg
  - B107: hardcoded_password_default
  - B108: hardcoded_tmp_directory
  - B110: try_except_pass
  - B112: try_except_continue
  - B201: flask_debug_true
  - B301: pickle
  - B302: marshal
  - B303: eval
  - B304: mark_safe
  - B305: mark_safe
  - B306: mark_safe
  - B307: mark_safe
  - B308: mark_safe
  - B309: httpsconnection
  - B310: urllib_urlopen
  - B311: urllib_urlopen
  - B312: telnetlib
  - B313: xml_bad_cElementTree
  - B314: xml_bad_etree
  - B315: xml_bad_expatbuilder
  - B316: xml_bad_expatreader
  - B317: xml_bad_sax
  - B318: xml_bad_minidom
  - B319: xml_bad_pulldom
  - B320: xml_bad_xmlrpc
  - B321: ftplib
  - B322: input
  - B323: unverified_context
  - B325: tempnam
  - B401: import_telnetlib
  - B402: import_ftplib
  - B403: import_pickle
  - B404: import_subprocess
  - B405: import_pycrypto
  - B406: import_cryptography
  - B407: import_paramiko
  - B408: import_requests
  - B409: import_urllib3
  - B410: import_yaml
  - B411: import_xmlrpc
  - B412: import_pymysql
  - B413: import_psycopg2
  - B501: request_with_no_cert_validation
  - B502: ssl_with_no_version
  - B503: ssl_with_bad_defaults
  - B504: ssl_with_bad_version
  - B505: weak_cryptographic_key
  - B506: ssl_with_bad_ciphers
  - B507: ssh_no_host_key_verification
  - B601: paramiko_injection
  - B602: subprocess_popen_with_shell_equals_true
  - B603: subprocess_without_shell_equals_true
  - B604: shell_injection_subprocess
  - B605: shell_injection_start_process_with_partial_path
  - B606: start_process_with_a_shell
  - B607: start_process_with_no_path
  - B608: hardcoded_sql_expressions
  - B609: linux_commands_wildcard_injection
  - B610: django_extra_used
  - B611: django_raw_used
  - B701: jinja2_autoescape_false
  - B702: use_of_mako_templates
  - B703: django_mark_safe
  - B704: yaml_load
```

### Semgrep Configuration
```yaml
# .semgrep.yml
rules:
  - id: security.hardcoded-secret
    pattern: |
      $KEY = "$SECRET"
    languages: [python]
    message: Hardcoded secret detected
    severity: ERROR
    metadata:
      category: security
      technology:
        - python
      confidence: HIGH

  - id: security.sql-injection
    pattern: |
      cursor.execute($QUERY + $INPUT)
    languages: [python]
    message: Potential SQL injection vulnerability
    severity: ERROR
    metadata:
      category: security
      technology:
        - python
      confidence: HIGH

  - id: security.path-traversal
    pattern: |
      open($USER_INPUT, ...)
    languages: [python]
    message: Potential path traversal vulnerability
    severity: ERROR
    metadata:
      category: security
      technology:
        - python
      confidence: MEDIUM

  - id: security.xss
    pattern: |
      $TEMPLATE.render($USER_INPUT)
    languages: [python]
    message: Potential XSS vulnerability
    severity: ERROR
    metadata:
      category: security
      technology:
        - python
      confidence: MEDIUM
```

---

## 4. Code Quality and Linting

### Black Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
```

### Flake8 Configuration
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503
max-complexity = 10
select = B,C,E,F,W,T4,B9
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    migrations
per-file-ignores =
    __init__.py:F401
    tests/*:S
```

### MyPy Configuration
```toml
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
```

---

## 5. Dependency Management and Vulnerability Scanning

### Requirements Management
```python
# requirements.txt
Django==4.1.7
djangorestframework==3.14.0
psycopg2-binary==2.9.5
redis==4.5.1
celery==5.2.7
gunicorn==20.1.0
whitenoise==6.3.0
```

```python
# requirements-dev.txt
pytest==7.2.1
pytest-cov==4.0.0
pytest-django==4.5.2
black==23.1.0
isort==5.12.0
flake8==6.0.0
mypy==1.0.1
bandit==1.7.4
safety==2.3.5
semgrep==1.14.0
```

### Safety Configuration
```yaml
# .safety-policy.yml
security:
  ignore-vulnerabilities:
    - 51458  # Example: Temporary ignore for specific vulnerability
  full-report: true
  key: # Optional API key for paid features
```

### Dependency Update Workflow
```yaml
# .github/workflows/dependency-update.yml
name: Dependency Update

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Update pip
        run: python -m pip install --upgrade pip

      - name: Update dependencies
        run: |
          pip-compile --upgrade requirements.in
          pip-compile --upgrade requirements-dev.in

      - name: Check for changes
        id: verify-changed-files
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
          fi

      - name: Create Pull Request
        if: steps.verify-changed-files.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore: update dependencies'
          title: 'chore: update dependencies'
          body: |
            Automated dependency update
            
            This PR updates the project dependencies to their latest versions.
            
            Please review the changes and ensure all tests pass before merging.
          branch: chore/update-dependencies
          delete-branch: true
```

---

## 6. Testing Strategy

### Test Structure
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_authentication.py
├── e2e/
│   ├── test_exam_flow.py
│   ├── test_user_journey.py
│   └── test_admin_workflow.py
├── performance/
│   ├── test_load.py
│   ├── test_stress.py
│   └── test_scalability.py
├── security/
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_data_protection.py
└── smoke/
    ├── test_basic_functionality.py
    └── test_system_health.py
```

### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    smoke: Smoke tests
    slow: Slow running tests
```

### Test Configuration
```python
# conftest.py
import pytest
import django
from django.test import TestCase
from django.conf import settings

@pytest.fixture(scope='session')
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    django.setup()

@pytest.fixture
def test_user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(test_user, client):
    client.login(username='testuser', password='testpass123')
    return client
```

---

## 7. Environment Configuration

### Environment Variables
```bash
# .env.example
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/cbt_dev
DATABASE_NAME=cbt_dev
DATABASE_USER=cbt_user
DATABASE_PASSWORD=secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security Configuration
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=cbt.settings.development
DEBUG=True

# External Services
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Monitoring and Logging
LOG_LEVEL=DEBUG
SENTRY_DSN=your-sentry-dsn
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "cbt.wsgi:application"]
```

---

## 8. Monitoring and Alerting

### Pipeline Monitoring
```yaml
# .github/workflows/monitoring.yml
name: Pipeline Monitoring

on:
  workflow_run:
    workflows: ["CI Pipeline", "Release Pipeline"]
    types:
      - completed

jobs:
  monitor-pipeline:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion != 'success' }}
    steps:
      - name: Notify pipeline failure
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          channel: '#ci-cd'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          text: |
            Pipeline ${{ github.event.workflow_run.name }} failed!
            Repository: ${{ github.repository }}
            Branch: ${{ github.event.workflow_run.head_branch }}
            Commit: ${{ github.event.workflow_run.head_sha }}
```

### Performance Monitoring
```yaml
# .github/workflows/performance.yml
name: Performance Monitoring

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install locust pytest

      - name: Run load tests
        run: |
          locust --headless --users 100 --spawn-rate 10 --run-time 60s --host https://staging.cbt.custech.edu.ng -f tests/performance/locustfile.py

      - name: Generate performance report
        run: |
          python tests/performance/generate_report.py

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance-report.html
```

---

## 9. Quality Gates and Policies

### Quality Gate Configuration
```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  pull_request:
    branches: [ develop, main ]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run all quality checks
        run: |
          # Code formatting
          black --check .
          isort --check-only .
          
          # Linting
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
          
          # Type checking
          mypy .
          
          # Security scanning
          bandit -r src/ -f json -o bandit-report.json
          safety check --json --output safety-report.json
          semgrep --config=auto --json --output=semgrep-report.json src/
          
          # Unit tests
          pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80

      - name: Quality gate evaluation
        run: |
          # Check code quality metrics
          coverage=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); print(root.attrib.get('line-rate', '0'))")
          
          # Check security issues
          high_issues=$(cat bandit-report.json | jq '.results | map(select(.issue_severity == "HIGH")) | length')
          
          # Evaluate quality gate
          if (( $(echo "$coverage < 0.8" | bc -l) )); then
            echo "❌ Coverage gate failed: $coverage < 0.8"
            exit 1
          fi
          
          if [ "$high_issues" -gt 0 ]; then
            echo "❌ Security gate failed: $high_issues high-severity issues"
            exit 1
          fi
          
          echo "✅ All quality gates passed"
```

### Branch Protection Rules
```yaml
# .github/branch-protection.yml
protection_rules:
  main:
    required_status_checks:
      strict: true
      contexts:
        - "code-quality"
        - "unit-tests"
        - "security-scan"
        - "build"
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 2
      dismiss_stale_reviews: true
      require_code_owner_reviews: true
    restrictions:
      users: []
      teams: ["core-team"]

  develop:
    required_status_checks:
      strict: false
      contexts:
        - "code-quality"
        - "unit-tests"
        - "security-scan"
        - "build"
    enforce_admins: false
    required_pull_request_reviews:
      required_approving_review_count: 1
      dismiss_stale_reviews: true
    restrictions:
      users: []
      teams: ["development-team"]
```

---

## 10. Success Metrics and KPIs

### Pipeline Performance Metrics
```
Build Success Rate: ≥ 95%
- Successful builds / total builds
- Target: 95% or higher
- Measured: Weekly average

Build Time: < 10 minutes
- Time from commit to deployment
- Target: < 10 minutes for development
- Measured: Average build duration

Test Coverage: ≥ 80%
- Code coverage percentage
- Target: 80% or higher
- Measured: Per build

Security Scan Pass Rate: 100%
- No high-severity vulnerabilities
- Target: Zero high-severity issues
- Measured: Per build
```

### Quality Metrics
```
Code Quality Score: ≥ 8.5/10
- Combined linting, formatting, type checking
- Target: 8.5 or higher
- Measured: Per pull request

Defect Density: < 1 defect per 1000 lines
- Number of defects found in production
- Target: < 1 per 1000 lines of code
- Measured: Monthly average

Mean Time to Recovery (MTTR): < 1 hour
- Time to fix production issues
- Target: < 1 hour for critical issues
- Measured: Average recovery time
```

### Development Metrics
```
Pull Request Merge Time: < 24 hours
- Time from PR creation to merge
- Target: < 24 hours average
- Measured: Monthly average

Deployment Frequency: ≥ 1 per day
- Number of deployments to development
- Target: At least 1 per day
- Measured: Weekly average

Change Lead Time: < 2 days
- Time from commit to production
- Target: < 2 days for changes
- Measured: Monthly average
```

This comprehensive CI/CD pipeline provides automated testing, security scanning, quality checks, and deployment capabilities while maintaining high standards for code quality, security, and reliability throughout the development lifecycle.
