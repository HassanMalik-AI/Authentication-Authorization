# Authentication & Authorization Module Documentation

Welcome to the **Enterprise-Grade Authentication & Authorization Module** - a production-ready, reusable module for secure user authentication and authorization.

## 📋 Quick Start

### What's Included

✅ **User Authentication**
- Registration with email verification
- Login/Logout with session management
- Multi-device session tracking
- Account lockout protection (after 5 failed attempts)
- Automatic password rehashing

✅ **Token Management**
- JWT-based access tokens (15-minute expiry)
- Long-lived refresh tokens (7-day expiry)
- Token revocation and blacklisting
- Device-based token management

✅ **Security Features**
- Argon2 password hashing (industry-standard)
- Two-Factor Authentication (MFA) ready
- Rate limiting (Redis + in-memory fallback)
- Secure headers (CSP, HSTS, X-Frame-Options, etc.)
- Row-level security (RLS) for multi-tenancy
- Audit logging of all auth events

✅ **Role-Based Access Control (RBAC)**
- Role management
- Permission management
- Role-permission assignments
- User-role assignments
- Role hierarchy support

✅ **Advanced Features**
- Password reset workflow
- Email verification
- Login alerts
- Account suspension/deletion
- Multi-tenant support
- Comprehensive audit trail

## 📂 Project Structure

```
Authentication and Authorization/
├── app/
│   ├── core/                 # Core authentication logic
│   │   ├── config.py        # Configuration (environment variables)
│   │   ├── database.py      # Database connection setup
│   │   ├── security.py      # Password hashing, JWT tokens, encryption
│   │   ├── dependencies.py  # FastAPI dependency injection
│   │   ├── exceptions.py    # Custom exception classes
│   │   ├── rate_limit.py    # Rate limiting (Redis + fallback)
│   │   └── redis_client.py  # Redis client wrapper
│   ├── middleware/           # HTTP middleware
│   │   ├── security.py      # Security headers
│   │   ├── logging.py       # Request/response logging
│   │   └── cors.py          # CORS configuration
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User model with validation
│   │   ├── role.py          # Role & Permission models
│   │   ├── audit_log.py     # Audit trail logging
│   │   ├── refresh_token.py # Refresh token tracking
│   │   └── password_reset.py# Password reset tokens
│   ├── routes/              # API endpoints
│   │   ├── auth.py          # Auth routes (login, register, etc)
│   │   ├── users.py         # User management routes
│   │   ├── roles.py         # Role management routes
│   │   └── admin/           # Admin endpoints
│   ├── schemas/             # Pydantic request/response models
│   │   ├── auth.py          # Auth schemas (UserCreate, Token, etc)
│   │   ├── user.py          # User schemas
│   │   ├── role.py          # Role schemas
│   │   └── responce.py      # Generic response models
│   ├── services/            # Business logic layer
│   │   ├── auth_servics.py  # Authentication logic
│   │   ├── user_servics.py  # User management logic
│   │   ├── token_servics.py # Token management logic
│   │   └── email_servics.py # Email sending (verification, password reset)
│   └── utils/               # Utility functions
│       ├── decorators.py    # Custom decorators
│       ├── validators.py    # Data validators
│       └── formatters.py    # Data formatters
├── docs/                     # Documentation (this folder)
│   ├── architecture/        # System architecture diagrams
│   ├── integration/         # Integration guides for multiple projects
│   ├── api/                 # API documentation
│   └── examples/            # Code examples
├── tests/                   # Unit & integration tests
├── migrations/              # Database migrations (Alembic)
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker container configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md               # Main README

```

## 🚀 Getting Started

### 1. Installation

```bash
# Clone the repository
git clone <repo-url>
cd Authentication\ and\ Authorization

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### 2. Configuration

Edit `.env` file with your settings:

```env
# Essential
SECRET_KEY=your-very-secure-secret-key-min-32-chars
APP_ENV=production

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
MAIL_FROM=noreply@your-domain.com

# Frontend
FRONTEND_URL=http://localhost:3000

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

### 3. Database Setup

```bash
# Create database
createdb auth_db

# Run migrations
alembic upgrade head
```

