"""
Pydantic schemas for Fine-related requests and responses.
"""
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional


class FineCreate(BaseModel):
    """Schema for creating a new fine."""
    user_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Fine amount")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for the fine")
    assessed_date: date = Field(..., description="Date when fine was assessed")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class FinePayment(BaseModel):
    """Schema for marking a fine as paid."""
    payment_date: date = Field(..., description="Date when fine was paid")


class FineResponse(BaseModel):
    """Schema for fine response."""
    fine_id: UUID
    user_id: UUID
    amount: Decimal
    reason: str
    status: str
    assessed_date: date
    paid_date: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FineListResponse(BaseModel):
    """Schema for list of fines."""
    fines: List[FineResponse]
