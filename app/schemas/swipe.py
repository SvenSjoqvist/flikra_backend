from pydantic import BaseModel, validator
from uuid import UUID
from datetime import datetime
from typing import Optional

class SwipeBase(BaseModel):
    user_id: UUID
    product_id: UUID
    direction: str

    @validator('direction')
    def validate_direction(cls, v):
        if v not in ['left', 'right']:
            raise ValueError('direction must be either "left" or "right"')
        return v

class SwipeCreate(SwipeBase):
    pass

class Swipe(SwipeBase):
    id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True 