from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class BrandBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None
    image_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None
    image_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class Brand(BrandBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 