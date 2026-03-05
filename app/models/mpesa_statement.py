"""
M-Pesa Statement model for individual client statements
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MpesaStatement(Base):
    """Individual client M-Pesa statement"""
    __tablename__ = "mpesa_statements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_subject_id = Column(UUID(as_uuid=True), ForeignKey("credit_subjects.id"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    statement_date = Column(DateTime, nullable=False)
    statement_period = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    # credit_subject = relationship("CreditSubject", back_populates="mpesa_statements")
    # transactions = relationship("MpesaTransaction", backref="transactions")

    def __repr__(self):
        return f"<MpesaStatement(id={self.id}, credit_subject_id={self.credit_subject_id}, is_active={self.is_active})>"
