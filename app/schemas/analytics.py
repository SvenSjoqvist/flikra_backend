from pydantic import BaseModel, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

# Original analytics event schemas (needed by other parts of the app)
class BrandAnalyticsEventBase(BaseModel):
    brand_id: UUID
    product_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    event_type: str
    event_metadata: Optional[Dict[str, Any]] = None
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

# New dashboard schemas
class DashboardOverview(BaseModel):
    period: str
    total_swipes: Dict[str, Any]
    conversion_rate: Dict[str, Any]
    avg_session_time: Dict[str, Any]
    weekly_activity: Dict[str, int]
    user_demographics: Dict[str, int]
    top_performing_products: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]

class RealTimeStats(BaseModel):
    date: str
    swipes_today: int
    likes_today: int
    active_users_today: int
    conversion_rate_today: float

class ExportData(BaseModel):
    date_range: Dict[str, str]
    swipes: List[Dict[str, Any]]
    analytics_events: List[Dict[str, Any]]

class TopProduct(BaseModel):
    product: str
    swipes: int
    likes: int
    rate: float

class WeeklyActivity(BaseModel):
    Mon: int
    Tue: int
    Wed: int
    Thu: int
    Fri: int
    Sat: int
    Sun: int

class QuickStats(BaseModel):
    total_likes: int
    total_dislikes: int
    returning_users_percent: float
    overall_like_rate: float
    avg_rating: float
    daily_active_users: int
    engagement_rate: float
    total_views: int 