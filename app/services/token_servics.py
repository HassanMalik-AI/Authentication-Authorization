from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.models.refresh_token import RefreshToken
from app.core.security import decode_token, create_access_token, create_refresh_token
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenService:
    """Token management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tokens(
        self,
        user_id: int,
        username: str,
        ip_address: str,
        user_agent: str,
        device_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """Create access and refresh tokens"""
        # Token payload
        token_data = {"sub": username, "user_id": user_id}
        
        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in database
        refresh_token_obj = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            is_revoked=False
        )
        self.db.add(refresh_token_obj)
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def refresh_tokens(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Create new tokens from refresh token"""
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Find stored refresh token
        stored_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Check if revoked
        if stored_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Check expiry
        if stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        
        # Create new tokens
        token_data = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id")
        }
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)
        
        # Revoke old refresh token
        stored_token.is_revoked = True
        stored_token.revoked_at = datetime.utcnow()
        
        # Store new refresh token
        new_refresh_obj = RefreshToken(
            token=new_refresh,
            user_id=stored_token.user_id,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=stored_token.ip_address,
            user_agent=stored_token.user_agent,
            device_name=stored_token.device_name,
            is_revoked=False
        )
        self.db.add(new_refresh_obj)
        self.db.commit()
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def revoke_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token"""
        stored_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if stored_token:
            stored_token.is_revoked = True
            stored_token.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user"""
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        count = 0
        for token in tokens:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        logger.info(f"Revoked {count} tokens for user {user_id}")
        
        return count
    
    def get_user_devices(self, user_id: int) -> list:
        """Get all active devices for user (refresh tokens)"""
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        devices = []
        for token in tokens:
            devices.append({
                "device_name": token.device_name,
                "ip_address": token.ip_address,
                "user_agent": token.user_agent,
                "created_at": token.created_at,
                "expires_at": token.expires_at
            })
        
        return devices
    
    def revoke_device_token(self, user_id: int, device_name: str) -> bool:
        """Revoke token for specific device"""
        token = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.device_name == device_name,
            RefreshToken.is_revoked == False
        ).first()
        
        if token:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired refresh tokens"""
        # Delete tokens that are revoked and expired
        tokens_to_delete = self.db.query(RefreshToken).filter(
            RefreshToken.is_revoked == True,
            RefreshToken.revoked_at < datetime.utcnow() - timedelta(days=7)
        ).all()
        
        count = 0
        for token in tokens_to_delete:
            self.db.delete(token)
            count += 1
        
        self.db.commit()
        logger.info(f"Cleaned up {count} expired tokens")
        
        return count
    
    def is_token_revoked(self, refresh_token: str) -> bool:
        """Check if token is revoked"""
        token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        return token and token.is_revoked if token else False
    
    def validate_token_ip(self, refresh_token: str, current_ip: str) -> bool:
        """Validate token was used from same IP"""
        token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if token:
            return token.ip_address == current_ip
        
        return False
