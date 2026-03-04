"""
Credit Score model for the Credit Score API.
Stores calculated credit scores and their component factors.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ScoreCategory(enum.Enum):
    """Enum for credit score categories."""
    Poor = "Poor"
    Fair = "Fair"
    Good = "Good"
    Excellent = "Excellent"


class CreditScore(Base):
    """
    Credit Score model representing calculated creditworthiness scores.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User
        score: Credit score value (0-850)
        category: Score category (Poor, Fair, Good, Excellent)
        repayment_factor: Contribution from repayment history (35% weight)
        mpesa_factor: Contribution from M-Pesa transactions (20% weight)
        consistency_factor: Contribution from payment consistency (25% weight)
        fine_factor: Contribution from fines (20% weight)
        calculated_at: Timestamp when score was calculated
    """
    __tablename__ = "credit_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    category = Column(String(20), nullable=False)
    repayment_factor = Column(Float, nullable=False)
    mpesa_factor = Column(Float, nullable=False)
    consistency_factor = Column(Float, nullable=False)
    fine_factor = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="credit_scores")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_credit_scores_user_calculated', 'user_id', 'calculated_at'),
    )
    
    def __repr__(self):
        return f"<CreditScore(id={self.id}, user_id={self.user_id}, score={self.score}, category={self.category})>"
