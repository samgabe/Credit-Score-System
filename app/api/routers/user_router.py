"""
User Router for the Credit Score API.
Handles user management endpoints including creation, retrieval, and updates.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.error import ErrorResponse
from app.repositories.user_repository import UserRepository
from app.services.data_source_factory import DataSourceFactory
from app.exceptions import UserNotFoundError, DuplicateNationalIDError, ValidationException

router = APIRouter()


@router.get(
    "/users",
    response_model=list[UserResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["users"]
)
def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users.
    
    Retrieves a list of all users in the system with their basic information.
    
    Args:
        db: Database session (injected)
        
    Returns:
        list[UserResponse]: List of all users
        
    Raises:
        DatabaseError: If database operation fails (500)
        
    Validates: Requirement 6.4 - User listing functionality
    """
    user_repo = UserRepository(db)
    users = user_repo.get_all()
    
    return [
        UserResponse(
            id=user.id,
            fullname=user.fullname,
            national_id=user.national_id,
            phone_number=user.phone_number,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Duplicate national ID"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["users"]
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    Creates a new user record with full name, national ID, phone number, and optional email.
    National ID must be unique across all users.
    
    Args:
        user_data: User creation data (fullname, national_id, phone_number, email)
        db: Database session (injected)
        
    Returns:
        UserResponse: Created user with user_id and timestamps
        
    Raises:
        ValidationException: If validation fails (400)
        DuplicateNationalIDError: If national ID already exists (409)
        
    Validates: Requirements 6.1, 6.2, 6.3, 6.6
    """
    user_repo = UserRepository(db)
    
    # Create the user - repository will handle duplicate check
    user = user_repo.create(
        fullname=user_data.fullname,
        national_id=user_data.national_id,
        phone_number=user_data.phone_number,
        email=user_data.email
    )
    
    # Return user response
    return UserResponse(
        id=user.id,
        fullname=user.fullname,
        national_id=user.national_id,
        phone_number=user.phone_number,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["users"]
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID.
    
    Retrieves user information including full name, national ID, phone number, and email.
    
    Args:
        user_id: UUID of the user to retrieve
        db: Database session (injected)
        
    Returns:
        UserResponse: User profile with all fields
        
    Raises:
        UserNotFoundError: If user not found (404)
        
    Validates: Requirements 6.3
    """
    # Use factory to get user data source
    factory = DataSourceFactory()
    user_data_source = factory.create_user_repository(db)
    
    if factory.is_csv_mode():
        # Get user from CSV
        user_data = user_data_source.get_user_by_id(user_id)
        
        if not user_data:
            raise UserNotFoundError(str(user_id))
        
        # Convert CSV data to UserResponse format
        return UserResponse(
            id=UUID(user_data['id']),
            fullname=user_data['fullname'],
            national_id=int(user_data['national_id']),
            phone_number=user_data['phone_number'],
            email=user_data.get('email'),
            created_at=datetime.fromisoformat(user_data['created_at']),
            updated_at=datetime.fromisoformat(user_data['updated_at'])
        )
    else:
        # Get user from database
        user = user_data_source.get_by_id(user_id)
        
        if not user:
            raise UserNotFoundError(str(user_id))
        
        return UserResponse(
            id=user.id,
            fullname=user.fullname,
            national_id=user.national_id,
            phone_number=user.phone_number,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["users"]
)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    
    Updates user's full name and/or phone number. National ID cannot be changed.
    At least one field must be provided for update.
    
    Args:
        user_id: UUID of the user to update
        user_data: User update data (fullname, phone_number)
        db: Database session (injected)
        
    Returns:
        UserResponse: Updated user profile
        
    Raises:
        UserNotFoundError: If user not found (404)
        ValidationException: If validation fails (400)
        
    Validates: Requirements 6.4, 6.5
    """
    user_repo = UserRepository(db)
    
    # Check if at least one field is provided
    if user_data.fullname is None and user_data.phone_number is None:
        raise ValidationException(
            "At least one field must be provided for update",
            {"fields": ["fullname", "phone_number"]}
        )
    
    # Update the user - repository will handle not found
    user = user_repo.update(
        user_id=user_id,
        fullname=user_data.fullname,
        phone_number=user_data.phone_number
    )
    
    if not user:
        raise UserNotFoundError(str(user_id))
    
    return UserResponse(
        id=user.id,
        fullname=user.fullname,
        national_id=user.national_id,
        phone_number=user.phone_number,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
