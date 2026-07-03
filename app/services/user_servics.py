from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from app.models.user import User, UserStatus
from app.models.role import Role, UserRole
from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.services.email_servics import EmailService
import logging

logger = logging.getLogger(__name__)


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).filter(
            User.status != UserStatus.DELETED
        ).offset(skip).limit(limit).all()
    
    def update_user_profile(
        self,
        user: User,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Update user profile"""
        if full_name is not None:
            user.full_name = full_name
        if phone_number is not None:
            user.phone_number = phone_number
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Prevent reusing same password
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as current password"
            )
        
        # Hash and save new password
        user.hashed_password = hash_password(new_password)
        self.db.commit()
        
        # Send email notification
        EmailService.send_password_changed_email(user.email, user.username)
        
        return True
    
    def assign_role(self, user: User, role_id: int) -> User:
        """Assign role to user"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Check if already assigned
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == role_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already assigned to user"
            )
        
        user_role = UserRole(user_id=user.id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def remove_role(self, user: User, role_id: int) -> User:
        """Remove role from user"""
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == role_id
        ).first()
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role assignment not found"
            )
        
        self.db.delete(user_role)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def suspend_user(self, user: User, reason: Optional[str] = None) -> User:
        """Suspend user account"""
        user.status = UserStatus.SUSPENDED
        user.is_active = False
        self.db.commit()
        
        logger.info(f"User {user.id} suspended. Reason: {reason}")
        return user
    
    def activate_user(self, user: User) -> User:
        """Activate suspended user"""
        user.status = UserStatus.ACTIVE
        user.is_active = True
        self.db.commit()
        
        logger.info(f"User {user.id} activated")
        return user
    
    def delete_user(self, user: User, soft_delete: bool = True) -> None:
        """Delete user (soft or hard)"""
        if soft_delete:
            # Soft delete
            user.status = UserStatus.DELETED
            user.is_active = False
            user.deleted_at = None  # Should be auto-set by DB
            self.db.commit()
            logger.info(f"User {user.id} soft deleted")
        else:
            # Hard delete - be careful!
            self.db.delete(user)
            self.db.commit()
            logger.warning(f"User {user.id} hard deleted")
    
    def count_users(self) -> int:
        """Get total user count (excluding deleted)"""
        return self.db.query(User).filter(
            User.status != UserStatus.DELETED
        ).count()
