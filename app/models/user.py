"""
User model for the Credit Score API.
Represents individual users whose credit scores are being tracked.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    User model representing an individual in the credit score system.
    
    Attributes:
        id: Unique identifier (UUID)
        fullname: User's full name
        national_id: User's unique national identification number
        phone_number: User's phone number
        email: User's email address (optional for backward compatibility)
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fullname = Column(String(255), nullable=False)
    national_id = Column(Integer, unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    repayments = relationship("Repayment", back_populates="user", cascade="all, delete-orphan")
    mpesa_transactions = relationship("MpesaTransaction", back_populates="user", cascade="all, delete-orphan")
    fines = relationship("Fine", back_populates="user", cascade="all, delete-orphan")
    credit_scores = relationship("CreditScore", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, national_id={self.national_id}, fullname={self.fullname})>"
