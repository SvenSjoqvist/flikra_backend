import uuid
from sqlalchemy import Column, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text)
    logo = Column(Text)
    website = Column(Text)
    industry = Column(Text)
    status = Column(Text)
    plan = Column(Text)
    image_urls = Column(ARRAY(Text))
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand")
    user_roles = relationship("UserRole", back_populates="brand")
    brand_members = relationship("BrandMember", back_populates="brand")
    analytics_events = relationship("BrandAnalyticsEvent", back_populates="brand")
    referral_clicks = relationship("ReferralClick", back_populates="brand")
    reports = relationship("Report", back_populates="brand") 