from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

# --- Token Schemas for Authentication ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- User Schemas ---
class UserBase(BaseModel):
    """Shared fields used in user-related schemas."""
    email: EmailStr
    full_name: str
    password: str

class UserCreate(UserBase):
    """Schema for user registration."""
    
    confirmPassword: str

class S_User(UserBase):
    """Schema for user data returned after registration."""
    role: str

    class Config:
        from_attributes = True  # Allows Pydantic to work with SQLAlchemy models

class UserLogin(BaseModel):
    """Schema for user login."""
    username: EmailStr
    password: str