from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

class ProductBase(BaseModel):
    brand_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    item_url: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    tags: Optional[List[str]] = None
    product_metadata: Optional[Dict[str, Any]] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    brand_id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    item_url: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    tags: Optional[List[str]] = None
    product_metadata: Optional[Dict[str, Any]] = None

class Product(ProductBase):
    id: UUID
    vector_id_image: Optional[str] = None
    vector_id_text: Optional[str] = None
    swipe_right_count: int
    swipe_left_count: int
    created_at: datetime

    class Config:
        from_attributes = True 