from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class WishlistItemBase(BaseModel):
    user_id: UUID
    product_id: UUID
    notes: Optional[str] = None

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItemUpdate(BaseModel):
    notes: Optional[str] = None

class WishlistItem(WishlistItemBase):
    id: UUID
    saved_at: datetime

    class Config:
        from_attributes = True 