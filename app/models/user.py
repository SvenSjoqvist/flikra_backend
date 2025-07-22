import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - specify foreign_keys to avoid ambiguity
    user_roles = relationship("UserRole", foreign_keys="UserRole.user_id", back_populates="user")
    swipes = relationship("Swipe", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_user_id", back_populates="referred_user")
    analytics_events = relationship("BrandAnalyticsEvent", back_populates="user")
    referral_clicks = relationship("ReferralClick", back_populates="user") 