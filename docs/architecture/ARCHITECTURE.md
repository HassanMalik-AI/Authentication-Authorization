# System Architecture

## Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile App]
        SDK[3rd Party SDK]
    end
    
    subgraph "API Gateway / Load Balancer"
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        API[FastAPI Application]
        ROUTE[Route Handlers]
        MIDDLEWARE[Middleware]
    end
    
    subgraph "Business Logic Layer"
        AUTH_SVC[AuthService]
        USER_SVC[UserService]
        TOKEN_SVC[TokenService]
        EMAIL_SVC[EmailService]
    end
    
    subgraph "Security & Validation"
        SECURITY[Security Module]
        RATE_LIMIT[Rate Limiter]
        DEPENDS[Dependencies]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "External Services"
        SMTP[SMTP Server]
        ANALYTICS[Analytics]
    end
    
    WEB -->|HTTP/S| LB
    MOBILE -->|HTTP/S| LB
    SDK -->|HTTP/S| LB
    
    LB --> API
    API --> MIDDLEWARE
    MIDDLEWARE --> ROUTE
    ROUTE --> DEPENDS
    DEPENDS --> AUTH_SVC
    DEPENDS --> USER_SVC
    DEPENDS --> TOKEN_SVC
    
    AUTH_SVC --> SECURITY
    AUTH_SVC --> RATE_LIMIT
    AUTH_SVC --> DB
    AUTH_SVC --> REDIS
    
    USER_SVC --> DB
    TOKEN_SVC --> DB
    TOKEN_SVC --> REDIS
    
    EMAIL_SVC --> SMTP
    
    RATE_LIMIT --> REDIS
    SECURITY --> DB
```

## Authentication Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Client as Client/Browser
    participant API as Auth API
    participant DB as Database
    participant Redis as Redis
    participant Email as Email Service
    
    User->>Client: 1. Enter Credentials
    Client->>API: 2. POST /register
    API->>DB: 3. Check if user exists
    DB-->>API: User not found
    API->>API: 4. Hash password (Argon2)
    API->>DB: 5. Create user account
    DB-->>API: User created
    API->>API: 6. Generate verification token
    API->>Email: 7. Send verification email
    Email-->>User: Email with verification link
    
    User->>Email: 8. Click verification link
    User->>Client: 9. Login with credentials
    Client->>API: 10. POST /login
    API->>DB: 11. Find user by username
    DB-->>API: User found
    API->>API: 12. Verify password
    API->>API: 13. Create access token (15 min)
    API->>API: 14. Create refresh token (7 days)
    API->>DB: 15. Store refresh token
    DB-->>API: Token stored
    API->>API: 16. Generate session cookie
    Client-->>API: 17. Receive tokens + cookie
    
    Client->>API: 18. POST /api/data (with access token)
    API->>API: 19. Validate JWT token
    API->>DB: 20. Check token blacklist
    API-->>Client: 21. Request authorized
    
    Note over User,Email: Token Expiry
    Client->>API: 22. POST /refresh (with refresh token)
    API->>DB: 23. Find stored refresh token
    DB-->>API: Token found and valid
    API->>API: 24. Create new access token
    API->>Redis: 25. Revoke old refresh token
    Client-->>API: 26. New tokens issued
    
    Client->>API: 27. POST /logout
    API->>DB: 28. Revoke refresh token
    DB-->>API: Token revoked
    Client-->>API: 29. Cookie cleared
```

## Authorization & Role Flow

```mermaid
graph LR
    USER[User]
    ROLE1[Role: Admin]
    ROLE2[Role: Moderator]
    PERM1["Permission: users.read"]
    PERM2["Permission: users.write"]
    PERM3["Permission: users.delete"]
    PERM4["Permission: posts.moderate"]
    
    USER -->|has| ROLE1
    USER -->|has| ROLE2
    
    ROLE1 -->|grants| PERM1
    ROLE1 -->|grants| PERM2
    ROLE1 -->|grants| PERM3
    
    ROLE2 -->|grants| PERM1
    ROLE2 -->|grants| PERM4
    
    PERM1 -->|allows| READ["Read Users"]
    PERM2 -->|allows| WRITE["Create/Update Users"]
    PERM3 -->|allows| DELETE["Delete Users"]
    PERM4 -->|allows| MOD["Moderate Posts"]
```

## Rate Limiting Architecture

```mermaid
graph TB
    REQUEST[Incoming Request]
    
    REQUEST -->|Check| REDIS_CHECK{Redis Available?}
    
    REDIS_CHECK -->|Yes| REDIS["Redis Rate Limiter"]
    REDIS_CHECK -->|No| MEMORY["In-Memory Limiter<br/>(Thread-safe)"]
    
    REDIS -->|Get Key| REDIS_DB[(Redis DB)]
    REDIS_DB -->|Count| REDIS_LIMIT{Within Limit?}
    
    MEMORY -->|Thread Lock| MEMORY_DICT["Dictionary<br/>User → Count"]
    MEMORY_DICT -->|Check| MEMORY_LIMIT{Within Limit?}
    
    REDIS_LIMIT -->|Yes| ALLOW[✅ Allow Request]
    REDIS_LIMIT -->|No| DENY[❌ Reject - 429]
    
    MEMORY_LIMIT -->|Yes| ALLOW
    MEMORY_LIMIT -->|No| DENY
    
    ALLOW --> ROUTE[Route Handler]
    DENY --> ERROR[Return Error]
```

## Database Schema Overview

