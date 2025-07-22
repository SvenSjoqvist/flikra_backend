from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: UUID
    password_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True 