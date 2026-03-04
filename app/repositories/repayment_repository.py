"""
Repayment Repository for the Credit Score API.
Handles data access operations for Repayment entities.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from app.models.repayment import Repayment, RepaymentStatus


class RepaymentRepository:
    """
    Repository for Repayment entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the RepaymentRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        user_id: UUID,
        amount: float,
        loan_reference: str,
        due_date: date,
        payment_date: date,
        status: RepaymentStatus,
        days_overdue: int = 0
    ) -> Repayment:
        """
        Create a new repayment record in the database.
        
        Args:
            user_id: UUID of the user making the repayment
            amount: Repayment amount
            loan_reference: Reference number for the loan
            due_date: Date when payment was due
            payment_date: Date when payment was made
            status: Payment status (on_time or late)
            days_overdue: Number of days payment was overdue (default 0)
            
        Returns:
            Repayment: The created repayment object with generated UUID
            
        Validates: Requirements 2.1, 2.4
        """
        repayment = Repayment(
            user_id=user_id,
            amount=amount,
            loan_reference=loan_reference,
            due_date=due_date,
            payment_date=payment_date,
            status=status,
            days_overdue=days_overdue
        )
        self.db.add(repayment)
        self.db.commit()
        self.db.refresh(repayment)
        return repayment
    
    def get_by_user(self, user_id: UUID) -> List[Repayment]:
        """
        Retrieve all repayments for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[Repayment]: List of all repayments for the user
            
        Validates: Requirements 2.5
        """
        return self.db.query(Repayment).filter(Repayment.user_id == user_id).all()
    
    def get_by_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Repayment]:
        """
        Retrieve repayments for a user within a specific date range.
        
        Args:
            user_id: UUID of the user
            start_date: Start date of the range (inclusive)
            end_date: End date of the range (inclusive)
            
        Returns:
            List[Repayment]: List of repayments within the date range
            
        Validates: Requirements 2.4, 2.5
        """
        return self.db.query(Repayment).filter(
            Repayment.user_id == user_id,
            Repayment.payment_date >= start_date,
            Repayment.payment_date <= end_date
        ).all()
