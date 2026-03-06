"""
Credit Score model for the Credit Score API.
Stores calculated credit scores and their component factors.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, UUID
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
    
    Updated to properly align with clients (credit subjects) as primary relationship.
    
    Attributes:
        id: Unique identifier (UUID)
        credit_subject_id: Foreign key to CreditSubject (client) - PRIMARY
        user_id: Foreign key to User (legacy, for migration)
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
    credit_subject_id = Column(UUID(as_uuid=True), ForeignKey("credit_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Legacy, nullable for migration
    score = Column(Integer, nullable=False)
    category = Column(String(20), nullable=False)
    repayment_factor = Column(Float, nullable=False)
    mpesa_factor = Column(Float, nullable=False)
    consistency_factor = Column(Float, nullable=False)
    fine_factor = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    # credit_subject = relationship("CreditSubject", back_populates="credit_scores")
    # user = relationship("User", back_populates="credit_scores")  # Legacy
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_credit_scores_subject_calculated', 'credit_subject_id', 'calculated_at'),
        Index('ix_credit_scores_user_calculated', 'user_id', 'calculated_at'),  # Legacy
    )
    
    def __repr__(self):
        return f"<CreditScore(id={self.id}, credit_subject_id={self.credit_subject_id}, score={self.score}, category={self.category})>"


# Set up the CreditSubject relationship after both models are defined
def setup_credit_subject_relationship():
    """Set up the relationship between CreditScore and CreditSubject."""
    # from app.models.credit_subject import CreditSubject
    # CreditScore.credit_subject = relationship("CreditSubject", back_populates="credit_scores")
    pass
