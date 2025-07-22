import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Swipe(Base):
    __tablename__ = "swipes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    direction = Column(Text, CheckConstraint("direction IN ('left', 'right')"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="swipes")
    product = relationship("Product", back_populates="swipes")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),
    ) 