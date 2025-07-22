import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    referral_code = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred_user = relationship("User", foreign_keys=[referred_user_id], back_populates="referrals_received") 