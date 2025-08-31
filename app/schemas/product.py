from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

class ProductBase(BaseModel):
    brand_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    price: Optional[Decimal] = None
    image: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    flagged: Optional[bool] = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    brand_id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    image: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    flagged: Optional[bool] = None

class Product(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 