"""
Fine model for the Credit Score API.
Tracks penalty charges assessed against users.
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
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User
        amount: Fine amount
        reason: Reason for the fine
        status: Payment status (unpaid or paid)
        assessed_date: Date when fine was assessed
        paid_date: Date when fine was paid (nullable)
        created_at: Timestamp when record was created
    """
    __tablename__ = "fines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(Enum(FineStatus), nullable=False, default=FineStatus.unpaid)
    assessed_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="fines")
    
    def __repr__(self):
        return f"<Fine(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status.value})>"
