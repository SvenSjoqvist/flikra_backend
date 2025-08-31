import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, ARRAY, JSON, DateTime, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.id'))
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Numeric)
    image = Column(Text)
    category = Column(Text)
    color = Column(Text, nullable=True, comment='Product color')
    tags = Column(ARRAY(Text), nullable=True, comment='Product tags')
    status = Column(Text)
    flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Vector fields for similarity search
    image_vector = Column(ARRAY(Float), nullable=True, comment='CLIP image embedding vector')
    text_vector = Column(ARRAY(Float), nullable=True, comment='Text embedding vector')
    combined_vector = Column(ARRAY(Float), nullable=True, comment='Combined image+text vector')
    vector_metadata = Column(Text, nullable=True, comment='JSON metadata about vectors')
    
    # Relationships
    brand = relationship("Brand", back_populates="products")
    swipes = relationship("Swipe", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    analytics_events = relationship("BrandAnalyticsEvent", back_populates="product")
    referral_clicks = relationship("ReferralClick", back_populates="product") 