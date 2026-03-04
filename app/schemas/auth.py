"""
Authentication schemas for the Credit Score API.
Handles user authentication, registration, and token management.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """Schema for user registration request."""
    fullname: str
    email: EmailStr
    password: str
    national_id: int
    phone_number: str


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: str
    email: str


class UserResponse(BaseModel):
    """Schema for authenticated user response."""
    id: str
    fullname: str
    email: str
    national_id: int
    phone_number: str
    created_at: str
    updated_at: str


class ChangePassword(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str
