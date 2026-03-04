"""
Transaction Processor Service for the Credit Score API.
Handles processing of financial transactions including repayments, M-Pesa transactions, and fines.
"""
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.repayment import RepaymentStatus
from app.models.mpesa_transaction import TransactionType
from app.models.fine import FineStatus
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.fine_repository import FineRepository


class TransactionProcessor:
    """
    Service for processing financial transactions.
    Handles business logic for repayments, M-Pesa transactions, and fines.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the TransactionProcessor with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repayment_repo = RepaymentRepository(db)
        self.mpesa_repo = MpesaTransactionRepository(db)
        self.fine_repo = FineRepository(db)
    
    def process_repayment(
        self,
        user_id: UUID,
        amount: float,
        loan_reference: str,
        due_date: date,
        payment_date: date
    ):
        """
        Process a repayment transaction with on-time/late classification.
        
        Classifies the repayment as on-time or late based on payment_date vs due_date.
        Calculates days_overdue for late payments.
        
        Args:
            user_id: UUID of the user making the repayment
            amount: Repayment amount
            loan_reference: Reference number for the loan
            due_date: Date when payment was due
            payment_date: Date when payment was made
            
        Returns:
            Repayment: The created repayment object
            
        Validates: Requirements 2.1, 2.2, 2.3
        """
        # Determine if payment is on-time or late
        if payment_date <= due_date:
            status = RepaymentStatus.on_time
            days_overdue = 0
        else:
            status = RepaymentStatus.late
            days_overdue = (payment_date - due_date).days
        
        # Create the repayment record
        repayment = self.repayment_repo.create(
            user_id=user_id,
            amount=amount,
            loan_reference=loan_reference,
            due_date=due_date,
            payment_date=payment_date,
            status=status,
            days_overdue=days_overdue
        )
        
        return repayment
    
    def process_mpesa_transaction(
        self,
        user_id: UUID,
        transaction_type: str,
        amount: float,
        reference: str,
        transaction_date: datetime
    ):
        """
        Process an M-Pesa transaction with type validation.
        
        Validates that transaction_type is either 'incoming' or 'outgoing'.
        
        Args:
            user_id: UUID of the user
            transaction_type: Type of transaction ('incoming' or 'outgoing')
            amount: Transaction amount
            reference: M-Pesa transaction reference number
            transaction_date: Date and time of transaction
            
        Returns:
            MpesaTransaction: The created transaction object
            
        Raises:
            ValueError: If transaction_type is not 'incoming' or 'outgoing'
            
        Validates: Requirements 3.1, 3.3
        """
        # Validate transaction type
        if transaction_type not in ['incoming', 'outgoing']:
            raise ValueError(f"Invalid transaction type: {transaction_type}. Must be 'incoming' or 'outgoing'.")
        
        # Convert string to enum
        trans_type_enum = TransactionType.incoming if transaction_type == 'incoming' else TransactionType.outgoing
        
        # Create the M-Pesa transaction record
        transaction = self.mpesa_repo.create(
            user_id=user_id,
            transaction_type=trans_type_enum,
            amount=amount,
            reference=reference,
            transaction_date=transaction_date
        )
        
        return transaction
    
    def process_fine(
        self,
        user_id: UUID,
        amount: float,
        reason: str,
        assessed_date: date
    ):
        """
        Process a fine assessment.
        
        Creates a new fine record with status 'unpaid'.
        
        Args:
            user_id: UUID of the user being fined
            amount: Fine amount
            reason: Reason for the fine
            assessed_date: Date when fine was assessed
            
        Returns:
            Fine: The created fine object
            
        Validates: Requirements 5.1
        """
        fine = self.fine_repo.create(
            user_id=user_id,
            amount=amount,
            reason=reason,
            assessed_date=assessed_date
        )
        
        return fine
    
    def mark_fine_paid(
        self,
        fine_id: UUID,
        payment_date: date
    ):
        """
        Mark a fine as paid.
        
        Updates the fine status to 'paid' and sets the paid_date.
        
        Args:
            fine_id: UUID of the fine to mark as paid
            payment_date: Date when fine was paid
            
        Returns:
            Fine: The updated fine object, or None if fine not found
            
        Validates: Requirements 5.2
        """
        fine = self.fine_repo.update_status(
            fine_id=fine_id,
            status=FineStatus.paid,
            paid_date=payment_date
        )
        
        return fine
