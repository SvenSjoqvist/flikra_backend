from pydantic import BaseModel, validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class BrandAnalyticsEventBase(BaseModel):
    brand_id: UUID
    product_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    event_type: str
    event_metadata: Optional[Dict[str, Any]] = None  # Changed from 'metadata' to 'event_metadata'
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ['view_brand', 'view_product', 'swipe_right', 'swipe_left', 'wishlist_save', 'click_link']
        if v not in allowed_types:
            raise ValueError(f'event_type must be one of: {", ".join(allowed_types)}')
        return v

class BrandAnalyticsEventCreate(BrandAnalyticsEventBase):
    pass

class BrandAnalyticsEvent(BrandAnalyticsEventBase):
    id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True 