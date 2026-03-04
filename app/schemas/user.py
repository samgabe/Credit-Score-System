"""
Pydantic schemas for User-related requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
import re


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    fullname: str = Field(..., min_length=1, max_length=255, description="User's full name")
    national_id: int = Field(..., description="User's unique national identification number")
    phone_number: str = Field(..., min_length=10, max_length=20, description="User's phone number")
    email: Optional[EmailStr] = Field(None, description="User's email address (optional)")
    
    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, v: str) -> str:
        """Validate fullname is non-empty after trimming."""
        if not v or not v.strip():
            raise ValueError('Fullname must be non-empty')
        if len(v) < 1 or len(v) > 255:
            raise ValueError('Fullname must be between 1 and 255 characters')
        return v.strip()
    
    @field_validator('national_id')
    @classmethod
    def validate_national_id(cls, v: int) -> int:
        """Validate national_id is a positive integer."""
        if v <= 0:
            raise ValueError('National ID must be a positive integer')
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone_number is numeric with optional country code."""
        if not v or not v.strip():
            raise ValueError('Phone number must be non-empty')
        if len(v) < 10 or len(v) > 20:
            raise ValueError('Phone number must be between 10 and 20 characters')
        # Allow digits, optional + at start, optional spaces and hyphens
        if not re.match(r'^\+?[0-9\s\-]+$', v.strip()):
            raise ValueError('Phone number must be numeric with optional country code (+)')
        return v.strip()


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    fullname: str
    national_id: int
    phone_number: str
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    fullname: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, description="User's phone number")
    
    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, v: Optional[str]) -> Optional[str]:
        """Validate fullname is non-empty after trimming if provided."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Fullname must be non-empty')
        if len(v) < 1 or len(v) > 255:
            raise ValueError('Fullname must be between 1 and 255 characters')
        return v.strip()
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone_number is numeric with optional country code if provided."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Phone number must be non-empty')
        if len(v) < 10 or len(v) > 20:
            raise ValueError('Phone number must be between 10 and 20 characters')
        # Allow digits, optional + at start, optional spaces and hyphens
        if not re.match(r'^\+?[0-9\s\-]+$', v.strip()):
            raise ValueError('Phone number must be numeric with optional country code (+)')
        return v.strip()
