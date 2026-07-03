from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List


class UserCreate(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    phone_number: Optional[str] = Field(None, description="Phone number in E.164 format")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    is_active: bool
    is_admin: bool
    is_mfa_enabled: bool
    created_at: datetime
    email_verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LoginResponse(BaseModel):
    """Login response with user info"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 900  # 15 minutes


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class PasswordChange(BaseModel):
    """Change password request (authenticated)"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")


class LogoutRequest(BaseModel):
    """Logout request"""
    all_devices: bool = Field(default=False, description="Logout from all devices")


class MFAEnable(BaseModel):
    """Enable MFA request"""
    password: str = Field(..., description="User password for verification")


class MFAVerify(BaseModel):
    """Verify MFA token"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit MFA code")


class MFARecoveryCodes(BaseModel):
    """MFA recovery codes"""
    codes: List[str]
    generated_at: datetime


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token (from cookie if not provided)")
