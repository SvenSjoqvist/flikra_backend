from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db import get_db
from app.models import WishlistItem, Product, User
from app.schemas import WishlistItem as WishlistItemSchema, WishlistItemCreate, WishlistItemUpdate

router = APIRouter()

@router.post("/", response_model=WishlistItemSchema, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(wishlist_item: WishlistItemCreate, db: Session = Depends(get_db)):
    """Add a product to user's wishlist."""
    # Check if user exists
    user = db.query(User).filter(User.id == wishlist_item.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == wishlist_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if item already in wishlist
    existing_item = db.query(WishlistItem).filter(
        WishlistItem.user_id == wishlist_item.user_id,
        WishlistItem.product_id == wishlist_item.product_id
    ).first()
    
    if existing_item:
        raise HTTPException(status_code=400, detail="Product already in wishlist")
    
    # Create wishlist item
    db_wishlist_item = WishlistItem(**wishlist_item.dict())
    db.add(db_wishlist_item)
    db.commit()
    db.refresh(db_wishlist_item)
    
    return db_wishlist_item

@router.get("/user/{user_id}", response_model=List[WishlistItemSchema])
def get_user_wishlist(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all items in a user's wishlist."""
    wishlist_items = db.query(WishlistItem).filter(
        WishlistItem.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return wishlist_items

@router.put("/{wishlist_item_id}", response_model=WishlistItemSchema)
def update_wishlist_item(wishlist_item_id: UUID, item_update: WishlistItemUpdate, db: Session = Depends(get_db)):
    """Update notes for a wishlist item."""
    wishlist_item = db.query(WishlistItem).filter(WishlistItem.id == wishlist_item_id).first()
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wishlist_item, field, value)
    
    db.commit()
    db.refresh(wishlist_item)
    return wishlist_item

@router.delete("/{wishlist_item_id}")
def remove_from_wishlist(wishlist_item_id: UUID, db: Session = Depends(get_db)):
    """Remove an item from wishlist."""
    wishlist_item = db.query(WishlistItem).filter(WishlistItem.id == wishlist_item_id).first()
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    db.delete(wishlist_item)
    db.commit()
    return {"message": "Item removed from wishlist"}

@router.delete("/user/{user_id}/product/{product_id}")
def remove_product_from_wishlist(user_id: UUID, product_id: UUID, db: Session = Depends(get_db)):
    """Remove a specific product from user's wishlist."""
    wishlist_item = db.query(WishlistItem).filter(
        WishlistItem.user_id == user_id,
        WishlistItem.product_id == product_id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")
    
    db.delete(wishlist_item)
    db.commit()
    return {"message": "Product removed from wishlist"} 