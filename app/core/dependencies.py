from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserStatus
from app.models.role import Permission
import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if not payload:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if not username:
        raise credentials_exception
    
    user = db.query(User).filter(
        User.username == username,
        User.status != UserStatus.DELETED
    ).first()
    
    if not user:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def require_roles(allowed_roles: List[str]):
    """Role-based access control"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Get user's roles
        user_roles = [ur.role.name for ur in current_user.roles]
        
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{', '.join(user_roles)}' not allowed. Requires: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: List[str]):
    """Permission-based access control"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's permissions (from roles + direct)
        user_permissions = set()
        
        # From roles
        for user_role in current_user.roles:
            for permission in user_role.role.permissions:
                user_permissions.add(permission.name)
        
        # Direct permissions
        for perm in current_user.permissions:
            user_permissions.add(perm.permission.name)
        
        # Check if user has ALL required permissions
        if not all(perm in user_permissions for perm in required_permissions):
            missing = [p for p in required_permissions if p not in user_permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}"
            )
        return current_user
    return permission_checker

def require_mfa_enabled():
    """Check if user has MFA enabled"""
    async def mfa_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.is_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA required for this endpoint"
            )
        return current_user
    return mfa_checker