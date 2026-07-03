from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class PermissionResponse(BaseModel):
    """Permission response"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Create role request"""
    name: str = Field(..., min_length=3, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")
    permissions: Optional[List[int]] = Field(default_factory=list, description="Permission IDs")


class RoleUpdate(BaseModel):
    """Update role request"""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[int]] = Field(None, description="Permission IDs")


class RoleResponse(BaseModel):
    """Role response"""
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """Detailed role response with user count"""
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionResponse] = []
    user_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    """Create permission request"""
    name: str = Field(..., min_length=3, max_length=100, description="Permission name (e.g., users.create)")
    description: Optional[str] = Field(None, max_length=500)


class PermissionUpdate(BaseModel):
    """Update permission request"""
    description: Optional[str] = Field(None, max_length=500)


class RolePermissionAssign(BaseModel):
    """Assign permission to role"""
    permission_ids: List[int] = Field(..., description="List of permission IDs")
