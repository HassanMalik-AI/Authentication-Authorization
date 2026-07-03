from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, JSON, Table, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import re
from datetime import datetime

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    UNVERIFIED = "unverified"

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        {'schema': 'auth'}  # Use separate schema for security
    )
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    
    # Profile
    full_name = Column(String(100))
    phone_number = Column(String(20))
    avatar_url = Column(String(500))
    
    # Status
    status = Column(Enum(UserStatus), default=UserStatus.UNVERIFIED)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45))  # IPv6 support
    last_login_user_agent = Column(Text)
    
    # MFA
    is_mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(Text, nullable=True)
    mfa_recovery_codes = Column(JSON, nullable=True)  # Encrypted
    
    # Multi-tenancy
    tenant_id = Column(Integer, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    permissions = relationship("UserPermission", back_populates="user")
    
    @validates('username')
    def validate_username(self, key, value):
        if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', value):
            raise ValueError('Username must be 3-50 characters and contain only letters, numbers, underscore, and hyphen')
        return value
    
    @validates('email')
    def validate_email(self, key, value):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError('Invalid email format')
        return value
    
    @validates('phone_number')
    def validate_phone(self, key, value):
        if value and not re.match(r'^\+?[1-9]\d{1,14}$', value):
            raise ValueError('Invalid phone number format (E.164)')
        return value
    
    @property
    def is_locked(self) -> bool:
        if not self.locked_until:
            return False
        return self.locked_until > datetime.utcnow()