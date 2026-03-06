"""
Credit Score Router for the Credit Score API.
Handles credit score calculation, retrieval, and history endpoints.
"""
from datetime import date, datetime
from typing import Optional, List
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
from app.repositories.user_repository import UserRepository
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
    credit_subject_repo = CreditSubjectRepository(db)
    
    # Initialize factor data aggregator using factory
    factor_aggregator = factory.create_factor_data_aggregator(
        repayment_repository=repayment_repo,
        mpesa_transaction_repository=mpesa_repo,
        payment_repository=payment_repo,
        fine_repository=fine_repo
    )
    
    # Initialize calculator
    calculator = CreditScoreCalculator()
    
    # Initialize and return service with all dependencies
    return CreditScoreService(
        factor_aggregator=factor_aggregator,
        calculator=calculator,
        credit_score_repository=credit_score_repo,
        credit_subject_repository=credit_subject_repo
    )


@router.post(
    "/users/{user_id}/credit-score",
    response_model=CreditScoreResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def calculate_credit_score(
    user_id: str,
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Calculate credit score for a user.
    
    Calculates a new credit score based on all financial factors and stores it.
    
    Args:
        user_id: UUID string of the user
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        
    Returns:
        CreditScoreResponse: Calculated score with factors and category
        
    Validates: Requirements 7.1
    """
    try:
        # Parse and validate UUID
        user_id = str(user_id).strip()
        
        try:
            user_uuid = UUID(user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "user_id": f"Invalid UUID format received: '{user_id}'. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "received": user_id,
                        "error": str(e)
                    }
                }
            )
        
        # Verify user exists using factory
        factory = DataSourceFactory()
        user_data_source = factory.create_user_repository(db)
        
        if factory.is_csv_mode():
            user_data = user_data_source.get_user_by_id(user_uuid)
            user_exists = user_data is not None
        else:
            user = user_data_source.get_by_id(user_uuid)
            user_exists = user is not None
        
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {user_uuid} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(user_uuid)}
                }
            )
        
        # Calculate and store the credit score using the service
        credit_score = credit_score_service.calculate_and_store_score(user_uuid)
        
        # Build factors dictionary
        factors = {
            "repayment_factor": credit_score.repayment_factor,
            "mpesa_factor": credit_score.mpesa_factor,
            "consistency_factor": credit_score.consistency_factor,
            "fine_factor": credit_score.fine_factor
        }
        
        # Determine score category
        if credit_score.score >= 750:
            category = "Excellent"
        elif credit_score.score >= 700:
            category = "Good"
        elif credit_score.score >= 650:
            category = "Fair"
        elif credit_score.score >= 600:
            category = "Poor"
        else:
            category = "Very Poor"
        
        return CreditScoreResponse(
            id=credit_score.id,
            user_id=credit_score.user_id,
            score=credit_score.score,
            category=category,
            calculated_at=credit_score.calculated_at,
            factors=factors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CALCULATION_ERROR",
                "message": "Failed to calculate credit score",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/users/{user_id}/credit-score",
    response_model=CreditScoreResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User or score not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def get_current_credit_score(
    user_id: UUID,
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service)
):
    """
    Get current credit score for a user.
    
    Retrieves the most recent credit score for the specified user.
    
    Args:
        user_id: UUID of the user
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        
    Returns:
        CreditScoreResponse: Current score with factors and category
        
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    try:
        # Verify user exists using factory
        factory = DataSourceFactory()
        user_data_source = factory.create_user_repository(db)
        
        if factory.is_csv_mode():
            user_data = user_data_source.get_user_by_id(user_id)
            user_exists = user_data is not None
        else:
            user = user_data_source.get_by_id(user_id)
            user_exists = user is not None
        
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(user_id)}
                }
            )
        
        # Get latest credit score using the service
        credit_score = credit_score_service.get_latest_score(user_id)
        
        if not credit_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "SCORE_NOT_FOUND",
                    "message": f"No credit score found for user {user_id}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(user_id)}
                }
            )
        
        # Build factors dictionary
        factors = {
            "repayment_factor": credit_score.repayment_factor,
            "mpesa_factor": credit_score.mpesa_factor,
            "consistency_factor": credit_score.consistency_factor,
            "fine_factor": credit_score.fine_factor
        }
        
        return CreditScoreResponse(
            user_id=credit_score.user_id,
            score=credit_score.score,
            category=credit_score.category,
            calculated_at=credit_score.calculated_at,
            factors=factors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving the credit score",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/users/{user_id}/credit-score/history",
    response_model=CreditScoreHistoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def get_credit_score_history(
    user_id: UUID,
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service)
):
    """
    Get credit score history for a user.
    
    Retrieves all historical credit scores for the specified user,
    optionally filtered by date range. Includes score deltas between consecutive calculations.
    
    Args:
        user_id: UUID of the user
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        
    Returns:
        CreditScoreHistoryResponse: List of historical scores with deltas
        
    Validates: Requirements 7.5
    """
    try:
        # Verify user exists using factory
        factory = DataSourceFactory()
        user_data_source = factory.create_user_repository(db)
        
        if factory.is_csv_mode():
            user_data = user_data_source.get_user_by_id(user_id)
            user_exists = user_data is not None
        else:
            user = user_data_source.get_by_id(user_id)
            user_exists = user is not None
        
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with ID {user_id} does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"user_id": str(user_id)}
                }
            )
        
        # Get credit score history using the service
        scores = credit_score_service.get_score_history(user_id, start_date, end_date)
        
        # Build history items with delta calculation
        history_items = []
        for i, score in enumerate(scores):
            # Calculate delta (difference from previous score)
            delta = None
            if i < len(scores) - 1:  # Not the oldest score
                previous_score = scores[i + 1]
                delta = score.score - previous_score.score
            
            history_items.append(
                CreditScoreHistoryItem(
                    score=score.score,
                    category=score.category,
                    calculated_at=score.calculated_at,
                    delta=delta
                )
            )
        
        return CreditScoreHistoryResponse(
            user_id=user_id,
            scores=history_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving credit score history",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/credit-scores",
    response_model=List[CreditScoreResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-scores"]
)
def get_all_credit_scores(
    current_user: SystemUser = Depends(require_role("viewer")),
    db: Session = Depends(get_db),
    credit_score_service: CreditScoreService = Depends(get_credit_score_service)
):
    """
    Get all credit scores for all subjects.
    
    Retrieves all credit scores in the system with subject information.
    Requires viewer role or higher.
    
    Args:
        current_user: Current authenticated system user
        db: Database session (injected)
        credit_score_service: Credit score service (injected)
        
    Returns:
        List[CreditScoreResponse]: List of all credit scores with subject info
    """
    try:
        # Get all credit scores with their subject information
        credit_scores = credit_score_service.get_all_credit_scores_with_subjects()
        
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
            for score, subject in credit_scores
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve credit scores: {str(e)}"
        )
