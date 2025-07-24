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
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str