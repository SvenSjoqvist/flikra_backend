from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.models import Brand
from app.schemas import Brand as BrandSchema, BrandCreate, BrandUpdate

router = APIRouter()

@router.get("/", response_model=List[BrandSchema])
def list_brands(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all brands with pagination."""
    brands = db.query(Brand).offset(skip).limit(limit).all()
    return brands

@router.post("/", response_model=BrandSchema, status_code=status.HTTP_201_CREATED)
def create_brand(brand: BrandCreate, db: Session = Depends(get_db)):
    """Create a new brand."""
    db_brand = Brand(**brand.dict())
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand

@router.get("/{brand_id}", response_model=BrandSchema)
def get_brand(brand_id: UUID, db: Session = Depends(get_db)):
    """Get a specific brand by ID."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.put("/{brand_id}", response_model=BrandSchema)
def update_brand(brand_id: UUID, brand_update: BrandUpdate, db: Session = Depends(get_db)):
    """Update a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    update_data = brand_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)
    
    db.commit()
    db.refresh(brand)
    return brand

@router.delete("/{brand_id}")
def delete_brand(brand_id: UUID, db: Session = Depends(get_db)):
    """Delete a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    db.delete(brand)
    db.commit()
    return {"message": "Brand deleted successfully"}

@router.get("/{brand_id}/products", response_model=List)
def get_brand_products(brand_id: UUID, db: Session = Depends(get_db)):
    """Get all products for a specific brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand.products 