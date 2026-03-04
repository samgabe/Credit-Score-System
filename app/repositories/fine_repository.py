"""
Fine Repository for the Credit Score API.
Handles data access operations for Fine entities.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from app.models.fine import Fine, FineStatus


class FineRepository:
    """
    Repository for Fine entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the FineRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        user_id: UUID,
        amount: float,
        reason: str,
        assessed_date: date
    ) -> Fine:
        """
        Create a new fine record in the database.
        
        Args:
            user_id: UUID of the user being fined
            amount: Fine amount
            reason: Reason for the fine
            assessed_date: Date when fine was assessed
            
        Returns:
            Fine: The created fine object with generated UUID
            
        Validates: Requirements 5.1, 5.4
        """
        fine = Fine(
            user_id=user_id,
            amount=amount,
            reason=reason,
            assessed_date=assessed_date,
            status=FineStatus.unpaid
        )
        self.db.add(fine)
        self.db.commit()
        self.db.refresh(fine)
        return fine
    
    def get_by_user(self, user_id: UUID) -> List[Fine]:
        """
        Retrieve all fines for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[Fine]: List of all fines for the user with their payment status
            
        Validates: Requirements 5.3, 5.4
        """
        return self.db.query(Fine).filter(Fine.user_id == user_id).all()
    
    def update_status(
        self,
        fine_id: UUID,
        status: FineStatus,
        paid_date: Optional[date] = None
    ) -> Optional[Fine]:
        """
        Update the status of a fine.
        
        Args:
            fine_id: UUID of the fine to update
            status: New status (unpaid or paid)
            paid_date: Date when fine was paid (required if status is paid)
            
        Returns:
            Optional[Fine]: Updated fine object if found, None otherwise
            
        Validates: Requirements 5.2, 5.4
        """
        fine = self.db.query(Fine).filter(Fine.id == fine_id).first()
        if fine:
            fine.status = status
            if status == FineStatus.paid and paid_date:
                fine.paid_date = paid_date
            self.db.commit()
            self.db.refresh(fine)
        return fine
