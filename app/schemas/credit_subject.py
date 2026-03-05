"""
Credit Subject schemas for the Credit Score API.
Handles data validation and serialization for credit subjects.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class CreditSubjectCreate(BaseModel):
    """Schema for creating a new credit subject."""
    full_name: str = Field(..., min_length=1, max_length=255, description="Subject's full name")
    national_id: Optional[str] = Field(None, max_length=50, description="National identification number")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    external_id: Optional[str] = Field(None, max_length=255, description="External reference ID (from CSV import)")

    class Config:
        from_attributes = True


class CreditSubjectUpdate(BaseModel):
    """Schema for updating a credit subject."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    national_id: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    external_id: Optional[str] = Field(None, max_length=255)

    class Config:
        from_attributes = True


class CreditSubjectResponse(BaseModel):
    """Schema for credit subject response."""
    id: UUID
    full_name: str
    national_id: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreditSubjectSearch(BaseModel):
    """Schema for credit subject search parameters."""
    query: Optional[str] = Field(None, description="Search query for name, email, phone, or national ID")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class CreditSubjectSummary(BaseModel):
    """Schema for credit subject summary with latest score."""
    id: UUID
    full_name: str
    national_id: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    latest_score: Optional[int] = Field(None, description="Latest credit score")
    latest_score_category: Optional[str] = Field(None, description="Latest score category")
    latest_score_date: Optional[datetime] = Field(None, description="Latest score calculation date")
    created_at: datetime

    class Config:
        from_attributes = True
