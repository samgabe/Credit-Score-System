"""
Fine model for the Credit Score API.
Tracks penalty charges assessed against clients.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class FineStatus(enum.Enum):
    """Enum for fine payment status."""
    unpaid = "unpaid"
    paid = "paid"


class Fine(Base):
    """
    Fine model representing penalty charges.
    
    Updated to properly align with clients (credit subjects) instead of system users.
    
    Attributes:
        id: Unique identifier (UUID)
        credit_subject_id: Foreign key to CreditSubject (client)
        amount: Fine amount
        reason: Reason for the fine
        status: Payment status (unpaid or paid)
        assessed_date: Date when fine was assessed
        paid_date: Date when fine was paid (nullable)
        created_at: Timestamp when record was created
    """
    __tablename__ = "fines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_subject_id = Column(UUID(as_uuid=True), ForeignKey("credit_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(Enum(FineStatus), nullable=False, default=FineStatus.unpaid)
    assessed_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Legacy user_id for migration (nullable)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Relationships
    # credit_subject = relationship("CreditSubject", back_populates="fines")
    # user = relationship("User", back_populates="fines")  # Legacy
    
    def __repr__(self):
        return f"<Fine(id={self.id}, credit_subject_id={self.credit_subject_id}, amount={self.amount}, status={self.status.value})>"
