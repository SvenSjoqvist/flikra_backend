from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.db import get_db
from app.models import Brand, Product, Swipe, BrandMember
from app.schemas import Brand as BrandSchema, BrandCreate, BrandUpdate, Product as ProductSchema

router = APIRouter()

# Schema for brand statistics
class BrandStats(BaseModel):
    brand_id: UUID
    total_products: int
    total_swipes: int
    total_likes: int
    total_dislikes: int
    total_members: int
    active_members: int

@router.get("/", response_model=List[BrandSchema])
def get_brands(db: Session = Depends(get_db)):
    """Get all brands."""
    brands = db.query(Brand).all()
    return brands

@router.get("/{brand_id}", response_model=BrandSchema)
def get_brand(brand_id: UUID, db: Session = Depends(get_db)):
    """Get a specific brand by ID."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.get("/{brand_id}/products", response_model=List[ProductSchema])
def get_brand_products(brand_id: UUID, db: Session = Depends(get_db)):
    """Get all products for a specific brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand.products

@router.get("/{brand_id}/stats", response_model=BrandStats)
def get_brand_stats(brand_id: UUID, db: Session = Depends(get_db)):
    """Get comprehensive statistics for a brand using efficient COUNT queries."""
    
    # Check if brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        # Use raw SQL for maximum efficiency
        query = text("""
        SELECT 
            :brand_id as brand_id,
            COALESCE(products.count, 0) as total_products,
            COALESCE(swipes.count, 0) as total_swipes,
            COALESCE(likes.count, 0) as total_likes,
            COALESCE(dislikes.count, 0) as total_dislikes,
            COALESCE(members.count, 0) as total_members,
            COALESCE(active_members.count, 0) as active_members
        FROM (SELECT 1) as dummy
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM products 
            WHERE brand_id = :brand_id
        ) as products ON true
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM swipes s
            JOIN products p ON s.product_id = p.id
            WHERE p.brand_id = :brand_id
        ) as swipes ON true
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM swipes s
            JOIN products p ON s.product_id = p.id
            WHERE p.brand_id = :brand_id AND s.action = 'right'
        ) as likes ON true
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM swipes s
            JOIN products p ON s.product_id = p.id
            WHERE p.brand_id = :brand_id AND s.action = 'left'
        ) as dislikes ON true
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM brand_members 
            WHERE brand_id = :brand_id
        ) as members ON true
        LEFT JOIN (
            SELECT COUNT(*) as count 
            FROM brand_members 
            WHERE brand_id = :brand_id AND status IN ('active', 'ACTIVE', 'Active')
        ) as active_members ON true
        """)
        
        result = db.execute(query, {"brand_id": brand_id}).first()
        
        return BrandStats(
            brand_id=brand_id,
            total_products=result.total_products,
            total_swipes=result.total_swipes,
            total_likes=result.total_likes,
            total_dislikes=result.total_dislikes,
            total_members=result.total_members,
            active_members=result.active_members
        )
        
    except Exception as e:
        print(f"Error getting brand stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get brand statistics")

@router.get("/{brand_id}/stats/simple")
def get_brand_stats_simple(brand_id: UUID, db: Session = Depends(get_db)):
    """Get simple brand statistics using SQLAlchemy ORM."""
    
    # Check if brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Count products
    total_products = db.query(func.count(Product.id)).filter(Product.brand_id == brand_id).scalar()
    
    # Count swipes (through products)
    total_swipes = db.query(func.count(Swipe.id)).join(Product).filter(Product.brand_id == brand_id).scalar()
    
    # Count likes
    total_likes = db.query(func.count(Swipe.id)).join(Product).filter(
        Product.brand_id == brand_id,
        Swipe.action == "right"
    ).scalar()
    
    # Count dislikes
    total_dislikes = db.query(func.count(Swipe.id)).join(Product).filter(
        Product.brand_id == brand_id,
        Swipe.action == "left"
    ).scalar()
    
    # Count members
    total_members = db.query(func.count(BrandMember.id)).filter(BrandMember.brand_id == brand_id).scalar()
    
    # Count active members
    active_members = db.query(func.count(BrandMember.id)).filter(
        BrandMember.brand_id == brand_id,
        BrandMember.status.in_(["active", "ACTIVE", "Active"])
    ).scalar()
    
    return {
        "brand_id": brand_id,
        "total_products": total_products,
        "total_swipes": total_swipes,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "total_members": total_members,
        "active_members": active_members
    }

@router.post("/", response_model=BrandSchema, status_code=status.HTTP_201_CREATED)
def create_brand(brand: BrandCreate, db: Session = Depends(get_db)):
    """Create a new brand."""
    db_brand = Brand(**brand.dict())
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand

@router.put("/{brand_id}", response_model=BrandSchema)
def update_brand(brand_id: UUID, brand_update: BrandUpdate, db: Session = Depends(get_db)):
    """Update a brand."""
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    update_data = brand_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_brand, field, value)
    
    db.commit()
    db.refresh(db_brand)
    return db_brand

@router.delete("/{brand_id}")
def delete_brand(brand_id: UUID, db: Session = Depends(get_db)):
    """Delete a brand."""
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    db.delete(db_brand)
    db.commit()
    return {"message": "Brand deleted successfully"} 