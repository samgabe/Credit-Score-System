"""
Pydantic schemas for M-Pesa Transaction-related requests and responses.
"""
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import List, Literal


class MpesaTransactionCreate(BaseModel):
    """Schema for creating a new M-Pesa transaction."""
    user_id: UUID
    transaction_type: Literal['incoming', 'outgoing'] = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Transaction amount")
    reference: str = Field(..., min_length=1, max_length=100, description="M-Pesa reference number")
    transaction_date: datetime = Field(..., description="Date and time of transaction")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class MpesaTransactionResponse(BaseModel):
    """Schema for M-Pesa transaction response."""
    transaction_id: UUID
    user_id: UUID
    transaction_type: str
    amount: Decimal
    reference: str
    transaction_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MpesaTransactionListResponse(BaseModel):
    """Schema for list of M-Pesa transactions."""
    transactions: List[MpesaTransactionResponse]
