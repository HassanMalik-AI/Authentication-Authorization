from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class UserUpdate(BaseModel):
    """User profile update"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserDetailResponse(BaseModel):
    """Detailed user response"""
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
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    email_verified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list item"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    status: str
    is_active: bool
    is_admin: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    """Update user status"""
    status: str = Field(..., description="User status (active, inactive, suspended, deleted)")


class UserRoleAssign(BaseModel):
    """Assign role to user"""
    role_id: int = Field(..., description="Role ID")


class UserPermissionAssign(BaseModel):
    """Assign permission to user"""
    permission_id: int = Field(..., description="Permission ID")
