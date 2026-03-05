"""
Credit Subject Router for the Credit Score API.
Handles CRUD operations for credit subjects (people being scored).
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.system_user import SystemUser
from app.repositories.credit_subject_repository import CreditSubjectRepository
from app.schemas.credit_subject import CreditSubjectCreate, CreditSubjectResponse, CreditSubjectUpdate
from app.schemas.error import ErrorResponse
from app.api.routers.system_auth_router import get_current_system_user, require_role

router = APIRouter()


@router.post(
    "/credit-subjects",
    response_model=CreditSubjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-subjects"]
)
def create_credit_subject(
    subject_data: CreditSubjectCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Create a new credit subject.
    
    Creates a new credit subject (person to be scored) in the system.
    Requires operator or admin permissions.
    
    Args:
        subject_data: Credit subject creation data
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        CreditSubjectResponse: Created credit subject information
        
    Raises:
        HTTPException: If validation fails or user lacks permissions
    """
    subject_repo = CreditSubjectRepository(db)
    
    try:
        # Check if subject with same identifiers already exists
        if subject_data.national_id:
            existing = subject_repo.get_by_national_id(subject_data.national_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credit subject with national ID {subject_data.national_id} already exists"
                )
        
        if subject_data.email:
            existing = subject_repo.search(query=subject_data.email, limit=1)
            if existing and existing[0].email == subject_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credit subject with email {subject_data.email} already exists"
                )
        
        # Create subject
        subject = subject_repo.create(
            full_name=subject_data.full_name,
            national_id=subject_data.national_id,
            phone_number=subject_data.phone_number,
            email=subject_data.email,
            external_id=subject_data.external_id
        )
        
        return CreditSubjectResponse(
            id=subject.id,
            full_name=subject.full_name,
            national_id=subject.national_id,
            phone_number=subject.phone_number,
            email=subject.email,
            external_id=subject.external_id,
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create credit subject"
        )


@router.get(
    "/credit-subjects",
    response_model=List[CreditSubjectResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-subjects"]
)
def list_credit_subjects(
    search: Optional[str] = Query(None, description="Search query for name, email, phone, or national ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
):
    """
    List credit subjects with optional search and pagination.
    
    Returns a list of credit subjects in the system.
    Supports search by name, email, phone number, or national ID.
    Requires viewer, operator, or admin permissions.
    
    Args:
        search: Optional search query
        limit: Maximum number of results to return
        offset: Number of results to skip
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        List[CreditSubjectResponse]: List of credit subjects
    """
    subject_repo = CreditSubjectRepository(db)
    
    try:
        if search:
            subjects = subject_repo.search(query=search, limit=limit, offset=offset)
        else:
            subjects = subject_repo.get_all(limit=limit, offset=offset)
        
        return [
            CreditSubjectResponse(
                id=subject.id,
                full_name=subject.full_name,
                national_id=subject.national_id,
                phone_number=subject.phone_number,
                email=subject.email,
                external_id=subject.external_id,
                created_at=subject.created_at,
                updated_at=subject.updated_at
            )
            for subject in subjects
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit subjects"
        )


@router.get(
    "/credit-subjects/{subject_id}",
    response_model=CreditSubjectResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-subjects"]
)
def get_credit_subject(
    subject_id: UUID,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
):
    """
    Get a specific credit subject by ID.
    
    Returns detailed information about a specific credit subject.
    Requires viewer, operator, or admin permissions.
    
    Args:
        subject_id: UUID of the credit subject
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        CreditSubjectResponse: Credit subject information
        
    Raises:
        HTTPException: If subject not found or user lacks permissions
    """
    subject_repo = CreditSubjectRepository(db)
    
    try:
        subject = subject_repo.get_by_id(subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit subject not found"
            )
        
        return CreditSubjectResponse(
            id=subject.id,
            full_name=subject.full_name,
            national_id=subject.national_id,
            phone_number=subject.phone_number,
            email=subject.email,
            external_id=subject.external_id,
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit subject"
        )


@router.put(
    "/credit-subjects/{subject_id}",
    response_model=CreditSubjectResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-subjects"]
)
def update_credit_subject(
    subject_id: UUID,
    subject_data: CreditSubjectUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Update a credit subject.
    
    Updates information for an existing credit subject.
    Requires operator or admin permissions.
    
    Args:
        subject_id: UUID of the credit subject to update
        subject_data: Updated credit subject data
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        CreditSubjectResponse: Updated credit subject information
        
    Raises:
        HTTPException: If subject not found, validation fails, or user lacks permissions
    """
    subject_repo = CreditSubjectRepository(db)
    
    try:
        # Check if subject exists
        existing = subject_repo.get_by_id(subject_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit subject not found"
            )
        
        # Update subject
        updated_subject = subject_repo.update(
            subject_id=subject_id,
            full_name=subject_data.full_name,
            national_id=subject_data.national_id,
            phone_number=subject_data.phone_number,
            email=subject_data.email,
            external_id=subject_data.external_id
        )
        
        return CreditSubjectResponse(
            id=updated_subject.id,
            full_name=updated_subject.full_name,
            national_id=updated_subject.national_id,
            phone_number=updated_subject.phone_number,
            email=updated_subject.email,
            external_id=updated_subject.external_id,
            created_at=updated_subject.created_at,
            updated_at=updated_subject.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credit subject"
        )


@router.delete(
    "/credit-subjects/{subject_id}",
    responses={
        204: {"description": "Credit subject deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Credit subject not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["credit-subjects"]
)
def delete_credit_subject(
    subject_id: UUID,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("admin"))
):
    """
    Delete a credit subject.
    
    Deletes a credit subject from the system.
    Requires admin permissions only.
    
    Args:
        subject_id: UUID of the credit subject to delete
        db: Database session (injected)
        current_user: Current authenticated system user (must be admin)
        
    Returns:
        None: Returns 204 No Content on success
        
    Raises:
        HTTPException: If subject not found or user lacks permissions
    """
    subject_repo = CreditSubjectRepository(db)
    
    try:
        # Check if subject exists
        existing = subject_repo.get_by_id(subject_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit subject not found"
            )
        
        # Delete subject
        success = subject_repo.delete(subject_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete credit subject"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credit subject"
        )
