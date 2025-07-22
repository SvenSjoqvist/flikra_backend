from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    brand = relationship("Brand", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'brand_id', name='_user_role_brand_uc'),
    ) 