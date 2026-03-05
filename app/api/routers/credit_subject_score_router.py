"""
Credit Score Router for Credit Subjects.
Handles credit score calculation and retrieval for credit subjects.
"""
from datetime import date, datetime
from typing import List, Optional, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.credit_score import CreditScoreResponse, CreditScoreHistoryResponse, CreditScoreHistoryItem
from app.schemas.error import ErrorResponse
from app.services.credit_score_service import CreditScoreService
from app.services.score_calculator import CreditScoreCalculator
from app.services.data_source_factory import DataSourceFactory
from app.repositories.credit_score_repository import CreditScoreRepository
from app.repositories.credit_subject_repository import CreditSubjectRepository
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.fine_repository import FineRepository
from app.api.routers.system_auth_router import get_current_system_user, require_role
from app.models.system_user import SystemUser

router = APIRouter()


def get_credit_score_service(db: Session = Depends(get_db)) -> CreditScoreService:
    """
    Dependency injection for CreditScoreService.
    
    Creates and wires all dependencies needed for credit score operations:
    - Factor Data Aggregator (or CSV loader based on configuration)
    - Credit Score Calculator
    - Credit Score Repository
    
    Args:
        db: Database session (injected)
        
    Returns:
        CreditScoreService: Fully configured credit score service
    """
    # Initialize data source factory
    factory = DataSourceFactory()
    
    # Initialize repositories for database mode
    repayment_repo = RepaymentRepository(db)
    mpesa_repo = MpesaTransactionRepository(db)
    payment_repo = PaymentRepository(db)
    fine_repo = FineRepository(db)
    credit_score_repo = CreditScoreRepository(db)
    
    # Initialize factor data aggregator using factory
    factor_aggregator = factory.create_factor_data_aggregator(
        repayment_repository=repayment_repo,
        mpesa_transaction_repository=mpesa_repo,
        payment_repository=payment_repo,
        fine_repository=fine_repo
    )
    
    # Initialize calculator
    calculator = CreditScoreCalculator()
    
    # Initialize credit score service
    return CreditScoreService(
        factor_aggregator=factor_aggregator,
        calculator=calculator,
        credit_score_repository=credit_score_repo,
        credit_subject_repository=CreditSubjectRepository(db)
    )


