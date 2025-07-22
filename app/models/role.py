from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship
from app.db import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role") 