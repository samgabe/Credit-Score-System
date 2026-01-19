"""
Credit Score Repository for the Credit Score API.
Handles data access operations for CreditScore entities.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.credit_score import CreditScore


class CreditScoreRepository:
    """
    Repository for CreditScore entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the CreditScoreRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        user_id: UUID,
        score: int,
        category: str,
        repayment_factor: float,
        mpesa_factor: float,
        consistency_factor: float,
        fine_factor: float
    ) -> CreditScore:
        """
        Create a new credit score record in the database.
        
        Args:
            user_id: UUID of the user
            score: Credit score value (0-850)
            category: Score category (Poor, Fair, Good, Excellent)
            repayment_factor: Contribution from repayment history
            mpesa_factor: Contribution from M-Pesa transactions
            consistency_factor: Contribution from payment consistency
            fine_factor: Contribution from fines
            
        Returns:
            CreditScore: The created credit score object with generated UUID
            
        Validates: Requirements 3.8, 5.1
        """
        credit_score = CreditScore(
            user_id=user_id,
            score=score,
            category=category,
            repayment_factor=repayment_factor,
            mpesa_factor=mpesa_factor,
            consistency_factor=consistency_factor,
            fine_factor=fine_factor
        )
        self.db.add(credit_score)
        self.db.commit()
        self.db.refresh(credit_score)
        return credit_score
    
    def get_latest_by_user_id(self, user_id: UUID) -> Optional[CreditScore]:
        """
        Retrieve the most recent credit score for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Optional[CreditScore]: Most recent credit score if found, None otherwise
            
        Validates: Requirements 5.3, 7.1
        """
        return self.db.query(CreditScore).filter(
            CreditScore.user_id == user_id
        ).order_by(desc(CreditScore.calculated_at)).first()
    
    def get_history_by_user_id(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CreditScore]:
        """
        Retrieve credit score history for a user, optionally filtered by date range.
        
        Args:
            user_id: UUID of the user
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            List[CreditScore]: List of credit scores sorted by date in descending order
            
        Validates: Requirements 5.2, 5.4, 5.5
        """
        query = self.db.query(CreditScore).filter(CreditScore.user_id == user_id)
        
        if start_date:
            # Convert date to datetime for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(CreditScore.calculated_at >= start_datetime)
        
        if end_date:
            # Convert date to datetime for comparison (end of day)
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(CreditScore.calculated_at <= end_datetime)
        
        return query.order_by(desc(CreditScore.calculated_at)).all()
