# Integration Guide

Learn how to integrate this authentication module into your projects in different ways.

## Table of Contents

1. [Option 1: Standalone Microservice](#option-1-standalone-microservice)
2. [Option 2: Embedded in FastAPI](#option-2-embedded-in-fastapi)
3. [Option 3: Python Package](#option-3-python-package)
4. [Option 4: Docker Container](#option-4-docker-container)
5. [Integration Patterns by Framework](#integration-patterns-by-framework)

---

## Option 1: Standalone Microservice

### Best For
- Multiple frontend applications
- Microservices architecture
- Centralized authentication
- Different backend technologies

### Setup

1. **Deploy the Auth Module**
```bash
# Clone the module
git clone <auth-module-repo>
cd Authentication\ and\ Authorization

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start service
docker-compose up -d
```

2. **Access the API**
```
Base URL: http://localhost:8000
API Docs: http://localhost:8000/docs
```

3. **Client-Side Integration**

```javascript
// Example: JavaScript/React Client
const API_BASE_URL = "http://localhost:8000/api/v1";

// Register
async function register(username, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
    credentials: "include"  // Important: include cookies
  });
  return response.json();
}

// Login
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    body: new URLSearchParams({ username, password }),
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include"
  });
  const data = await response.json();
  localStorage.setItem("accessToken", data.access_token);
  return data;
}

// API Request with Token
async function apiRequest(endpoint, method = "GET", body = null) {
  const token = localStorage.getItem("accessToken");
  const headers = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
    credentials: "include"
  });

  // Handle token expiry
  if (response.status === 401) {
    const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include"
    });
    const refreshData = await refreshResponse.json();
    localStorage.setItem("accessToken", refreshData.access_token);
    
    // Retry original request
    return apiRequest(endpoint, method, body);
  }

  return response.json();
}
```

### Docker Compose for Multiple Services

```yaml
version: '3.8'

services:
  # Auth Service
  auth-service:
    image: auth-module:latest
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DB_HOST=postgres
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - microservices

  # Your Other Services
  api-service:
    image: your-api:latest
    ports:
      - "8001:8000"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:8000
    depends_on:
      - auth-service
    networks:
      - microservices

  # Shared Database
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=microservices
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    networks:
      - microservices

  # Shared Cache
  redis:
    image: redis:7
    networks:
      - microservices

volumes:
  postgres_data:

networks:
  microservices:
    driver: bridge
```

---

## Option 2: Embedded in FastAPI

### Best For
- Single monolithic application
- Using FastAPI for your entire application
- Simple deployment

### Setup

1. **Copy Module into Your Project**
```
your-project/
├── auth/                 # Copy the `app` folder here
│   ├── core/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── ...
├── app/
│   ├── main.py
│   └── ...
└── requirements.txt
```

2. **Merge Requirements**
```bash
# Add auth module dependencies to your requirements.txt
cat auth/requirements.txt >> requirements.txt
pip install -r requirements.txt
```

3. **Integrate in Your main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import auth components
from auth.core.config import settings
from auth.core.database import engine, Base, get_db
from auth.middleware.security import SecurityHeadersMiddleware
from auth.routes.auth import router as auth_router
from auth.routes.users import router as users_router
from auth.routes.roles import router as roles_router

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Include auth routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)

# Your other routes
@app.get("/")
async def root():
    return {"message": "Welcome to my app"}
```

4. **Use Auth in Your Routes**
```python
from fastapi import APIRouter, Depends
from auth.core.dependencies import get_current_active_user
from auth.models.user import User

router = APIRouter(prefix="/api/v1", tags=["my-endpoints"])

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    """This endpoint requires authentication"""
    return {
        "message": f"Hello {current_user.username}",
        "user_id": current_user.id
    }

@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """This endpoint requires admin role"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"admin_data": "sensitive"}
```

---

## Option 3: Python Package

### Best For
- Using the module from multiple Python projects
- Sharing code across team

### Setup

1. **Publish to Package Index**

Create `setup.py` in the module:
```python
from setuptools import setup, find_packages

setup(
    name="auth-module",
    version="1.0.0",
    description="Enterprise-grade auth module",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100",
        "sqlalchemy>=2.0",
        "python-jose[cryptography]>=3.3",
        "passlib[bcrypt]>=1.7",
        "redis>=5.0",
        "pydantic-settings>=2.0",
    ],
)
```

2. **Install in Your Projects**
```bash
# From PyPI
pip install auth-module

# Or from local
pip install -e /path/to/auth-module
```

3. **Use in Your Code**
```python
from auth.core.config import settings
from auth.core.security import hash_password, verify_password
from auth.core.database import get_db
from auth.routes.auth import router as auth_router

# Use in your FastAPI app
app.include_router(auth_router)
```

---

## Option 4: Docker Container

### Best For
- Any technology stack
- Language-agnostic integration
- Easy deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t auth-module:1.0 .

# Run container
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e DB_HOST=postgres \
  -e REDIS_URL=redis://redis:6379 \
  auth-module:1.0
```

---

## Integration Patterns by Framework

### Django

```python
# django_app/views.py
import requests

AUTH_SERVICE_URL = "http://localhost:8000/api/v1"

class LoginView(View):
    def post(self, request):
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/login",
            data=request.POST,
            cookies=request.COOKIES
        )
        
        if response.status_code == 200:
            data = response.json()
            # Store token in session
            request.session['access_token'] = data['access_token']
            return JsonResponse({"success": True})
        
        return JsonResponse(
            {"error": response.json()},
            status=response.status_code
        )

# Middleware to attach auth token
def attach_auth_token(request):
    if 'access_token' in request.session:
        request.headers['Authorization'] = f"Bearer {request.session['access_token']}"
```

### Flask

```python
from flask import Flask, request, jsonify
import requests
from functools import wraps

app = Flask(__name__)
AUTH_SERVICE_URL = "http://localhost:8000/api/v1"

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return {"error": "No token"}, 401
        
        # Validate token with auth service
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            return {"error": "Invalid token"}, 401
        
        # Attach user to request
        request.user = response.json()
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/protected')
@require_auth
def protected():
    return {"user": request.user}
```

### Node.js / Express

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
const AUTH_SERVICE_URL = "http://localhost:8000/api/v1";

// Middleware
async function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: "No token" });
  }
  
  try {
    const response = await axios.get(`${AUTH_SERVICE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    req.user = response.data;
    next();
  } catch (error) {
    res.status(401).json({ error: "Invalid token" });
  }
}

app.get('/protected', authMiddleware, (req, res) => {
  res.json({ user: req.user });
});
```

### React

```javascript
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if already logged in
    fetchCurrentUser();
  }, []);

  async function fetchCurrentUser() {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        credentials: 'include'
      });
      if (response.ok) {
        setUser(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  }

  async function login(username, password) {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('accessToken', data.access_token);
      setUser(data.user);
      return true;
    }
    return false;
  }

  async function logout() {
    await fetch('http://localhost:8000/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
    localStorage.removeItem('accessToken');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
```

---

## Network Configuration

### CORS Setup

For multiple frontend domains:

```python
# app/core/config.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Local development
    "https://app.example.com",    # Production app
    "https://admin.example.com",  # Admin panel
    "https://mobile.example.com"  # Mobile web
]
```

### API Gateway / Reverse Proxy

Using Nginx:

```nginx
upstream auth_service {
    server auth:8000;
}

upstream api_service {
    server api:8000;
}

server {
    listen 80;
    server_name *.example.com;

    # Auth service
    location /api/v1/auth {
        proxy_pass http://auth_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API service (requires auth)
    location /api/v1 {
        auth_request /api/v1/auth/me;
        proxy_pass http://api_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Troubleshooting Integration

### CORS Issues

```javascript
// Client side - use credentials
fetch(url, {
  credentials: 'include'  // Important!
})
```

### Token Not Persisting

```javascript
// Ensure localStorage is available
if (typeof window !== 'undefined') {
  localStorage.setItem('token', token);
}
```

### Refresh Token Loop

```python
# Prevent infinite loops with proper error handling
if response.status == 401:
    # Clear local token and redirect to login
    localStorage.removeItem('accessToken')
    redirect('/login')
```

---

## Production Checklist

- [ ] Use HTTPS/TLS for all connections
- [ ] Configure proper ALLOWED_ORIGINS
- [ ] Set strong SECRET_KEY (min 32 chars)
- [ ] Use secure database credentials
- [ ] Enable database SSL mode
- [ ] Configure Redis with password
- [ ] Set up email server credentials
- [ ] Enable audit logging
- [ ] Configure rate limiting appropriate for your use case
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Implement rate limiting at API gateway level too

---

See [Architecture](../architecture/ARCHITECTURE.md) for deployment options.
