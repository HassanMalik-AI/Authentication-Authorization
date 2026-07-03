from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.user import User, UserStatus
from app.models.refresh_token import RefreshToken
from app.models.audit_log import AuditLog
from app.core.security import (
    hash_password, verify_password, decode_token,
    create_access_token, create_refresh_token,
    needs_rehash
)
from app.core.config import settings
from app.services.email_servics import EmailService
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication business logic"""
    
    def __init__(self, db: Session, request_data: Dict[str, Any] = None):
        self.db = db
        self.request_data = request_data or {}
    
    def register_user(self, username: str, email: str, password: str, **kwargs) -> User:
        """Register new user"""
        # Check existing
        if self.db.query(User).filter(User.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            status=UserStatus.UNVERIFIED,
            is_active=False,
            **kwargs
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log registration
        self._log_audit(user, "REGISTER", "User registered")
        
        # Send verification email
        EmailService.send_verification_email(user.email, user.id)
        
        return user
    
    def login_user(self, username: str, password: str, ip: str, user_agent: str) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check account status
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended. Contact support."
            )
        
        if user.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Check lockout
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            self.db.commit()
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed attempts. Try again in 30 minutes."
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Reset failed attempts on success
        user.failed_login_attempts = 0
        
        # Rehash password if needed
        if needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(password)
        
        # Update login info
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip
        user.last_login_user_agent = user_agent
        user.status = UserStatus.ACTIVE
        user.is_active = True
        
        self.db.commit()
        
        # Create tokens
        token_data = {"sub": user.username, "user_id": user.id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in database
        refresh_token_obj = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip,
            user_agent=user_agent,
            device_name=self.request_data.get("device_name", "Unknown")
        )
        self.db.add(refresh_token_obj)
        self.db.commit()
        
        # Log login
        self._log_audit(user, "LOGIN", "User logged in", {"ip": ip, "user_agent": user_agent})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "status": user.status
            }
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is revoked
        stored_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()
        
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or not found"
            )
        
        # Check expiry
        if stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        token_data = {"sub": user.username, "user_id": user.id}
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)
        
        # Invalidate old refresh token
        stored_token.is_revoked = True
        stored_token.revoked_at = datetime.utcnow()
        
        # Store new refresh token
        new_refresh_obj = RefreshToken(
            token=new_refresh,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=stored_token.ip_address,
            user_agent=stored_token.user_agent
        )
        self.db.add(new_refresh_obj)
        self.db.commit()
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
    
    def logout_user(self, user_id: int, refresh_token: str) -> None:
        """Logout user by revoking refresh token"""
        token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == user_id
        ).first()
        
        if token:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
            self.db.commit()
            
            self._log_audit(token.user, "LOGOUT", "User logged out")
    
    def _log_audit(self, user: User, action: str, description: str, metadata: dict = None):
        """Log audit trail"""
        audit = AuditLog(
            user_id=user.id,
            action=action,
            description=description,
            metadata=metadata or {},
            ip_address=self.request_data.get("ip"),
            user_agent=self.request_data.get("user_agent")
        )
        self.db.add(audit)
        self.db.commit()