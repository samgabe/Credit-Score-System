"""
System User schemas for the Credit Score API.
Handles data validation and serialization for system users.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SystemUserRegister(BaseModel):
    """Schema for registering a new system user."""
    fullname: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=100, description="User's password")
    role: Optional[str] = Field("operator", description="User role (admin, operator, viewer)")


class SystemUserLogin(BaseModel):
    """Schema for system user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class SystemUserResponse(BaseModel):
    """Schema for system user response."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemUserUpdate(BaseModel):
    """Schema for updating a system user."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, description="User role (admin, operator, viewer)")
    is_active: Optional[bool] = None


class SystemPasswordChange(BaseModel):
    """Schema for changing system user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
