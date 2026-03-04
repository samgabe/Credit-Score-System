"""
Fine Router for the Credit Score API.
Handles fine management endpoints including assessment, payment, and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.fine import FineCreate, FinePayment, FineResponse, FineListResponse
from app.schemas.error import ErrorResponse
from app.services.transaction_processor import TransactionProcessor
from app.repositories.fine_repository import FineRepository
from app.repositories.user_repository import UserRepository
from datetime import datetime

router = APIRouter()


@router.post(
    "/fines",
    response_model=FineResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid data"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["fines"]
)
def create_fine(
    fine_data: FineCreate,
    db: Session = Depends(get_db)
):
    """
    Assess a new fine.
    
    Creates a fine record for a user with status 'unpaid'.
    
    Args:
        fine_data: Fine data (user_id, amount, reason, assessed_date)
        db: Database session (injected)
        
    Returns:
        FineResponse: Created fine with details
        
    Validates: Requirements 5.1
    """
    try:
        # Verify user exists
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(fine_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {fine_data.user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(fine_data.user_id)}
                }
            )
        
        # Process the fine
        processor = TransactionProcessor(db)
        fine = processor.process_fine(
            user_id=fine_data.user_id,
            amount=float(fine_data.amount),
            reason=fine_data.reason,
            assessed_date=fine_data.assessed_date
        )
        
        return FineResponse(
            fine_id=fine.id,
            user_id=fine.user_id,
            amount=fine.amount,
            reason=fine.reason,
            status=fine.status.value,
            assessed_date=fine.assessed_date,
            paid_date=fine.paid_date,
            created_at=fine.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while creating the fine",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.put(
    "/fines/{fine_id}/pay",
    response_model=FineResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Fine not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["fines"]
)
def mark_fine_paid(
    fine_id: UUID,
    payment_data: FinePayment,
    db: Session = Depends(get_db)
):
    """
    Mark a fine as paid.
    
    Updates the fine status to 'paid' and sets the paid_date.
    
    Args:
        fine_id: UUID of the fine to mark as paid
        payment_data: Payment data (payment_date)
        db: Database session (injected)
        
    Returns:
        FineResponse: Updated fine with paid status
        
    Validates: Requirements 5.2
    """
    try:
        # Mark fine as paid
        processor = TransactionProcessor(db)
        fine = processor.mark_fine_paid(
            fine_id=fine_id,
            payment_date=payment_data.payment_date
        )
        
        if not fine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "FINE_NOT_FOUND",
                    "message": f"Fine with ID {fine_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"fine_id": str(fine_id)}
                }
            )
        
        return FineResponse(
            fine_id=fine.id,
            user_id=fine.user_id,
            amount=fine.amount,
            reason=fine.reason,
            status=fine.status.value,
            assessed_date=fine.assessed_date,
            paid_date=fine.paid_date,
            created_at=fine.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while updating the fine",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/fines/{user_id}",
    response_model=FineListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["fines"]
)
def get_user_fines(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all fines for a user.
    
    Retrieves all fines for the specified user with their payment status.
    
    Args:
        user_id: UUID of the user
        db: Database session (injected)
        
    Returns:
        FineListResponse: List of all fines for the user
        
    Validates: Requirements 5.3
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
        
        # Get fine history
        fine_repo = FineRepository(db)
        fines = fine_repo.get_by_user(user_id)
        
        fine_responses = [
            FineResponse(
                fine_id=f.id,
                user_id=f.user_id,
                amount=f.amount,
                reason=f.reason,
                status=f.status.value,
                assessed_date=f.assessed_date,
                paid_date=f.paid_date,
                created_at=f.created_at
            )
            for f in fines
        ]
        
        return FineListResponse(fines=fine_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving fines",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )
