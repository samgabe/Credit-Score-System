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
            List[CreditScore]: List of credit scores for user
        """
        query = self.db.query(CreditScore).filter(CreditScore.user_id == user_id)
        
        if start_date:
            # Convert date to datetime for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(CreditScore.calculated_at >= start_datetime)
        
        if end_date:
            # Convert date to datetime for comparison
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(CreditScore.calculated_at <= end_datetime)
        
        return query.order_by(desc(CreditScore.calculated_at)).all()
    
    def get_all_scores(self) -> List[CreditScore]:
        """
        Retrieve all credit scores from database.
        
        Returns:
            List[CreditScore]: List of all credit scores in database
        """
        return self.db.query(CreditScore).order_by(desc(CreditScore.calculated_at)).all()
    
    def get_by_user_id(self, user_id: UUID) -> List[CreditScore]:
        """
        Retrieve all credit scores for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[CreditScore]: List of credit scores for user
        """
        return self.db.query(CreditScore).filter(
            CreditScore.user_id == user_id
        ).order_by(desc(CreditScore.calculated_at)).all()
    
    def get_scores_by_date_range(self, start_date: datetime, end_date: datetime) -> List[CreditScore]:
        """
        Retrieve credit scores created within a specific date range.
        
        Args:
            start_date: Start datetime for filtering (inclusive)
            end_date: End datetime for filtering (inclusive)
            
        Returns:
            List[CreditScore]: List of credit scores within the date range
        """
        return self.db.query(CreditScore).filter(
            CreditScore.calculated_at >= start_date,
            CreditScore.calculated_at <= end_date
        ).order_by(desc(CreditScore.calculated_at)).all()
    
    def get_recent_scores(self, limit: int = 10) -> List[CreditScore]:
        """
        Retrieve the most recent credit scores.
        
        Args:
            limit: Maximum number of scores to return
            
        Returns:
            List[CreditScore]: List of recent credit scores
        """
        return self.db.query(CreditScore).order_by(
            desc(CreditScore.calculated_at)
        ).limit(limit).all()
    
    def get_by_credit_subject_id(self, subject_id: str) -> List[CreditScore]:
        """
        Retrieve credit scores for a specific credit subject.
        
        Args:
            subject_id: Credit subject ID
            
        Returns:
            List[CreditScore]: List of credit scores for the subject
        """
        return self.db.query(CreditScore).filter(
            CreditScore.credit_subject_id == subject_id
        ).order_by(desc(CreditScore.calculated_at)).all()
    
    def get_latest_by_credit_subject_id(self, subject_id: str) -> Optional[CreditScore]:
        """
        Retrieve the latest credit score for a specific credit subject.
        
        Args:
            subject_id: Credit subject ID
            
        Returns:
            Optional[CreditScore]: Latest credit score for the subject
        """
        return self.db.query(CreditScore).filter(
            CreditScore.credit_subject_id == subject_id
        ).order_by(desc(CreditScore.calculated_at)).first()
    
    def create_for_subject(
        self,
        subject_id: UUID,
        score: int,
        category: str,
        repayment_factor: float,
        mpesa_factor: float,
        consistency_factor: float,
        fine_factor: float
    ) -> CreditScore:
        """
        Create a new credit score for a credit subject.
        
        Args:
            subject_id: UUID of the credit subject
            score: Credit score value (0-850)
            category: Score category (Poor, Fair, Good, Excellent)
            repayment_factor: Repayment history contribution
            mpesa_factor: M-Pesa transaction contribution
            consistency_factor: Payment consistency contribution
            fine_factor: Fine history contribution
            
        Returns:
            CreditScore: Created credit score record
        """
        credit_score = CreditScore(
            credit_subject_id=subject_id,
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
