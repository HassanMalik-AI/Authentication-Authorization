# Python Integration Example

Example of how to use the Auth Module from another Python application.

## Option 1: Direct Import (Embedded)

If you've copied the auth module into your project:

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from auth.core.database import get_db
from auth.core.dependencies import get_current_active_user
from auth.models.user import User
from auth.services.user_servics import UserService
from auth.routes.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)

# Your protected endpoints
@app.get("/api/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

@app.post("/api/profile/update")
async def update_profile(
    full_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user_service = UserService(db)
    updated_user = user_service.update_user_profile(
        current_user,
        full_name=full_name
    )
    return {"success": True, "user": updated_user}

@app.get("/api/admin/users")
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_service = UserService(db)
    users = user_service.get_all_users()
    return {"users": users}
```

## Option 2: HTTP Requests (Microservice)

If auth is running as a separate service:

```python
import requests
from typing import Optional, Dict
from fastapi import HTTPException, status

class AuthClient:
    """Client for communicating with Auth Service"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def register(self, username: str, email: str, password: str, **kwargs) -> Dict:
        """Register new user"""
        response = self.session.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                **kwargs
            }
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Registration failed")
            )
    
    def login(self, username: str, password: str) -> Dict:
        """Authenticate user"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    def get_user(self, token: str, user_id: int) -> Dict:
        """Get user details"""
        response = self.session.get(
            f"{self.base_url}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        response = self.session.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token"""
        response = self.session.post(
            f"{self.base_url}/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Refresh token invalid or expired")

# Usage in your application
from fastapi import FastAPI, Depends, Header

app = FastAPI()
auth_client = AuthClient()

@app.post("/register")
async def register(username: str, email: str, password: str):
    """Register endpoint that uses auth service"""
    user = auth_client.register(username, email, password)
    return {"message": "User registered successfully", "user_id": user["id"]}

@app.post("/login")
async def login(username: str, password: str):
    """Login endpoint"""
    result = auth_client.login(username, password)
    return result

async def get_current_user(authorization: str = Header(...)):
    """Dependency to get current user from token"""
    token = authorization.replace("Bearer ", "")
    user = auth_client.validate_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user

@app.get("/protected")
async def protected_endpoint(current_user: Dict = Depends(get_current_user)):
    """Protected endpoint"""
    return {"message": f"Hello {current_user['username']}"}
```

## Option 3: Using JWT Locally

If you want to validate tokens locally without calling the auth service:

```python
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Dict
from app.core.config import settings

class LocalTokenValidator:
    """Validate JWT tokens locally (no external calls)"""
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """Extract user ID from token"""
        payload = LocalTokenValidator.decode_token(token)
        return payload.get("user_id") if payload else None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if token has expired"""
        payload = LocalTokenValidator.decode_token(token)
        if not payload:
            return True
        
        try:
            exp = payload.get("exp")
            return datetime.utcfromtimestamp(exp) < datetime.utcnow()
        except:
            return True

# Usage
validator = LocalTokenValidator()

def get_current_user_id(authorization: str = Header(...)) -> int:
    """Extract user ID from token"""
    token = authorization.replace("Bearer ", "")
    user_id = validator.get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user details (only if user is authenticated)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
```

## Common Patterns

### Pattern 1: Single Sign-On (SSO)

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import secrets

app = FastAPI()
auth_client = AuthClient()

# Store session tokens in cache
session_store = {}

@app.get("/login/callback")
async def login_callback(code: str):
    """Handle OAuth-style login"""
    # Exchange code for tokens with auth service
    tokens = auth_client.exchange_code(code)
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    session_store[session_id] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user": tokens["user"]
    }
    
    # Return session cookie
    response = RedirectResponse("/dashboard")
    response.set_cookie("session_id", session_id, httponly=True)
    return response

@app.get("/dashboard")
async def dashboard(session_id: str = Cookie(None)):
    """Protected page"""
    if not session_id or session_id not in session_store:
        return RedirectResponse("/login")
    
    return {"user": session_store[session_id]["user"]}
```

### Pattern 2: Service-to-Service Auth

```python
import jwt
from datetime import datetime, timedelta

class ServiceAuthenticator:
    """Service-to-service authentication"""
    
    @staticmethod
    def create_service_token(service_name: str, secret_key: str) -> str:
        """Create service token"""
        payload = {
            "service": service_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @staticmethod
    def verify_service_token(token: str, secret_key: str) -> bool:
        """Verify service token"""
        try:
            jwt.decode(token, secret_key, algorithms=["HS256"])
            return True
        except:
            return False

# Service calling another service
service_token = ServiceAuthenticator.create_service_token(
    "my-service",
    "shared-secret"
)

response = requests.get(
    "http://other-service:8000/internal/data",
    headers={"X-Service-Token": service_token}
)
```

### Pattern 3: API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

class APIKeyValidator:
    """Validate API keys"""
    
    def __init__(self):
        self.valid_keys = {
            "api-key-1": "client-1",
            "api-key-2": "client-2"
        }
    
    def validate(self, api_key: str) -> str:
        """Validate and return client name"""
        if api_key not in self.valid_keys:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return self.valid_keys[api_key]

validator = APIKeyValidator()

@app.get("/api/data")
async def get_data(api_key: str = Security(api_key_header)):
    """Get data using API key"""
    client = validator.validate(api_key)
    return {"data": "...", "client": client}
```

---

See [Integration Guide](../integration/INTEGRATION_GUIDE.md) for more patterns.