### 4. Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access API
curl http://localhost:8000/api/v1/docs
```

## 📚 Core Concepts

### Authentication Flow

```
User Registration
    ↓
Email Verification
    ↓
Login (username + password)
    ↓
Generate Tokens (access + refresh)
    ↓
Set Cookies (refresh token)
    ↓
Authenticated User Session
    ↓
Token Expiry → Use Refresh Token to Get New Access Token
    ↓
Logout → Revoke All Tokens
```

### Token Types

- **Access Token**: Short-lived (15 min), used for API requests
- **Refresh Token**: Long-lived (7 days), stored in HTTP-only cookies, used to get new access tokens
- **Password Reset Token**: 1-hour validity, for password reset flow
- **Email Verification Token**: 24-hour validity, for email verification

### Security Layers

1. **Network Layer**: HTTPS/TLS, HSTS, secure cookies
2. **Header Layer**: CSP, X-Frame-Options, X-XSS-Protection
3. **Authentication Layer**: Argon2 password hashing, JWT tokens
4. **Authorization Layer**: RBAC, permission checks
5. **Data Layer**: SQL injection prevention, row-level security
6. **Application Layer**: Rate limiting, audit logging, input validation

## 🔐 Security Features

### Password Security
- Argon2 hashing (industry standard, resistant to GPU attacks)
- Minimum 12 characters with uppercase, lowercase, digits, special chars
- Automatic rehashing on login if algorithm upgraded
- Password change history not enforced (can be added)

### Session Security
- HTTP-only cookies (XSS protection)
- Secure flag (HTTPS only)
- SameSite=Strict (CSRF protection)
- Device tracking per session
- Per-device token revocation

### Rate Limiting
- Distributed rate limiting with Redis
- Fallback in-memory rate limiter if Redis unavailable
- Per-IP and per-endpoint rate limits
- Configurable requests per time period

### Audit Logging
- All auth events logged (login, logout, registration, password change, etc.)
- IP address and user agent tracking
- Failed attempt logging
- Admin access logging

## 🔄 Integration with Multiple Projects

See [Integration Guide](./integration/INTEGRATION_GUIDE.md) for:
- Using as a standalone microservice
- Embedding in existing FastAPI projects
- Using as a package/library
- Docker containerization
- Kubernetes deployment

## 📖 API Documentation

See [API Reference](./api/API_REFERENCE.md) for complete endpoint documentation.

## 🏗️ Architecture

See [Architecture Diagrams](./architecture/ARCHITECTURE.md) for:
- Component diagram
- Data flow diagrams
- Sequence diagrams
- Deployment options

## 💡 Examples

- [Python Integration](./examples/python_integration.md)
- [JavaScript/Node.js Integration](./examples/nodejs_integration.md)
- [React Integration](./examples/react_integration.md)
- [Docker Setup](./examples/docker_setup.md)

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

## 📝 Database Schema

See [Database Schema](./api/DATABASE_SCHEMA.md) for:
- Table structures
- Relationships
- Indexes
- Row-level security policies

## ⚙️ Configuration Reference

See [Configuration Guide](./api/CONFIGURATION.md) for:
- All environment variables
- Security settings
- Database configuration
- Email setup
- Redis configuration

## 🐛 Troubleshooting

Common issues and solutions:
- Database connection errors
- Redis connection failures
- Email sending failures
- Token validation errors
- Rate limiting issues

See [Troubleshooting Guide](./integration/TROUBLESHOOTING.md)

## 📞 Support

For issues, questions, or contributions:
1. Check the documentation
2. Review existing issues
3. Open a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

## 📄 License

This module is provided as-is for use in your projects.

## 🎯 Next Steps

1. ✅ Review [Architecture Diagrams](./architecture/ARCHITECTURE.md)
2. ✅ Read [API Reference](./api/API_REFERENCE.md)
3. ✅ Choose [Integration Pattern](./integration/INTEGRATION_GUIDE.md)
4. ✅ Follow [Example Implementation](./examples/)
5. ✅ Deploy using [Docker](./examples/docker_setup.md) or [Kubernetes](./examples/kubernetes_setup.md)

---

**Happy authenticating! 🔐**
