from pydantic import BaseModel, validator
from uuid import UUID
from datetime import datetime
from typing import Optional

class SwipeBase(BaseModel):
    user_id: UUID
    product_id: UUID
    action: str

    @validator('action')
    def validate_action(cls, v):
        if v not in ['left', 'right']:
            raise ValueError('Action must be either "left" or "right"')
        return v

class SwipeCreate(SwipeBase):
    pass

class Swipe(SwipeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True 