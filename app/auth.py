from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import bcrypt
from datetime import datetime, timedelta
from app.db import get_db
from app.models import User, BrandMember, Brand

SECRET_KEY = "yoursecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Pydantic models for login
class BrandLoginRequest(BaseModel):
    email: str
    password: str

class BrandLoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    brand: Optional[dict] = None
    token: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token - placeholder for future JWT implementation"""
    # For now, return None since we're using API key authentication
    # This can be updated later when implementing JWT user authentication
    return None

def brand_login(email: str, password: str, db: Session) -> dict:
    """Brand login logic - returns user and brand info if authentication successful."""
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user has password hash
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Account not properly set up")
    
    # Verify password
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active (has any active brand memberships) - case insensitive
    brand_member = db.query(BrandMember).filter(
        BrandMember.user_id == user.id,
        BrandMember.status.in_(["active", "ACTIVE", "Active"])
    ).first()
    
    if not brand_member:
        raise HTTPException(status_code=403, detail="Account is not active or has no brand access")
    
    # Get brand information
    brand = db.query(Brand).filter(Brand.id == brand_member.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Associated brand not found")
    
    # Check if brand is active - case insensitive
    if brand.status not in ["active", "ACTIVE", "Active", "pending", "PENDING", "Pending"]:
        raise HTTPException(status_code=403, detail="Brand account is not active")
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "created_at": user.created_at
        },
        "brand": {
            "id": brand.id,
            "name": brand.name,
            "industry": brand.industry,
            "status": brand.status,
            "plan": brand.plan
        },
        "brand_member": {
            "role": brand_member.role,
            "status": brand_member.status
        }
    }

def get_user_from_cookie(session_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    """Get user from session cookie token."""
    if not session_token:
        return None
    
    payload = decode_token(session_token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user
