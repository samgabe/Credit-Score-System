"""
M-Pesa Router for the Credit Score API.
Handles M-Pesa transaction endpoints including recording and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.mpesa_transaction import MpesaTransactionCreate, MpesaTransactionResponse, MpesaTransactionListResponse
from app.schemas.error import ErrorResponse
from app.services.transaction_processor import TransactionProcessor
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.user_repository import UserRepository
from datetime import datetime

router = APIRouter()


@router.post(
    "/mpesa/transactions",
    response_model=MpesaTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid data"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["mpesa"]
)
def create_mpesa_transaction(
    transaction_data: MpesaTransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Record a new M-Pesa transaction.
    
    Processes and stores an M-Pesa transaction with type validation.
    
    Args:
        transaction_data: M-Pesa transaction data (user_id, type, amount, reference, date)
        db: Database session (injected)
        
    Returns:
        MpesaTransactionResponse: Created transaction with details
        
    Validates: Requirements 3.1
    """
    try:
        # Verify user exists
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(transaction_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {transaction_data.user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(transaction_data.user_id)}
                }
            )
        
        # Process the M-Pesa transaction
        processor = TransactionProcessor(db)
        transaction = processor.process_mpesa_transaction(
            user_id=transaction_data.user_id,
            transaction_type=transaction_data.transaction_type,
            amount=float(transaction_data.amount),
            reference=transaction_data.reference,
            transaction_date=transaction_data.transaction_date
        )
        
        return MpesaTransactionResponse(
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount,
            reference=transaction.reference,
            transaction_date=transaction.transaction_date,
            created_at=transaction.created_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TRANSACTION_TYPE",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"transaction_type": transaction_data.transaction_type}
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while creating the M-Pesa transaction",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/mpesa/transactions/{user_id}",
    response_model=MpesaTransactionListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["mpesa"]
)
def get_mpesa_transactions(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get M-Pesa transaction history for a user.
    
    Retrieves all M-Pesa transactions for the specified user.
    
    Args:
        user_id: UUID of the user
        db: Database session (injected)
        
    Returns:
        MpesaTransactionListResponse: List of all M-Pesa transactions for the user
        
    Validates: Requirements 3.2
    """
    try:
        # Verify user exists
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(user_id)}
                }
            )
        
        # Get M-Pesa transaction history
        mpesa_repo = MpesaTransactionRepository(db)
        transactions = mpesa_repo.get_by_user(user_id)
        
        transaction_responses = [
            MpesaTransactionResponse(
                transaction_id=t.id,
                user_id=t.user_id,
                transaction_type=t.transaction_type.value,
                amount=t.amount,
                reference=t.reference,
                transaction_date=t.transaction_date,
                created_at=t.created_at
            )
            for t in transactions
        ]
        
        return MpesaTransactionListResponse(transactions=transaction_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving M-Pesa transactions",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )
