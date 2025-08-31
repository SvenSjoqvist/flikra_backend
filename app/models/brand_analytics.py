from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db import Base

class BrandAnalytics(Base):
    __tablename__ = "brand_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    
    # Statistics
    total_products = Column(Integer, default=0)
    total_swipes = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_dislikes = Column(Integer, default=0)
    total_members = Column(Integer, default=0)
    active_members = Column(Integer, default=0)
    
    # Additional metrics
    total_revenue = Column(Integer, default=0)  # In cents
    conversion_rate = Column(Integer, default=0)  # Percentage * 100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand", back_populates="analytics")
    
    def __repr__(self):
        return f"<BrandAnalytics(brand_id={self.brand_id}, products={self.total_products}, swipes={self.total_swipes})>" 