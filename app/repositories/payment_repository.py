"""
Payment Repository for the Credit Score API.
Handles data access operations for Payment entities.
"""
from typing import List
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.payment import Payment, PaymentType, PaymentStatus


class PaymentRepository:
    """
    Repository for Payment entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the PaymentRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        user_id: UUID,
        amount: float,
        payment_type: PaymentType,
        status: PaymentStatus,
        payment_date: datetime
    ) -> Payment:
        """
        Create a new payment record in the database.
        
        Args:
            user_id: UUID of the user making the payment
            amount: Payment amount
            payment_type: Type of payment (repayment, fine, other)
            status: Payment status (completed, pending, failed)
            payment_date: Date and time of payment
            
        Returns:
            Payment: The created payment object with generated UUID
            
        Validates: Requirements 4.1
        """
        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            status=status,
            payment_date=payment_date
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_by_user(self, user_id: UUID) -> List[Payment]:
        """
        Retrieve all payments for a specific user, sorted by date in descending order.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[Payment]: List of all payments for the user, most recent first
            
        Validates: Requirements 4.2
        """
        return self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(desc(Payment.payment_date)).all()
    
    def get_by_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Payment]:
        """
        Retrieve payments for a user within a specific date range,
        sorted by date in descending order.
        
        Args:
            user_id: UUID of the user
            start_date: Start date of the range (inclusive)
            end_date: End date of the range (inclusive)
            
        Returns:
            List[Payment]: List of payments within the date range, most recent first
            
        Validates: Requirements 4.2, 4.3
        """
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        return self.db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.payment_date >= start_datetime,
            Payment.payment_date <= end_datetime
        ).order_by(desc(Payment.payment_date)).all()
