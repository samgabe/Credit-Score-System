"""
M-Pesa Transaction model for the Credit Score API.
Tracks mobile money transactions from the M-Pesa payment system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionType(enum.Enum):
    """Enum for M-Pesa transaction types."""
    incoming = "incoming"
    outgoing = "outgoing"


class MpesaTransaction(Base):
    """
    M-Pesa Transaction model representing mobile money transactions.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User
        transaction_type: Type of transaction (incoming or outgoing)
        amount: Transaction amount
        reference: M-Pesa transaction reference number
        transaction_date: Date and time of transaction
        created_at: Timestamp when record was created
    """
    __tablename__ = "mpesa_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reference = Column(String(100), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="mpesa_transactions")
    
    def __repr__(self):
        return f"<MpesaTransaction(id={self.id}, user_id={self.user_id}, type={self.transaction_type.value}, amount={self.amount})>"
