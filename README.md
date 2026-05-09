# CBT System - Computer-Based Testing Platform

A comprehensive Computer-Based Testing (CBT) system for CUSTECH (Confluence University of Science and Technology), featuring multi-factor authentication, biometric integration, role-based access control, and secure exam management.

## 🚀 Features

### Core Functionality
- **Multi-Factor Authentication**: Password, biometric, and TOTP support
- **Role-Based Access Control**: Students, Lecturers, Examination Officers, Administrators
- **Secure Session Management**: JWT tokens with Redis caching and device fingerprinting
- **Academic Management**: Courses, departments, academic sessions, semesters
- **Student Lifecycle**: Registration, course enrollment, bulk import, soft delete
- **Examination System**: Question banks, exam creation, real-time monitoring, grading
- **Audit Logging**: Comprehensive security and academic integrity tracking

### Security Features
- **Zero Trust Architecture**: Comprehensive security model
- **Biometric Integration**: Fingerprint, facial, and voice recognition
- **Data Encryption**: End-to-end encryption for sensitive data
- **Rate Limiting**: DDoS protection and abuse prevention
- **Security Headers**: OWASP-compliant security headers
- **Session Security**: Device fingerprinting and concurrent session limits

### Performance & Scalability
- **Redis Caching**: Performance optimization for frequent operations
- **Database Indexing**: Optimized queries for exam performance
- **Async Operations**: High-performance async/await architecture
- **Docker Support**: Containerized deployment with orchestration
- **Monitoring**: Prometheus metrics and Grafana dashboards

## 📋 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI    │    │   FastAPI App   │    │   PostgreSQL    │
│   (React/Vue)    │◄──►│   (Python 3.11) │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      Redis      │
                       │   (Cache/Store) │
                       └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+
- **Database**: PostgreSQL 14+ with AsyncPG
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0.23
- **Authentication**: JWT, Argon2, Biometric Templates

### Security
- **Encryption**: Fernet, PBKDF2, Argon2
- **Biometrics**: Template-based fingerprint/facial recognition
- **Session Management**: Redis-based with device fingerprinting
- **Audit Logging**: Comprehensive security events tracking

### Deployment
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Docker Swarm (Production)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/custech/cbt-system.git
cd cbt-system
```

2. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Development environment**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. **Production environment**
```bash
docker-compose up -d
```

### Manual Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup database**
```bash
# Create PostgreSQL database
createdb cbt_db

# Run migrations
alembic upgrade head
```

3. **Start Redis**
```bash
redis-server
```

4. **Run the application**
```bash
python -m cbt.main
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cbt_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your-super-secret-jwt-key
BIOMETRIC_ENCRYPTION_KEY=your-biometric-encryption-key-32-bytes
SECRET_KEY=your-secret-key-for-session-management

# Application
DEBUG=false
ENVIRONMENT=production
API_V1_STR=/api/v1
```

### Database Configuration

The system uses PostgreSQL with the following optimized settings:

```sql
-- Performance settings
shared_preload_libraries = 'pg_stat_statements'
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

### Redis Configuration

```conf
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 📚 API Documentation

### Authentication Endpoints

```http
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/profile
```

### Student Management

```http
POST /api/v1/students
GET  /api/v1/students
GET  /api/v1/students/{id}
PUT  /api/v1/students/{id}
DELETE /api/v1/students/{id}
POST /api/v1/students/import
```

### Course Management

```http
POST /api/v1/courses
GET  /api/v1/courses
GET  /api/v1/courses/{id}
PUT  /api/v1/courses/{id}
DELETE /api/v1/courses/{id}
```

### Examination Management

```http
POST /api/v1/examinations
GET  /api/v1/examinations
GET  /api/v1/examinations/{id}
POST /api/v1/examinations/{id}/start
POST /api/v1/examinations/{id}/submit
```

### Interactive Documentation

Access the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 👥 User Roles & Permissions

### Students
- View courses and enroll
- Take examinations
- View results and grades
- Manage personal profile

### Lecturers
- Create and manage courses
- Create question banks
- Create and grade examinations
- View student performance

### Examination Officers
- Schedule examinations
- Monitor exam sessions
- Publish results
- Generate reports

### Administrators
- Manage users and roles
- Configure system settings
- Monitor system health
- Manage security policies

## 🔒 Security Implementation

### Authentication Flow

1. **Login Request**: Username/password + optional biometric
2. **Credential Verification**: Password hash validation + biometric matching
3. **Session Creation**: JWT tokens + Redis session storage
4. **Device Fingerprinting**: Browser/IP-based device identification
5. **Session Validation**: Continuous session integrity checks

### Biometric Security

- **Template Encryption**: Fernet encryption for biometric templates
- **Secure Storage**: Encrypted templates in database
- **Matching Thresholds**: Configurable similarity thresholds
- **Device Integration**: Support for multiple biometric devices

### Data Protection

- **Encryption at Rest**: Database field-level encryption
- **Encryption in Transit**: TLS 1.3 for all communications
- **Audit Logging**: Complete action logging with user context
- **Data Retention**: Configurable retention policies

## 📊 Monitoring & Logging

### Health Checks

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "host": "localhost",
    "port": 5432
  },
  "redis": {
    "status": "healthy",
    "host": "localhost",
    "port": 6379
  }
}
```

