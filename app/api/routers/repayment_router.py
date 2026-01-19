"""
Repayment Router for the Credit Score API.
Handles repayment tracking endpoints including recording and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.repayment import RepaymentCreate, RepaymentResponse, RepaymentListResponse
from app.schemas.error import ErrorResponse
from app.services.transaction_processor import TransactionProcessor
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.user_repository import UserRepository
from datetime import datetime

router = APIRouter()


@router.post(
    "/repayments",
    response_model=RepaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid data"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["repayments"]
)
def create_repayment(
    repayment_data: RepaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Record a new repayment.
    
    Processes and stores a repayment transaction with automatic on-time/late classification.
    
    Args:
        repayment_data: Repayment data (user_id, amount, loan_reference, dates)
        db: Database session (injected)
        
    Returns:
        RepaymentResponse: Created repayment with status and days_overdue
        
    Validates: Requirements 2.1
    """
    try:
        # Verify user exists
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(repayment_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {repayment_data.user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(repayment_data.user_id)}
                }
            )
        
        # Process the repayment
        processor = TransactionProcessor(db)
        repayment = processor.process_repayment(
            user_id=repayment_data.user_id,
            amount=float(repayment_data.amount),
            loan_reference=repayment_data.loan_reference,
            due_date=repayment_data.due_date,
            payment_date=repayment_data.payment_date
        )
        
        return RepaymentResponse(
            repayment_id=repayment.id,
            user_id=repayment.user_id,
            amount=repayment.amount,
            loan_reference=repayment.loan_reference,
            due_date=repayment.due_date,
            payment_date=repayment.payment_date,
            status=repayment.status.value,
            days_overdue=repayment.days_overdue,
            created_at=repayment.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while creating the repayment",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/repayments/{user_id}",
    response_model=RepaymentListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["repayments"]
)
def get_repayment_history(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get repayment history for a user.
    
    Retrieves all repayments for the specified user.
    
    Args:
        user_id: UUID of the user
        db: Database session (injected)
        
    Returns:
        RepaymentListResponse: List of all repayments for the user
        
    Validates: Requirements 2.5
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
        
        # Get repayment history
        repayment_repo = RepaymentRepository(db)
        repayments = repayment_repo.get_by_user(user_id)
        
        repayment_responses = [
            RepaymentResponse(
                repayment_id=r.id,
                user_id=r.user_id,
                amount=r.amount,
                loan_reference=r.loan_reference,
                due_date=r.due_date,
                payment_date=r.payment_date,
                status=r.status.value,
                days_overdue=r.days_overdue,
                created_at=r.created_at
            )
            for r in repayments
        ]
        
        return RepaymentListResponse(repayments=repayment_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving repayment history",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )
