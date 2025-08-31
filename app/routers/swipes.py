from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db import get_db
from app.models import Swipe, Product
from app.schemas import Swipe as SwipeSchema, SwipeCreate

router = APIRouter()

@router.post("/", response_model=SwipeSchema, status_code=status.HTTP_201_CREATED)
def create_swipe(swipe: SwipeCreate, db: Session = Depends(get_db)):
    """Record a swipe (left or right) on a product."""
    print(f"🔍 Debug: Creating swipe - User: {swipe.user_id}, Product: {swipe.product_id}, Action: {swipe.action}")
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == swipe.product_id).first()
    if not product:
        print(f"❌ Product not found: {swipe.product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user already swiped on this product
    existing_swipe = db.query(Swipe).filter(
        Swipe.user_id == swipe.user_id,
        Swipe.product_id == swipe.product_id
    ).first()
    
    if existing_swipe:
        print(f"❌ User already swiped on product: {swipe.user_id} -> {swipe.product_id}")
        raise HTTPException(status_code=400, detail="User has already swiped on this product")
    
    # Check if user has swiped all products
    total_products = db.query(Product).count()
    user_swipes_count = db.query(Swipe).filter(Swipe.user_id == swipe.user_id).count()
    if user_swipes_count >= total_products:
        print(f"ℹ️ User has swiped all products: {swipe.user_id}")
        return {"message": "You have swiped on all available products!"}
    
    # Create new swipe
    swipe_data = swipe.dict()
    if 'brand_id' in swipe_data:
        swipe_data.pop('brand_id')
    
    print(f"✅ Creating swipe with data: {swipe_data}")
    db_swipe = Swipe(**swipe_data)
    db.add(db_swipe)
    db.commit()
    db.refresh(db_swipe)
    
    print(f"✅ Swipe created successfully: {db_swipe.id}")
    return db_swipe

@router.get("/user/{user_id}", response_model=List[SwipeSchema])
def get_user_swipes(user_id: UUID, action: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all swipes by a specific user, optionally filtered by action."""
    query = db.query(Swipe).filter(Swipe.user_id == user_id)
    
    if action:
        query = query.filter(Swipe.action == action)
    
    swipes = query.offset(skip).limit(limit).all()
    return swipes

@router.get("/product/{product_id}", response_model=List[SwipeSchema])
def get_product_swipes(product_id: UUID, action: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all swipes for a specific product, optionally filtered by action."""
    query = db.query(Swipe).filter(Swipe.product_id == product_id)
    
    if action:
        query = query.filter(Swipe.action == action)
    
    swipes = query.offset(skip).limit(limit).all()
    return swipes

@router.get("/stats/product/{product_id}")
def get_product_swipe_stats(product_id: UUID, db: Session = Depends(get_db)):
    """Get swipe statistics for a specific product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    right_count = db.query(Swipe).filter(
        Swipe.product_id == product_id,
        Swipe.action == "right"
    ).count()
    
    left_count = db.query(Swipe).filter(
        Swipe.product_id == product_id,
        Swipe.action == "left"
    ).count()
    
    total_swipes = right_count + left_count
    right_percentage = (right_count / total_swipes * 100) if total_swipes > 0 else 0
    
    return {
        "product_id": product_id,
        "total_swipes": total_swipes,
        "right_swipes": right_count,
        "left_swipes": left_count,
        "right_percentage": round(right_percentage, 2)
    }

@router.delete("/user/{user_id}/reset", status_code=200)
def reset_user_swipes(user_id: UUID, db: Session = Depends(get_db)):
    """Delete all swipes for a user."""
    deleted = db.query(Swipe).filter(Swipe.user_id == user_id).delete()
    db.commit()
    return {"message": f"Deleted {deleted} swipes for user {user_id}"}
