from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('auth.users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('auth.roles.id'), primary_key=True),
    schema='auth'
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('auth.roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('auth.permissions.id'), primary_key=True),
    schema='auth'
)

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = ({'schema': 'auth'})
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = ({'schema': 'auth'})
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # create, read, update, delete, manage
    description = Column(String(200))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = ({'schema': 'auth'})
    
    user_id = Column(Integer, ForeignKey("auth.users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("auth.roles.id"), primary_key=True)
    granted_by = Column(Integer, ForeignKey("auth.users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    granted_by_user = relationship("User", foreign_keys=[granted_by])

class UserPermission(Base):
    __tablename__ = "user_permissions"
    __table_args__ = ({'schema': 'auth'})
    
    user_id = Column(Integer, ForeignKey("auth.users.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("auth.permissions.id"), primary_key=True)
    granted_by = Column(Integer, ForeignKey("auth.users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission")