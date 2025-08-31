from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class BrandMemberBase(BaseModel):
    user_id: UUID
    brand_id: UUID
    role: Optional[str] = None
    status: Optional[str] = None

class BrandMemberCreate(BrandMemberBase):
    pass

class BrandMemberUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None

class BrandMember(BrandMemberBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 