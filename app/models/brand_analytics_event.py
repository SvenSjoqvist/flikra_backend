import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class BrandAnalyticsEvent(Base):
    __tablename__ = "brand_analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_type = Column(Text)
    ip_address = Column(Text)
    country = Column(Text)
    city = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand", back_populates="analytics_events")
    product = relationship("Product", back_populates="analytics_events")
    user = relationship("User", back_populates="analytics_events") 