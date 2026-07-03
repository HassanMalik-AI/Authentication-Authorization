# API Reference

Complete API documentation for the Authentication & Authorization module.

## Base URL
```
http://localhost:8000/api/v1
```

## Table of Contents
- [Authentication Endpoints](#authentication-endpoints)
- [User Management](#user-management)
- [Role Management](#role-management)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone_number": "+1234567890"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "status": "unverified",
  "is_active": false,
  "is_mfa_enabled": false,
  "created_at": "2024-01-15T10:30:00Z",
  "email_verified_at": null
}
```

**Error Response (400):**
```json
{
  "detail": "Username already taken"
}
```

**Rate Limit:** 5 requests per 60 seconds

---

### POST /auth/login
Authenticate user with credentials.

**Request Body:**
```
Form data:
- username: string (required)
- password: string (required)
```

**Request Headers:**
```
X-Device-Name: iPhone 12  (optional)
User-Agent: Mozilla/5.0...  (automatic)
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "status": "active",
    "is_active": true,
    "is_mfa_enabled": false,
    "is_admin": false
  }
}
```

**Cookies Set:**
- `refresh_token` (HTTP-only, Secure, SameSite=Strict)

**Error Responses:**
```json
// Invalid credentials (401)
{ "detail": "Invalid credentials" }

// Account suspended (403)
{ "detail": "Account suspended. Contact support." }

// Account locked (423)
{ "detail": "Account locked until 2024-01-15T11:00:00. Try again in 30 minutes." }

// Too many attempts (429)
{ "detail": "Rate limit exceeded. Please try again later." }
```

**Rate Limit:** 10 requests per 60 seconds

---

### POST /auth/refresh
Refresh access token using refresh token.

**Request Headers:**
```
Authorization: Bearer <access_token> (optional)
Cookie: refresh_token=<token>  (from login response)
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
```json
// No refresh token (401)
{ "detail": "Refresh token not provided" }

// Expired token (401)
{ "detail": "Refresh token has expired. Please login again" }

// Revoked token (401)
{ "detail": "Refresh token has been revoked" }
```

---

### POST /auth/logout
Logout user and revoke refresh token.

**Request Headers:**
```
Authorization: Bearer <access_token>
Cookie: refresh_token=<token>
```

**Success Response (204):**
No content

**Side Effects:**
- Refresh token revoked in database
- Cookie cleared (refresh_token cookie deleted)

---

### GET /auth/me
Get current authenticated user information.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "avatar_url": "https://...",
  "status": "active",
  "is_active": true,
  "is_admin": false,
  "is_mfa_enabled": false,
  "last_login_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-14T15:45:00Z",
  "email_verified_at": "2024-01-14T16:00:00Z"
}
```

**Error Response (401):**
```json
{ "detail": "Could not validate credentials" }
```

---

### GET /auth/verify-email/{token}
Verify email address with verification token.

**URL Parameters:**
- `token` (string): Verification token from email

**Success Response (200):**
```json
{ "message": "Email verified successfully" }
```

**Error Responses:**
```json
// Invalid/expired token (400)
{ "detail": "Invalid or expired verification token" }

// User not found (404)
{ "detail": "User not found" }

// Already verified (200)
{ "message": "Email already verified" }
```

---

### POST /auth/password-reset-request
Request password reset email.

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Success Response (200):**
```json
{ "message": "Password reset email sent if account exists" }
```

**Rate Limit:** 3 requests per 3600 seconds (1 hour)

---

### POST /auth/password-reset-confirm
Confirm password reset with token.

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Success Response (200):**
```json
{ "message": "Password reset successful" }
```

**Error Responses:**
```json
// Invalid/expired token (400)
{ "detail": "Invalid or expired password reset token" }

// Passwords don't match (400)
{ "detail": "Passwords do not match" }
```

---

## User Management

### GET /users
List all users (admin only).

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, default: 0): Number of items to skip
- `limit` (integer, default: 20, max: 100): Number of items to return

**Success Response (200):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "status": "active",
      "is_active": true,
      "is_admin": false,
      "last_login_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-14T15:45:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_items": 150,
  "total_pages": 8,
  "has_more": true
}
```

