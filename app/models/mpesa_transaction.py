"""
M-Pesa Transaction model for the Credit Score API.
Tracks mobile money transactions from the M-Pesa payment system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MpesaTransaction(Base):
    """
    M-Pesa Transaction model representing mobile money transactions.
    
    Updated to support individual client statement analysis.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User (legacy, kept for compatibility)
        credit_subject_id: Foreign key to CreditSubject (new, for individual analysis)
        statement_id: Foreign key to M-Pesa Statement (new)
        transaction_type: Type of transaction (incoming or outgoing)
        amount: Transaction amount
        reference: M-Pesa transaction reference number
        receipt_no: M-Pesa receipt number
        completion_time: Date and time of transaction
        details: Transaction details
        recipient: Transaction recipient
        status: Transaction status
        is_paid_in: Whether this is a paid-in transaction
        is_paid_out: Whether this is a paid-out transaction
        transaction_date: Date and time of transaction (legacy)
        created_at: Timestamp when record was created
    """
    __tablename__ = "mpesa_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    credit_subject_id = Column(UUID(as_uuid=True), ForeignKey("credit_subjects.id"), nullable=True, index=True)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("mpesa_statements.id"), nullable=True, index=True)
    
    # Legacy fields (kept for compatibility)
    transaction_type = Column(String(50), nullable=True)
    reference = Column(String(100), nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    
    # New fields for individual statement analysis
    receipt_no = Column(String(50), nullable=True)
    completion_time = Column(DateTime, nullable=True)
    details = Column(Text, nullable=True)
    recipient = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True, default="COMPLETED")
    is_paid_in = Column(Boolean, default=False, nullable=False)
    is_paid_out = Column(Boolean, default=False, nullable=False)
    
    # Common fields
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships - simplified for now
    # user = relationship("User", back_populates="mpesa_transactions")
    # credit_subject = relationship("CreditSubject", backref="mpesa_transactions")
    # statement relationship will be added later
    
    def __repr__(self):
        return f"<MpesaTransaction(id={self.id}, credit_subject_id={self.credit_subject_id}, amount={self.amount})>"