```mermaid
erDiagram
    USERS ||--o{ REFRESH_TOKENS : creates
    USERS ||--o{ PASSWORD_RESET : requests
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ USER_ROLES : has
    USERS ||--o{ USER_PERMISSIONS : has
    
    USER_ROLES }o--|| ROLES : assigns
    ROLES ||--o{ ROLE_PERMISSIONS : has
    ROLE_PERMISSIONS }o--|| PERMISSIONS : grants
    USER_PERMISSIONS }o--|| PERMISSIONS : grants
    
    USERS {
        int id PK
        string username UK
        string email UK
        text hashed_password
        string status
        boolean is_active
        boolean is_mfa_enabled
        text mfa_secret
        json mfa_recovery_codes
        int failed_login_attempts
        datetime locked_until
        datetime last_login_at
        string last_login_ip
        datetime created_at
        datetime updated_at
    }
    
    REFRESH_TOKENS {
        int id PK
        int user_id FK
        text token
        datetime expires_at
        boolean is_revoked
        datetime revoked_at
        string device_name
        string ip_address
        text user_agent
    }
    
    ROLES {
        int id PK
        string name UK
        text description
        datetime created_at
    }
    
    PERMISSIONS {
        int id PK
        string name UK
        text description
    }
    
    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        text description
        json metadata
        string ip_address
        datetime created_at
    }
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│ 1. NETWORK LAYER                                             │
│ ├─ HTTPS/TLS Encryption (in transit)                       │
│ ├─ HSTS Headers (force HTTPS)                              │
│ └─ Certificate Pinning (optional)                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. HTTP HEADER LAYER                                         │
│ ├─ Content-Security-Policy (prevent XSS)                   │
│ ├─ X-Frame-Options: DENY (prevent clickjacking)            │
│ ├─ X-Content-Type-Options: nosniff                         │
│ ├─ Referrer-Policy: strict-origin-when-cross-origin        │
│ └─ Permissions-Policy (restrict browser features)           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. AUTHENTICATION LAYER                                      │
│ ├─ Argon2 Password Hashing                                 │
│ ├─ Secure Password Requirements                            │
│ ├─ Account Lockout (5 failed attempts)                     │
│ ├─ JWT Token with JTI (unique ID)                          │
│ └─ Token Expiration & Refresh                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. AUTHORIZATION LAYER                                       │
│ ├─ Role-Based Access Control (RBAC)                        │
│ ├─ Permission-Based Access Control                         │
│ ├─ Scope-based access                                       │
│ └─ Resource-level permissions                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. DATA LAYER                                                │
│ ├─ SQL Injection Prevention (parameterized queries)        │
│ ├─ Row-Level Security (RLS)                                │
│ ├─ Column-level encryption (sensitive data)                │
│ ├─ Database-level SSL/TLS                                  │
│ └─ Audit Trail (all changes logged)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. APPLICATION LAYER                                         │
│ ├─ Rate Limiting (per IP, per endpoint)                    │
│ ├─ Input Validation (Pydantic models)                      │
│ ├─ CORS Policy                                             │
│ ├─ Logging & Monitoring                                    │
│ └─ Error Handling (no sensitive data leaks)                │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Single Server
```
┌─────────────────────────────────────┐
│         Single Server               │
├─────────────────────────────────────┤
│  Docker Container                   │
│  ├─ FastAPI App                     │
│  ├─ PostgreSQL                      │
│  └─ Redis                           │
└─────────────────────────────────────┘
```

### Microservices
```
┌──────────────────────────────────────────────────────────┐
│  API Gateway (Load Balancer)                             │
└───────────┬────────────────────────────┬────────────────┘
            │                            │
     ┌──────▼───────┐         ┌──────────▼────────┐
     │Auth Service  │         │User Service       │
     │Container 1   │         │Container 2        │
     └──────┬───────┘         └──────────┬────────┘
            │                            │
            └──────────────┬─────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
      ┌─────▼──┐    ┌─────▼──┐    ┌─────▼──┐
      │PostgreSQL  │    │ Redis │    │ Kafka │
      │  Shared    │    │       │    │       │
      └──────────┘    └───────┘    └───────┘
```

### Kubernetes
```
┌────────────────────────────────────────────────┐
│  Kubernetes Cluster                            │
├────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐ │
│  │ Ingress Controller                       │ │
│  └───────────────┬──────────────────────────┘ │
│                  │                            │
│  ┌───────────────▼──────────────────────────┐ │
│  │ Service: auth-service                    │ │
│  └───────────────┬──────────────────────────┘ │
│                  │                            │
│  ┌───────────────▼────────────┐              │
│  │ Deployment: auth-app       │              │
│  │ ├─ Replica 1              │              │
│  │ ├─ Replica 2              │              │
│  │ └─ Replica 3              │              │
│  └─────────────────────────────┘             │
│                                              │
│  ┌──────────────────────────────────────────┐ │
│  │ StatefulSet: postgres-db                 │ │
│  └──────────────────────────────────────────┘ │
│                                              │
│  ┌──────────────────────────────────────────┐ │
│  │ StatefulSet: redis-cache                 │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. **Separation of Concerns**
- Routes (API endpoints)
- Services (business logic)
- Models (data objects)
- Schemas (validation & serialization)

### 2. **Security by Default**
- Secure configuration out of the box
- Validation on every input
- Error messages don't leak sensitive info
- Logging for audit trail

### 3. **Scalability**
- Redis for distributed rate limiting
- Stateless API design
- Database connection pooling
- Async/await throughout

### 4. **Maintainability**
- Clear module organization
- Type hints everywhere
- Comprehensive error handling
- Extensive documentation

### 5. **Reusability**
- Can be used as:
  - Standalone microservice
  - Embedded in FastAPI project
  - Python package
  - Docker container

---

See [Integration Guide](../integration/INTEGRATION_GUIDE.md) for deployment options.
