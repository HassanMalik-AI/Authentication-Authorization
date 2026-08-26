# Enterprise Authentication & Authorization Module

A **production-ready, enterprise-grade, reusable authentication and authorization module** built with FastAPI, PostgreSQL, Redis, and industry best practices.

## 🎯 Key Features

### Security First 🔒
- **Argon2 Password Hashing** - Resistant to GPU and ASIC attacks
- **JWT Tokens** with unique JTI for blacklisting
- **HTTP-Only Secure Cookies** - XSS and CSRF protection
- **Strong CSP Headers** - No unsafe-inline or unsafe-eval
- **Rate Limiting** - Distributed (Redis) + in-memory fallback
- **Account Lockout** - After 5 failed attempts
- **Audit Logging** - Complete trail of all auth events
- **Token Expiration** - Access (15 min) + Refresh (7 days)

### Complete Feature Set ✅
- User Registration & Email Verification
- Login/Logout with Session Management
- Multi-Device Session Tracking
- Password Reset Flow
- Role-Based Access Control (RBAC)
- Permission Management
- Two-Factor Authentication (MFA) Ready
- Multi-Tenant Support
- Row-Level Security (RLS)

### Production Ready 🚀
- Fully tested and documented
- Docker & Kubernetes ready
- Scalable architecture
- Proper error handling
- CORS configured
- Comprehensive logging
- Health check endpoints

### Reusable 🔄
Can be integrated as:
- Standalone microservice
- Embedded in FastAPI project
- Python package
- Docker container

## 📦 What's Included

```
├── app/                              # Main application
│   ├── core/                        # Core auth logic
│   │   ├── config.py               # Configuration with validation
│   │   ├── database.py             # PostgreSQL connection
│   │   ├── security.py             # Password & JWT handling
│   │   ├── dependencies.py         # FastAPI dependency injection
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── rate_limit.py           # Rate limiting
│   │   └── redis_client.py         # Redis client
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── user.py                 # User model
│   │   ├── role.py                 # Role & Permission models
│   │   ├── refresh_token.py        # Token tracking
│   │   ├── audit_log.py            # Audit trail
│   │   └── password_reset.py       # Password reset flow
│   ├── routes/                      # API endpoints
│   │   ├── auth.py                 # Auth routes
│   │   ├── users.py                # User management
│   │   └── roles.py                # Role management
│   ├── schemas/                     # Pydantic models
│   │   ├── auth.py                 # Auth schemas
│   │   ├── user.py                 # User schemas
│   │   ├── role.py                 # Role schemas
│   │   └── responce.py             # Response models
│   ├── services/                    # Business logic
│   │   ├── auth_servics.py         # Auth service
│   │   ├── user_servics.py         # User service
│   │   ├── token_servics.py        # Token service
│   │   └── email_servics.py        # Email service
│   ├── middleware/                  # HTTP middleware
│   │   └── security.py             # Security headers
│   └── main.py                      # FastAPI app
├── docs/                            # Comprehensive documentation
│   ├── README.md                   # Getting started guide
│   ├── architecture/               # System design
│   │   └── ARCHITECTURE.md        # Diagrams & design
│   ├── integration/                # Integration patterns
│   │   └── INTEGRATION_GUIDE.md   # Multi-project integration
│   ├── api/                        # API documentation
│   │   └── API_REFERENCE.md       # Complete API docs
│   └── examples/                   # Code examples
│       └── python_integration.md   # Python examples
├── tests/                          # Test suite
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker build
├── docker-compose.yml              # Docker Compose setup
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Docker (optional)

### 2. Installation

```bash
# Clone repository
git clone <repo-url>
cd Authentication\ and\ Authorization

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# !! Important: Set SECRET_KEY, DB_PASSWORD, MAIL_PASSWORD, ALLOWED_ORIGINS !!
```

### 3. Database Setup

```bash
# Create database
createdb auth_db

# Run migrations
alembic upgrade head
```

### 4. Start Server

```bash
# Development
uvicorn app.main:app --reload

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### 5. Access API

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API: http://localhost:8000/api/v1

## 🐳 Docker Setup

### Using Docker Compose (Easiest)

```bash
# Build and run everything
docker-compose up -d

# Access
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Manual Docker

```bash
# Build image
docker build -t auth-module:1.0 .

# Run container
docker run -d -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e DB_HOST=postgres \
  -e REDIS_URL=redis://redis:6379 \
  auth-module:1.0
