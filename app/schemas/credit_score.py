"""
Pydantic schemas for Credit Score-related requests and responses.
"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional, Dict


class CreditScoreResponse(BaseModel):
    """Schema for credit score response."""
    user_id: UUID
    score: int = Field(..., ge=0, le=850, description="Credit score value (0-850)")
    category: str = Field(..., description="Score category (Poor, Fair, Good, Excellent)")
    calculated_at: datetime
    factors: Dict[str, float] = Field(..., description="Score calculation factors")
    
    class Config:
        from_attributes = True


class CreditScoreHistoryItem(BaseModel):
    """Schema for a single credit score history item."""
    score: int
    category: str
    calculated_at: datetime
    delta: Optional[int] = None
    
    class Config:
        from_attributes = True


class CreditScoreHistoryResponse(BaseModel):
    """Schema for credit score history response."""
    user_id: UUID
    scores: List[CreditScoreHistoryItem]