@router.get(
    "/credit-subjects/{subject_id}/scores",
    response_model=List[CreditScoreResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def get_credit_scores_for_subject(
    subject_id: UUID,
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service),
    current_user: SystemUser = Depends(require_role("viewer"))
):
    """
    Get credit scores for a specific credit subject.
    
    Retrieves all credit scores for the specified credit subject.
    Requires viewer role or higher.
    
    Args:
        subject_id: UUID of credit subject
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        current_user: Current authenticated system user
        
    Returns:
        List[CreditScoreResponse]: List of credit scores for the subject
    """
    try:
        # Get credit scores for the specific subject
        credit_scores = credit_score_service.get_credit_scores_for_subject(subject_id)
        
        # Get subject information
        credit_subject_repo = CreditSubjectRepository(db)
        subject = credit_subject_repo.get_by_id(subject_id)
        
        return [
            CreditScoreResponse(
                id=str(score.id),
                user_id=str(score.credit_subject_id) if score.credit_subject_id else None,
                score=score.score,
                category=score.category,
                repayment_factor=score.repayment_factor,
                mpesa_factor=score.mpesa_factor,
                consistency_factor=score.consistency_factor,
                fine_factor=score.fine_factor,
                calculated_at=score.calculated_at.isoformat(),
                factors={
                    "repayment_factor": score.repayment_factor,
                    "mpesa_factor": score.mpesa_factor,
                    "consistency_factor": score.consistency_factor,
                    "fine_factor": score.fine_factor
                },
                credit_subject={
                    "id": str(subject.id) if subject else None,
                    "full_name": subject.full_name if subject else "Unknown",
                    "email": subject.email if subject else ""
                }
            )
            for score in credit_scores
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve credit scores for subject {subject_id}: {str(e)}"
        )


@router.post(
    "/credit-subjects/{subject_id}/credit-score",
    response_model=CreditScoreResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def calculate_credit_score_for_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Calculate credit score for a credit subject.
    
    Calculates a new credit score based on all financial factors and stores it.
    
    Args:
        subject_id: UUID string of the credit subject
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        current_user: Current authenticated system user
        
    Returns:
        CreditScoreResponse: Calculated score with factors and category
        
    Raises:
        HTTPException: If subject not found, validation fails, or user lacks permissions
    """
    try:
        # Parse and validate UUID
        if not subject_id:
            raise ValueError("Subject ID is empty")
        
        # Remove any potential whitespace or special characters
        clean_subject_id = str(subject_id).strip()
        
        try:
            subject_uuid = UUID(clean_subject_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid subject ID format",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": str(e)
                }
            )
        
        # Check if credit subject exists
        subject_repo = CreditSubjectRepository(db)
        subject = subject_repo.get_by_id(subject_uuid)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "SUBJECT_NOT_FOUND",
                    "message": f"Credit subject with ID {subject_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Calculate credit score
        credit_score = credit_score_service.calculate_credit_score_for_subject(subject_uuid)
        
        return CreditScoreResponse(
            id=credit_score.id,
            user_id=str(credit_score.credit_subject_id),  # Map to user_id for compatibility
            score=credit_score.score,
            category=credit_score.category,
            calculated_at=credit_score.calculated_at,
            factors={
                "repayment_factor": credit_score.repayment_factor,
                "mpesa_factor": credit_score.mpesa_factor,
                "consistency_factor": credit_score.consistency_factor,
                "fine_factor": credit_score.fine_factor
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "timestamp": datetime.utcnow().isoformat(),
                "details": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CALCULATION_ERROR",
                "message": "Failed to calculate credit score",
                "timestamp": datetime.utcnow().isoformat(),
                "details": str(e)
            }
        )


@router.get(
    "/credit-subjects/{subject_id}/credit-score",
    response_model=CreditScoreResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def get_credit_score_for_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
):
    """
    Get the latest credit score for a credit subject.
    
    Args:
        subject_id: UUID string of the credit subject
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        CreditScoreResponse: Latest credit score with factors and category
        
    Raises:
        HTTPException: If subject not found or user lacks permissions
    """
    try:
        # Parse and validate UUID
        if not subject_id:
            raise ValueError("Subject ID is empty")
        
        clean_subject_id = str(subject_id).strip()
        
        try:
            subject_uuid = UUID(clean_subject_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid subject ID format",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": str(e)
                }
            )
        
        # Check if credit subject exists
        subject_repo = CreditSubjectRepository(db)
        subject = subject_repo.get_by_id(subject_uuid)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "SUBJECT_NOT_FOUND",
                    "message": f"Credit subject with ID {subject_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Get latest credit score
        credit_score_repo = CreditScoreRepository(db)
        credit_score = credit_score_repo.get_latest_by_credit_subject_id(subject_uuid)
        
        if not credit_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "NO_SCORE_AVAILABLE",
                    "message": f"No credit score found for subject {subject_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return CreditScoreResponse(
            id=credit_score.id,
            user_id=str(credit_score.credit_subject_id),  # Map to user_id for compatibility
            score=credit_score.score,
            category=credit_score.category,
            calculated_at=credit_score.calculated_at,
            factors={
                "repayment_factor": credit_score.repayment_factor,
                "mpesa_factor": credit_score.mpesa_factor,
                "consistency_factor": credit_score.consistency_factor,
                "fine_factor": credit_score.fine_factor
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "timestamp": datetime.utcnow().isoformat(),
                "details": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "RETRIEVAL_ERROR",
                "message": "Failed to retrieve credit score",
                "timestamp": datetime.utcnow().isoformat(),
                "details": str(e)
            }
        )
