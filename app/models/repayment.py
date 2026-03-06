"""
Repayment model for the Credit Score API.
Tracks loan repayments made by clients.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RepaymentStatus(enum.Enum):
    """Enum for repayment status."""
    on_time = "on_time"
    late = "late"


class Repayment(Base):
    """
    Repayment model representing a loan repayment transaction.
    
    Updated to properly align with clients (credit subjects) instead of system users.
    
    Attributes:
        id: Unique identifier (UUID)
        credit_subject_id: Foreign key to CreditSubject (client)
        amount: Repayment amount
        loan_reference: Reference number for the loan
        due_date: Date when payment was due
        payment_date: Date when payment was made
        status: Payment status (on_time or late)
        days_overdue: Number of days payment was overdue (0 if on time)
        created_at: Timestamp when record was created
    """
    __tablename__ = "repayments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_subject_id = Column(UUID(as_uuid=True), ForeignKey("credit_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    loan_reference = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=False)
    status = Column(Enum(RepaymentStatus), nullable=False)
    days_overdue = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    # credit_subject = relationship("CreditSubject", back_populates="repayments")
    
    def __repr__(self):
        return f"<Repayment(id={self.id}, credit_subject_id={self.credit_subject_id}, amount={self.amount}, status={self.status.value})>"
