from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime
from pydantic import BaseModel
import bcrypt

from app.db import get_db
from app.models import BrandMember, User, Brand
from app.schemas import BrandMember as BrandMemberSchema, BrandMemberCreate, BrandMemberUpdate
from app.auth import get_current_user

router = APIRouter()

# New schema for creating user and brand member together
class UserAndBrandMemberCreate(BaseModel):
    user_id: Optional[UUID] = None  # If not provided, will generate one
    email: str
    name: str
    password: str  # Add password field
    avatar: Optional[str] = None
    brand_id: UUID
    role: Optional[str] = None
    status: Optional[str] = None

class UserAndBrandMemberResponse(BaseModel):
    user: dict
    brand_member: BrandMemberSchema

# New schema for brand members with user info
class BrandMemberWithUser(BaseModel):
    id: UUID
    user_id: UUID
    brand_id: UUID
    role: Optional[str]
    status: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]  # Make this optional
    # User information
    user_name: Optional[str]
    user_email: str
    user_avatar: Optional[str]

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

@router.post("/with-user", response_model=UserAndBrandMemberResponse)
def create_user_and_brand_member(
    data: UserAndBrandMemberCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new user and brand member in one request."""
    # Check if brand exists
    brand = db.query(Brand).filter(Brand.id == data.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Generate user ID if not provided
    user_id = data.user_id or uuid.uuid4()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash the password
    password_hash = hash_password(data.password)
    
    # Create new user
    new_user = User(
        id=user_id,
        email=data.email,
        name=data.name,
        avatar=data.avatar,
        password_hash=password_hash,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Check if brand member already exists
    existing_member = db.query(BrandMember).filter(
        BrandMember.user_id == user_id,
        BrandMember.brand_id == data.brand_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Brand member already exists")
    
    # Create brand member
    brand_member_data = {
        "user_id": user_id,
        "brand_id": data.brand_id,
        "role": data.role,
        "status": data.status
    }
    
    new_brand_member = BrandMember(**brand_member_data)
    db.add(new_brand_member)
    db.commit()
    db.refresh(new_brand_member)
    
    print(f"✅ Created user and brand member: User {new_user.id} -> Brand {data.brand_id}")
    
    return UserAndBrandMemberResponse(
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "avatar": new_user.avatar,
            "created_at": new_user.created_at
        },
        brand_member=new_brand_member
    )

@router.post("/", response_model=BrandMemberSchema)
def create_brand_member(
    brand_member: BrandMemberCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new brand member. If user doesn't exist, create them automatically."""
    # Check if brand exists
    brand = db.query(Brand).filter(Brand.id == brand_member.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Check if user exists, if not create them
    user = db.query(User).filter(User.id == brand_member.user_id).first()
    if not user:
        # Create a new user automatically with a default password
        default_password = "changeme123"  # User should change this later
        password_hash = hash_password(default_password)
        
        user = User(
            id=brand_member.user_id,
            email=f"user_{brand_member.user_id}@example.com",  # Placeholder email
            name="New User",  # Placeholder name
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created new user automatically: {user.id} (default password: {default_password})")
    
    # Check if brand member already exists
    existing_member = db.query(BrandMember).filter(
        BrandMember.user_id == brand_member.user_id,
        BrandMember.brand_id == brand_member.brand_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Brand member already exists")
    
    # Create the brand member
    db_brand_member = BrandMember(**brand_member.dict())
    db.add(db_brand_member)
    db.commit()
    db.refresh(db_brand_member)
    
    print(f"✅ Created brand member: {db_brand_member.id} for user: {brand_member.user_id} in brand: {brand_member.brand_id}")
    return db_brand_member

@router.get("/", response_model=List[BrandMemberWithUser])
def get_brand_members(
    brand_id: UUID = None,
    user_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get brand members with optional filtering and user information."""
    # Build base query with JOIN
    query = db.query(BrandMember, User).join(User, BrandMember.user_id == User.id)
    
    if brand_id:
        query = query.filter(BrandMember.brand_id == brand_id)
    
    if user_id:
        query = query.filter(BrandMember.user_id == user_id)
    
    # Execute query and format results
    results = query.all()
    brand_members = []
    
    for member, user in results:
        brand_members.append(BrandMemberWithUser(
            id=member.id,
            user_id=member.user_id,
            brand_id=member.brand_id,
            role=member.role,
            status=member.status,
            created_at=member.created_at,
            updated_at=member.updated_at,
            user_name=user.name,
            user_email=user.email,
            user_avatar=user.avatar
        ))
    
    return brand_members

@router.get("/{brand_member_id}", response_model=BrandMemberSchema)
def get_brand_member(
    brand_member_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific brand member by ID."""
    brand_member = db.query(BrandMember).filter(BrandMember.id == brand_member_id).first()
    if not brand_member:
        raise HTTPException(status_code=404, detail="Brand member not found")
    return brand_member

@router.put("/{brand_member_id}", response_model=BrandMemberSchema)
def update_brand_member(
    brand_member_id: UUID,
    brand_member_update: BrandMemberUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update a brand member."""
    db_brand_member = db.query(BrandMember).filter(BrandMember.id == brand_member_id).first()
    if not db_brand_member:
        raise HTTPException(status_code=404, detail="Brand member not found")
    
    update_data = brand_member_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_brand_member, field, value)
    
    db.commit()
    db.refresh(db_brand_member)
    return db_brand_member

@router.delete("/{brand_member_id}")
def delete_brand_member(
    brand_member_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Delete a brand member."""
    db_brand_member = db.query(BrandMember).filter(BrandMember.id == brand_member_id).first()
    if not db_brand_member:
        raise HTTPException(status_code=404, detail="Brand member not found")
    
    db.delete(db_brand_member)
    db.commit()
    return {"message": "Brand member deleted successfully"} 