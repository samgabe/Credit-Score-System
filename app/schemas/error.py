"""
Pydantic schemas for error responses.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "USER_NOT_FOUND",
                "message": "User with ID 123e4567-e89b-12d3-a456-426614174000 does not exist",
                "timestamp": "2026-01-15T10:30:00Z",
                "details": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }
