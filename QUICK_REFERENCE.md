# Quick Reference Guide

Fast lookup for common tasks and configurations.

## Environment Variables Cheat Sheet

```env
# 🔐 Critical (MUST configure)
SECRET_KEY=your-32-character-minimum-secret-key-here
DB_HOST=localhost
DB_PASSWORD=your-secure-password
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# 🛠️ Common (usually configure)
APP_ENV=production
DB_NAME=auth_db
DB_USER=postgres
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.gmail.com
FRONTEND_URL=http://localhost:3000

# ⚙️ Optional (use defaults if uncertain)
DEBUG=false
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=INFO
```

## Common Commands

```bash
# Start development
uvicorn app.main:app --reload

# Start production (with gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app

# Run specific test
pytest tests/test_auth.py::test_login -v

# Format code
black app/

# Check linting
flake8 app/

# Docker build
docker build -t auth-module:latest .

# Docker run
docker run -d -p 8000:8000 auth-module:latest

# Docker Compose
docker-compose up -d
docker-compose down
docker-compose logs -f
```

## API Endpoints Quick Reference

```bash
# Authentication
POST   /api/v1/auth/register              # Register
POST   /api/v1/auth/login                 # Login
POST   /api/v1/auth/logout                # Logout
POST   /api/v1/auth/refresh               # Refresh token
GET    /api/v1/auth/me                    # Current user
GET    /api/v1/auth/verify-email/{token}  # Verify email

# User Management
GET    /api/v1/users                      # List users
GET    /api/v1/users/{id}                 # Get user
PUT    /api/v1/users/{id}                 # Update user
POST   /api/v1/users/{id}/password-change # Change password
POST   /api/v1/users/{id}/roles           # Assign role
DELETE /api/v1/users/{id}/roles/{role_id} # Remove role

# Role Management
GET    /api/v1/roles                      # List roles
POST   /api/v1/roles                      # Create role
PUT    /api/v1/roles/{id}                 # Update role
DELETE /api/v1/roles/{id}                 # Delete role
```

## Code Usage Examples

### Using in FastAPI Endpoint

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user
from app.models.user import User
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # current_user is now available
    return {"message": f"Hello {current_user.username}"}
```

### Using Services

```python
from app.services.user_servics import UserService
from app.core.database import get_db
from sqlalchemy.orm import Session

db = next(get_db())
user_service = UserService(db)

# Get user
user = user_service.get_user_by_email("user@example.com")

# Update profile
user_service.update_user_profile(user, full_name="John Doe")

# Change password
user_service.change_password(user, "old_pass", "new_pass")
```

### Using Security Functions

```python
from app.core.security import (
    hash_password, verify_password, 
    create_access_token, decode_token
)

# Password
hashed = hash_password("MyPassword123!")
is_valid = verify_password("MyPassword123!", hashed)

# Tokens
token_data = {"sub": "username", "user_id": 1}
token = create_access_token(token_data)
payload = decode_token(token)
```

## Database Queries

### Get User by Email

```python
from app.models.user import User

user = db.query(User).filter(User.email == "user@example.com").first()
```

### Get All Roles for User

```python
user = db.query(User).filter(User.id == 1).first()
roles = [ur.role.name for ur in user.roles]
```

### Get Users with Admin Role

```python
from app.models.user import User, UserRole
from app.models.role import Role

admins = db.query(User).join(UserRole).join(Role).filter(
    Role.name == "admin"
).all()
```

### List Active Users (Not Deleted)

```python
from app.models.user import User, UserStatus

users = db.query(User).filter(
    User.status != UserStatus.DELETED
).all()
```

## Rate Limiting

```python
from fastapi import APIRouter
from app.core.rate_limit import rate_limit

router = APIRouter()

@router.post("/expensive-operation")
@rate_limit(requests=5, period=60)  # 5 requests per 60 seconds
async def expensive_operation():
    return {"status": "done"}
```

## File Locations Reference

| Task | File Location |
|------|---|
| Configure settings | `.env` |
| Add new route | `app/routes/{feature}.py` |
| Add new model | `app/models/{model}.py` |
| Add new schema | `app/schemas/{schema}.py` |
| Add business logic | `app/services/{feature}_servics.py` |
| Add custom exception | `app/core/exceptions.py` |
| Add middleware | `app/middleware/{name}.py` |
| Add utility function | `app/utils/{function}.py` |
| Run migrations | `alembic/` |
| Write tests | `tests/test_{feature}.py` |

## Debugging Tips

### Enable SQL Logging

```python
# In config.py
DB_ECHO=true
```

### View Generated SQL

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    print(statement)
```

### Debug Token Issues

```python
from app.core.security import decode_token
import logging

logging.basicConfig(level=logging.DEBUG)

token = "your_token_here"
payload = decode_token(token)
print(payload)  # See token contents
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token in Authorization header |
| 422 Unprocessable Entity | Check request body format |
| 429 Too Many Requests | Wait or change rate limit |
| Database connection error | Check DB_HOST, DB_PASSWORD, database exists |
| Redis connection error | Check REDIS_URL, Redis is running |
| Email not sending | Check MAIL_* settings, SMTP credentials |
| Token expiry issues | Check ACCESS_TOKEN_EXPIRE_MINUTES |
| CORS errors | Check ALLOWED_ORIGINS in .env |

## Performance Tuning

### Database

```python
# Increase connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Use indexes (auto-created)
# Check query performance with DB_ECHO=true
```

### Rate Limiting

```python
# Adjust limits in routes
@rate_limit(requests=100, period=60)  # 100 per minute

# Use Redis for distributed systems
REDIS_URL=redis://your-redis-server:6379
```

### Caching

```python
# Cache user lookups (custom implementation)
# Cache role/permission checks (custom implementation)
```

## Security Best Practices

✅ Always use HTTPS in production
✅ Keep SECRET_KEY secure (never commit to git)
✅ Use strong passwords for DB and email
✅ Regularly update dependencies
✅ Monitor audit logs
✅ Enable rate limiting
✅ Configure CORS properly
✅ Use environment variables for secrets

## Testing Endpoints

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePass123!"

# Protected endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python Requests

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Register
resp = requests.post(f"{base_url}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
})
print(resp.json())

# Login
resp = requests.post(f"{base_url}/auth/login", data={
    "username": "testuser",
    "password": "SecurePass123!"
})
token = resp.json()["access_token"]

# Protected endpoint
resp = requests.get(
    f"{base_url}/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
print(resp.json())
```

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [JWT Info](https://jwt.io/)
- [OWASP Security](https://owasp.org/)
- [Argon2](https://password-hashing.info/)

---

**For detailed information, see the full documentation in `docs/` folder.**
