from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({'schema': 'auth'})
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # LOGIN, REGISTER, UPDATE, DELETE, etc.
    description = Column(Text)
    metadata = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")