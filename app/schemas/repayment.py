"""
Pydantic schemas for Repayment-related requests and responses.
"""
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import List


class RepaymentCreate(BaseModel):
    """Schema for creating a new repayment."""
    user_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Repayment amount")
    loan_reference: str = Field(..., min_length=1, max_length=100, description="Loan reference number")
    due_date: date = Field(..., description="Date when payment was due")
    payment_date: date = Field(..., description="Date when payment was made")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class RepaymentResponse(BaseModel):
    """Schema for repayment response."""
    repayment_id: UUID
    user_id: UUID
    amount: Decimal
    loan_reference: str
    due_date: date
    payment_date: date
    status: str
    days_overdue: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RepaymentListResponse(BaseModel):
    """Schema for list of repayments."""
    repayments: List[RepaymentResponse]
