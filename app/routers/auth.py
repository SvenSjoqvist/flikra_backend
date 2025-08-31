from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from app.db import get_db
from app.auth import (
    brand_login, 
    create_access_token, 
    decode_token, 
    get_user_from_cookie,
    BrandLoginRequest,
    BrandLoginResponse
)

router = APIRouter()

@router.post("/brand-login", response_model=BrandLoginResponse)
def login_brand(
    login_data: BrandLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Brand login endpoint.
    
    Authenticates user with email/password, checks brand membership,
    and sets session cookie if successful.
    """
    try:
        # Authenticate user and get brand info
        auth_result = brand_login(login_data.email, login_data.password, db)
        
        # Create JWT token
        token_data = {
            "sub": str(auth_result["user"]["id"]),
            "email": auth_result["user"]["email"],
            "brand_id": str(auth_result["brand"]["id"]),
            "role": auth_result["brand_member"]["role"]
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=24)  # 24 hour session
        )
        
        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        return BrandLoginResponse(
            success=True,
            message="Login successful",
            user=auth_result["user"],
            brand=auth_result["brand"],
            token=access_token  # Also return token for client-side use if needed
        )
        
    except HTTPException as e:
        return BrandLoginResponse(
            success=False,
            message=e.detail
        )
    except Exception as e:
        return BrandLoginResponse(
            success=False,
            message="Login failed. Please try again."
        )

@router.post("/logout")
def logout_brand(response: Response):
    """
    Logout endpoint - clears the session cookie.
    """
    response.delete_cookie(key="session_token")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
def get_current_session_user(current_user = Depends(get_user_from_cookie)):
    """
    Get current user from session cookie.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "avatar": current_user.avatar
        }
    }

@router.get("/verify-session")
def verify_session(current_user = Depends(get_user_from_cookie)):
    """
    Verify if current session is valid.
    """
    if not current_user:
        return {"valid": False, "message": "No valid session"}
    
    return {"valid": True, "user_id": str(current_user.id)} 