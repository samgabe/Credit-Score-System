"""
M-Pesa Transaction Repository for the Credit Score API.
Handles data access operations for MpesaTransaction entities.
"""
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.mpesa_transaction import MpesaTransaction, TransactionType


class MpesaTransactionRepository:
    """
    Repository for MpesaTransaction entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the MpesaTransactionRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        user_id: UUID,
        transaction_type: TransactionType,
        amount: float,
        reference: str,
        transaction_date: datetime
    ) -> MpesaTransaction:
        """
        Create a new M-Pesa transaction record in the database.
        
        Args:
            user_id: UUID of the user
            transaction_type: Type of transaction (incoming or outgoing)
            amount: Transaction amount
            reference: M-Pesa transaction reference number
            transaction_date: Date and time of transaction
            
        Returns:
            MpesaTransaction: The created transaction object with generated UUID
            
        Validates: Requirements 3.1, 3.4
        """
        transaction = MpesaTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            reference=reference,
            transaction_date=transaction_date
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_by_user(self, user_id: UUID) -> List[MpesaTransaction]:
        """
        Retrieve all M-Pesa transactions for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List[MpesaTransaction]: List of all M-Pesa transactions for the user
            
        Validates: Requirements 3.2, 3.4
        """
        return self.db.query(MpesaTransaction).filter(
            MpesaTransaction.user_id == user_id
        ).all()
