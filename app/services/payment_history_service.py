"""
Payment History Service for the Credit Score API.
Manages comprehensive payment history and consistency metrics.
"""
from uuid import UUID
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.repositories.payment_repository import PaymentRepository


class PaymentHistoryService:
    """
    Service for managing payment history and calculating consistency metrics.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the PaymentHistoryService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.payment_repo = PaymentRepository(db)
    
    def add_to_history(
        self,
        user_id: UUID,
        amount: float,
        payment_type: PaymentType,
        status: PaymentStatus,
        payment_date: datetime
    ) -> Payment:
        """
        Add a payment to the user's payment history.
        
        Records all payments (repayments, fines, other) in a unified history.
        
        Args:
            user_id: UUID of the user making the payment
            amount: Payment amount
            payment_type: Type of payment (repayment, fine, other)
            status: Payment status (completed, pending, failed)
            payment_date: Date and time of payment
            
        Returns:
            Payment: The created payment record
            
        Validates: Requirements 4.1
        """
        payment = self.payment_repo.create(
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            status=status,
            payment_date=payment_date
        )
        
        return payment
    
    def get_history(self, user_id: UUID) -> List[Payment]:
        """
        Retrieve payment history for a user, sorted by date in descending order.
        
        Returns all payments with most recent first.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[Payment]: List of payments sorted by date (most recent first)
            
        Validates: Requirements 4.2
        """
        payments = self.payment_repo.get_by_user(user_id)
        return payments
    
    def calculate_consistency_metrics(self, user_id: UUID) -> Dict[str, float]:
        """
        Calculate payment consistency metrics for a user.
        
        Metrics include:
        - completion_rate: Percentage of completed payments
        - average_interval_days: Average days between payments
        - interval_std_dev: Standard deviation of payment intervals
        - total_payments: Total number of payments
        - completed_payments: Number of completed payments
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dict[str, float]: Dictionary containing consistency metrics
            
        Validates: Requirements 4.4
        """
        payments = self.payment_repo.get_by_user(user_id)
        
        if not payments:
            return {
                "completion_rate": 0.0,
                "average_interval_days": 0.0,
                "interval_std_dev": 0.0,
                "total_payments": 0,
                "completed_payments": 0
            }
        
        # Calculate completion rate
        total_payments = len(payments)
        completed_payments = sum(1 for p in payments if p.status == PaymentStatus.completed)
        completion_rate = (completed_payments / total_payments) * 100 if total_payments > 0 else 0.0
        
        # Calculate payment intervals (if enough payments)
        average_interval_days = 0.0
        interval_std_dev = 0.0
        
        if len(payments) >= 2:
            # Sort payments by date (oldest first for interval calculation)
            sorted_payments = sorted(payments, key=lambda p: p.payment_date)
            
            # Calculate intervals between consecutive payments (in days)
            intervals = []
            for i in range(1, len(sorted_payments)):
                interval = (sorted_payments[i].payment_date - sorted_payments[i-1].payment_date).days
                intervals.append(interval)
            
            # Calculate average interval
            if intervals:
                average_interval_days = sum(intervals) / len(intervals)
                
                # Calculate standard deviation
                if len(intervals) > 1:
                    mean = average_interval_days
                    variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
                    interval_std_dev = variance ** 0.5
        
        return {
            "completion_rate": round(completion_rate, 2),
            "average_interval_days": round(average_interval_days, 2),
            "interval_std_dev": round(interval_std_dev, 2),
            "total_payments": total_payments,
            "completed_payments": completed_payments
        }
