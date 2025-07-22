import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class ReferralClick(Base):
    __tablename__ = "referral_clicks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    target_url = Column(Text)
    utm_source = Column(Text)
    utm_campaign = Column(Text)
    ref_code = Column(Text)
    ip_address = Column(Text)
    country = Column(Text)
    city = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="referral_clicks")
    product = relationship("Product", back_populates="referral_clicks")
    brand = relationship("Brand", back_populates="referral_clicks") 