```

## 📚 Documentation

Comprehensive documentation is in the `docs/` folder:

1. **[Getting Started Guide](docs/README.md)** - Setup and basic usage
2. **[Architecture Guide](docs/architecture/ARCHITECTURE.md)** - System design with diagrams
3. **[Integration Guide](docs/integration/INTEGRATION_GUIDE.md)** - Use in multiple projects
4. **[API Reference](docs/api/API_REFERENCE.md)** - Complete endpoint documentation
5. **[Python Examples](docs/examples/python_integration.md)** - Code examples

### Quick Links

- How to use as **standalone microservice**: [Integration Guide](docs/integration/INTEGRATION_GUIDE.md#option-1-standalone-microservice)
- How to **embed in FastAPI**: [Integration Guide](docs/integration/INTEGRATION_GUIDE.md#option-2-embedded-in-fastapi)
- How to use in **Django**: [Integration Guide](docs/integration/INTEGRATION_GUIDE.md#django)
- How to use in **Node.js/Express**: [Integration Guide](docs/integration/INTEGRATION_GUIDE.md#nodejs--express)
- How to use in **React**: [Integration Guide](docs/integration/INTEGRATION_GUIDE.md#react)

## 🔐 Security Features

### Password Security
- ✅ Argon2 hashing (resistant to GPU attacks)
- ✅ Minimum 12 characters with mixed case, digits, special chars
- ✅ Automatic password rehashing on login
- ✅ Password reset with time-limited tokens

### Session Security
- ✅ HTTP-only cookies (XSS protection)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=Strict (CSRF protection)
- ✅ Device tracking per session
- ✅ Per-device token revocation

### API Security
- ✅ Rate limiting (Redis + in-memory fallback)
- ✅ JWT token with unique JTI
- ✅ Token blacklist support
- ✅ Account lockout after failed attempts
- ✅ Audit logging of all events

### Infrastructure Security
- ✅ Content Security Policy (CSP) headers
- ✅ X-Frame-Options: DENY
- ✅ HSTS headers (force HTTPS)
- ✅ Secure database SSL/TLS
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention

## 📊 Configuration

All configuration via environment variables (`.env` file):

```env
# Application
SECRET_KEY=your-very-secure-secret-key-min-32-chars
APP_ENV=production
DEBUG=false

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_SSL_MODE=require

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@example.com

# CORS & Frontend
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Security (leave defaults for security)
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test
pytest tests/test_auth.py::test_register -v
```

## 📈 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Current user
- `GET /api/v1/auth/verify-email/{token}` - Verify email
- `POST /api/v1/auth/password-reset-request` - Request password reset
- `POST /api/v1/auth/password-reset-confirm` - Confirm password reset

### User Management
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `POST /api/v1/users/{id}/password-change` - Change password
- `POST /api/v1/users/{id}/roles` - Assign role
- `DELETE /api/v1/users/{id}/roles/{role_id}` - Remove role

### Role Management
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role
- `PUT /api/v1/roles/{id}` - Update role
- `DELETE /api/v1/roles/{id}` - Delete role

See [API Reference](docs/api/API_REFERENCE.md) for complete documentation.

## 🏗️ Architecture

The system is built with:

```
┌─────────────────────────────────────────────┐
│         FastAPI Application Layer           │
├─────────────────────────────────────────────┤
│  Routes → Schemas → Services → Database    │
├─────────────────────────────────────────────┤
│  Middleware (Security, CORS, Logging)      │
├─────────────────────────────────────────────┤
│         PostgreSQL Database + Redis        │
└─────────────────────────────────────────────┘
```

Key design patterns:
- **Dependency Injection** - FastAPI Depends()
- **Service Layer** - Business logic separation
- **Repository Pattern** - Database access
- **DTO Pattern** - Pydantic schemas
- **Middleware** - Cross-cutting concerns

See [Architecture Guide](docs/architecture/ARCHITECTURE.md) for detailed diagrams.

## 🔄 Deployment Options

### Option 1: Docker Compose (Development/Small Scale)
```bash
docker-compose up -d
```

### Option 2: Single Server (Production)
```bash
docker build -t auth-module:latest .
docker run -d -p 8000:8000 auth-module:latest
```

### Option 3: Kubernetes (Enterprise)
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Option 4: Cloud Platforms
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

See [Integration Guide](docs/integration/INTEGRATION_GUIDE.md) for deployment details.

## 🛠️ Development

### Project Structure
- Follows FastAPI best practices
- Clean separation of concerns
- Type hints throughout
- Comprehensive error handling
- Extensive documentation

### Adding New Features

1. Create model in `app/models/`
2. Create schema in `app/schemas/`
3. Create service in `app/services/`
4. Create routes in `app/routes/`
5. Add tests in `tests/`

### Code Style
- Use type hints everywhere
- Follow PEP 8
- 100 line maximum
- Docstrings for all functions
- Comprehensive error messages

## 🐛 Troubleshooting

### Database Connection Error
```
Check:
1. PostgreSQL is running: psql --version
2. Database exists: createdb auth_db
3. Credentials in .env are correct
4. DB_HOST is accessible
```

### Redis Connection Error
```
Check:
1. Redis is running: redis-cli ping
2. REDIS_URL in .env is correct
3. Redis port 6379 is accessible
```

### Email Sending Failed
```
Check:
1. MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in .env
2. Gmail: Enable "Less secure apps" or use App Password
3. Network: Port 587 open for SMTP
4. Check logs for error details
```

See [Troubleshooting Guide](docs/integration/TROUBLESHOOTING.md) for more issues.

## 📞 Support & Contribution

### Getting Help
1. Check [Documentation](docs/README.md)
2. Review [API Reference](docs/api/API_REFERENCE.md)
3. Search existing issues
4. Open new issue with details

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This module is provided under the MIT License - see LICENSE file for details.

## 🎓 Learning Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/advanced/security/)
- [Argon2 Password Hashing](https://password-hashing.info/)


