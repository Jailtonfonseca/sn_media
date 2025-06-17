from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    google_user_id: Optional[str] = None

    class Config:
        orm_mode = True # Compatibility com SQLAlchemy models, pydantic v1
        # from_attributes = True # para pydantic v2
