from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from app.db import get_db
from app.models import User, Product as ProductModel
from app.schemas import User as UserSchema, UserCreate, UserUpdate, Product, ProductCreate, ProductUpdate
from app.utils.auth import get_password_hash

router = APIRouter()

# Schema for the users with brands response
class UserWithBrands(BaseModel):
    id: UUID
    name: Optional[str]
    email: str
    join_date: datetime
    brand_name: Optional[str]
    industry: Optional[str]
    role: Optional[str]
    status: Optional[str]
    products_managed: int
    swipes_generated: int

@router.get("/", response_model=List[UserSchema])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users with pagination."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/with-brands", response_model=List[UserWithBrands])
def get_users_with_brands(db: Session = Depends(get_db)):
    """Get users with their brand information and statistics."""
    # SQL query with JOIN
    query = text("""
    SELECT 
        u.id, u.name, u.email, u.created_at as join_date,
        b.name as brand_name, b.industry,
        bm.role, bm.status,
        COUNT(DISTINCT p.id) as products_managed,
        COUNT(DISTINCT s.id) as swipes_generated
    FROM users u
    LEFT JOIN brand_members bm ON u.id = bm.user_id
    LEFT JOIN brands b ON bm.brand_id = b.id
    LEFT JOIN products p ON b.id = p.brand_id
    LEFT JOIN swipes s ON u.id = s.user_id
    GROUP BY u.id, u.name, u.email, u.created_at, b.id, b.name, b.industry, bm.id, bm.role, bm.status
    ORDER BY u.created_at DESC
    """)
    
    try:
        # Execute raw SQL query
        result = db.execute(query)
        
        # Convert results to list of dictionaries
        users_with_brands = []
        for row in result:
            users_with_brands.append({
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "join_date": row.join_date,
                "brand_name": row.brand_name,
                "industry": row.industry,
                "role": row.role,
                "status": row.status,
                "products_managed": row.products_managed,
                "swipes_generated": row.swipes_generated
            })
        
        return users_with_brands
        
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user with hashed password and all fields
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        avatar=user.avatar,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
