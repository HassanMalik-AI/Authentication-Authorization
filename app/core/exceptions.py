from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any


class AuthenticationException(HTTPException):
    """Authentication failed"""
    def __init__(self, detail: str = "Authentication failed", headers: Optional[Dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class InvalidCredentialsException(AuthenticationException):
    """Invalid username or password"""
    def __init__(self):
        super().__init__(detail="Invalid username or password")


class TokenExpiredException(AuthenticationException):
    """Token has expired"""
    def __init__(self):
        super().__init__(detail="Token has expired. Please login again")


class InvalidTokenException(AuthenticationException):
    """Invalid or malformed token"""
    def __init__(self):
        super().__init__(detail="Invalid or malformed token")


class AuthorizationException(HTTPException):
    """Authorization failed"""
    def __init__(self, detail: str = "Insufficient permissions", required_roles: Optional[List[str]] = None):
        message = detail
        if required_roles:
            message = f"{detail}. Required roles: {', '.join(required_roles)}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


class InsufficientPermissionsException(AuthorizationException):
    """User doesn't have required permissions"""
    def __init__(self, required_permissions: Optional[List[str]] = None):
        detail = "Insufficient permissions"
        if required_permissions:
            detail = f"Missing permissions: {', '.join(required_permissions)}"
        super().__init__(detail)


class InsufficientRoleException(AuthorizationException):
    """User doesn't have required role"""
    def __init__(self, required_roles: Optional[List[str]] = None):
        super().__init__(
            detail="Insufficient role",
            required_roles=required_roles
        )


class AccountDisabledException(HTTPException):
    """User account is disabled"""
    def __init__(self, reason: str = "Account disabled"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account {reason}"
        )


class AccountLockedException(HTTPException):
    """User account is locked"""
    def __init__(self, locked_until: Optional[str] = None):
        detail = "Account locked due to too many failed login attempts"
        if locked_until:
            detail = f"{detail}. Locked until {locked_until}"
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=detail
        )


class AccountSuspendedException(AccountDisabledException):
    """User account is suspended"""
    def __init__(self):
        super().__init__(reason="is suspended. Contact support")


class AccountDeletedException(HTTPException):
    """User account is deleted"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail="Account not found or has been deleted"
        )


class EmailNotVerifiedException(HTTPException):
    """Email address not verified"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please check your email for verification link"
        )


class MFARequiredException(HTTPException):
    """MFA verification required"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-factor authentication required"
        )


class DuplicateUserException(HTTPException):
    """User already exists"""
    def __init__(self, field: str = "username"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this {field} already exists"
        )


class UserNotFoundException(HTTPException):
    """User not found"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


class InvalidPasswordResetTokenException(HTTPException):
    """Invalid password reset token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )


class PasswordResetExpiredException(HTTPException):
    """Password reset token expired"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired"
        )


class EmailSendingException(HTTPException):
    """Failed to send email"""
    def __init__(self, detail: str = "Failed to send email. Please try again"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class RateLimitExceededException(HTTPException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later",
            headers={"Retry-After": str(retry_after)} if retry_after else None
        )


class InvalidMFACodeException(HTTPException):
    """Invalid MFA code"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )


class RefreshTokenExpiredException(HTTPException):
    """Refresh token expired"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please login again"
        )


class InvalidRefreshTokenException(HTTPException):
    """Invalid refresh token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


class DatabaseException(HTTPException):
    """Database error"""
    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ValidationException(HTTPException):
    """Validation error"""
    def __init__(self, errors: List[Dict[str, Any]]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors
        )