### Metrics

- **Application Metrics**: Request latency, error rates, user sessions
- **Database Metrics**: Connection pool, query performance, storage
- **Security Metrics**: Authentication attempts, failed logins, security events
- **Business Metrics**: Exam participation, completion rates, grade distributions

### Logging

- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Centralized Logging**: ELK stack integration
- **Audit Trail**: Complete user action logging

## 🧪 Testing

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Coverage report
pytest --cov=cbt --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Database and service integration
- **Contract Tests**: API contract validation
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

## 🚀 Deployment

### Development Deployment

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production Deployment

```bash
docker-compose up -d
```

### Environment-Specific Configurations

- **Development**: Debug mode, hot reload, detailed logging
- **Staging**: Production-like configuration, testing data
- **Production**: Optimized settings, security hardening

## 📈 Performance Optimization

### Database Optimization

- **Indexing Strategy**: Comprehensive indexing for query performance
- **Connection Pooling**: Async connection pool management
- **Query Optimization**: Efficient query patterns and N+1 prevention
- **Partitioning**: Time-based partitioning for large tables

### Caching Strategy

- **Redis Caching**: Session data, permissions, frequently accessed data
- **Application Caching**: In-memory caching for static data
- **CDN Integration**: Static asset delivery optimization
- **Cache Invalidation**: Intelligent cache invalidation policies

### Scalability Features

- **Horizontal Scaling**: Stateless application design
- **Load Balancing**: Multiple instance support
- **Database Sharding**: Read replicas and write scaling
- **Async Processing**: Background job processing

## 🔧 Development Guide

### Code Structure

```
src/cbt/
├── api/           # API endpoints
├── core/          # Core utilities (config, security, database)
├── models/        # Database models
├── schemas/       # Pydantic schemas
├── services/      # Business logic services
└── main.py        # Application entry point
```

### Development Workflow

1. **Feature Development**: Create feature branch
2. **Code Review**: Peer review and security review
3. **Testing**: Unit and integration tests
4. **Documentation**: API documentation updates
5. **Deployment**: Staging deployment and validation
6. **Production**: Production deployment with monitoring

### Coding Standards

- **Python**: PEP 8 compliance with Black formatting
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings
- **Security**: OWASP security guidelines
- **Testing**: Minimum 80% code coverage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines

- **Code Quality**: Follow coding standards and best practices
- **Testing**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **Security**: Consider security implications of changes
- **Performance**: Monitor performance impact

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](./docs/api/)
- [Development Guide](./docs/development/)
- [Deployment Guide](./docs/deployment/)
- [Security Guide](./docs/security/)

### Issues & Support
- **Bug Reports**: Create GitHub issues with detailed information
- **Feature Requests**: Submit feature proposals with use cases
- **Security Issues**: Report security issues privately to maintainers
- **Questions**: Use GitHub Discussions for general questions

### Contact
- **Development Team**: dev@custech.edu.ng
- **Security Team**: security@custech.edu.ng
- **Support Team**: support@custech.edu.ng

## 🗺️ Roadmap

### Phase 1: Core System (Current)
- [x] Authentication & Authorization
- [x] Student Management
- [x] Course Management
- [x] Examination System
- [x] Security & Audit Logging

### Phase 2: Advanced Features
- [ ] Biometric Integration
- [ ] Advanced Analytics
- [ ] Mobile Application
- [ ] Integration APIs
- [ ] Performance Optimization

### Phase 3: Enterprise Features
- [ ] Multi-tenant Support
- [ ] Advanced Security
- [ ] AI-Powered Features
- [ ] Cloud Native Deployment
- [ ] Advanced Analytics

## 📊 System Status

- **Current Version**: 1.0.0
- **Last Updated**: 2024-04-28
- **Status**: Production Ready
- **Support**: Active Development
- **License**: MIT

---

**CBT System** - Empowering education through technology 🎓
