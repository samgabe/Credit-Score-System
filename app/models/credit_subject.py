"""
Credit Subject model for the Credit Score API.
Represents individuals whose credit scores are calculated and analyzed.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CreditSubject(Base):
    """
    Credit Subject model representing individuals being scored.
    
    These are NOT system users - they are data subjects whose credit
    scores are calculated by system operators.
    
    Attributes:
        id: Unique identifier (UUID)
        external_id: External reference ID (from CSV import)
        full_name: Subject's full name
        national_id: National identification number
        phone_number: Phone number
        email: Email address
        created_at: Timestamp when subject was created
        updated_at: Timestamp when subject was last updated
    """
    __tablename__ = "credit_subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), nullable=True, index=True)  # For CSV import reference
    full_name = Column(String(255), nullable=False)
    national_id = Column(String(50), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    # credit_scores = relationship("CreditScore", back_populates="credit_subject", cascade="all, delete-orphan")
    # mpesa_statements = relationship("MpesaStatement", back_populates="credit_subject", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CreditSubject(id={self.id}, full_name={self.full_name})>"
