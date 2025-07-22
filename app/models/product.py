import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, ARRAY, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(Text)
    item_url = Column(Text)
    color = Column(String)
    category = Column(String)
    gender = Column(String)
    tags = Column(ARRAY(Text))
    product_metadata = Column(JSON)  # Use JSON instead of JSONB
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.id'))
    swipe_right_count = Column(Integer, default=0)
    swipe_left_count = Column(Integer, default=0)
    vector_id_combined = Column(ARRAY(Float))  # New field for combined vector representation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand", back_populates="products")
    swipes = relationship("Swipe", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    analytics_events = relationship("BrandAnalyticsEvent", back_populates="product")
    referral_clicks = relationship("ReferralClick", back_populates="product") 