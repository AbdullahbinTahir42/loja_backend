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



class ItemBase(BaseModel):
    """Shared fields used in item-related schemas."""
 
    name: str
    description: str
    price: int
    quantity: int
    category: str

class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    
    
    @field_validator('price', 'quantity')
    def validate_positive(cls, v):
        """Ensure price and quantity are positive integers."""
        if v < 0:
            raise ValueError("Must be a positive integer")
        return v

class Item(ItemBase):
    """Schema for item data returned after creation."""
    id: int
    image_name: str  # Optional field for image name

    class Config:
        from_attributes = True  # Allows Pydantic to work with SQLAlchemy models