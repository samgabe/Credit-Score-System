"""
Payment model for the Credit Score API.
Tracks comprehensive payment history for users.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentType(enum.Enum):
    """Enum for payment types."""
    repayment = "repayment"
    fine = "fine"
    other = "other"


class PaymentStatus(enum.Enum):
    """Enum for payment status."""
    completed = "completed"
    pending = "pending"
    failed = "failed"


class Payment(Base):
    """
    Payment model representing all payment transactions.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User
        amount: Payment amount
        payment_type: Type of payment (repayment, fine, other)
        status: Payment status (completed, pending, failed)
        payment_date: Date and time of payment
        created_at: Timestamp when record was created
    """
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.payment_type.value}, status={self.status.value})>"