---

### GET /users/{user_id}
Get user details.

**URL Parameters:**
- `user_id` (integer): User ID

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "avatar_url": "https://...",
  "status": "active",
  "is_active": true,
  "is_admin": false,
  "is_mfa_enabled": true,
  "last_login_at": "2024-01-15T10:30:00Z",
  "last_login_ip": "192.168.1.1",
  "created_at": "2024-01-14T15:45:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "email_verified_at": "2024-01-14T16:00:00Z"
}
```

---

### PUT /users/{user_id}
Update user profile.

**URL Parameters:**
- `user_id` (integer): User ID

**Request Body:**
```json
{
  "full_name": "John Updated",
  "phone_number": "+9876543210",
  "avatar_url": "https://..."
}
```

**Success Response (200):**
Returns updated user object

---

### POST /users/{user_id}/password-change
Change user password (requires current password).

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Success Response (200):**
```json
{ "message": "Password changed successfully" }
```

**Error Responses:**
```json
// Wrong current password (400)
{ "detail": "Current password is incorrect" }

// Same password (400)
{ "detail": "New password cannot be the same as current password" }

// Weak password (400)
{
  "detail": [
    {
      "field": "new_password",
      "message": "Password must contain at least one uppercase letter"
    }
  ]
}
```

---

### POST /users/{user_id}/roles
Assign role to user.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "role_id": 2
}
```

**Success Response (200):**
Returns updated user with roles

---

### DELETE /users/{user_id}/roles/{role_id}
Remove role from user.

**Success Response (200):**
Returns updated user without role

---

## Role Management

### GET /roles
List all roles.

**Success Response (200):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator role",
      "permissions": [
        {
          "id": 1,
          "name": "users.create",
          "description": "Create users"
        }
      ],
      "created_at": "2024-01-10T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ]
}
```

---

### POST /roles
Create new role.

**Request Body:**
```json
{
  "name": "moderator",
  "description": "Content moderator role",
  "permissions": [1, 2, 3]
}
```

**Success Response (201):**
Returns created role

---

### PUT /roles/{role_id}
Update role.

**Request Body:**
```json
{
  "description": "Updated description",
  "permissions": [1, 2]
}
```

**Success Response (200):**
Returns updated role

---

### DELETE /roles/{role_id}
Delete role.

**Success Response (204):**
No content

---

## Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE",
  "errors": [
    {
      "field": "username",
      "message": "Username is required"
    }
  ]
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Login successful |
| 201 | Created | User registered |
| 204 | No Content | Logout successful |
| 400 | Bad Request | Invalid password format |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | User not found |
| 409 | Conflict | Username already taken |
| 422 | Unprocessable Entity | Validation error |
| 423 | Locked | Account locked |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Database error |

---

## Rate Limiting

Rate limits are applied per endpoint:

```
GET    /auth/login        10 per 60 seconds
POST   /auth/register     5 per 60 seconds
POST   /auth/refresh      20 per 60 seconds
POST   /password-reset    3 per 3600 seconds
```

### Rate Limit Headers

When rate limited, you'll receive:
```
HTTP/1.1 429 Too Many Requests

Retry-After: 60
```

---

## Authentication

All protected endpoints require the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Token Expiration

- **Access Token**: 15 minutes
- **Refresh Token**: 7 days
- **Password Reset Token**: 1 hour
- **Email Verification Token**: 24 hours

When access token expires, use the refresh token to get a new one:

```
POST /auth/refresh
```

---

## CORS

The API supports CORS for configured origins. Include credentials:

```javascript
fetch(url, {
  credentials: 'include',  // Important!
  headers: {
    'Authorization': 'Bearer ' + token
  }
})
```

---

See [Integration Guide](../integration/INTEGRATION_GUIDE.md) for usage examples in different frameworks.
