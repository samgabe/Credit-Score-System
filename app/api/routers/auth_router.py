"""
Authentication Router for the Credit Score API.
Handles user registration, login, and token management.
"""
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import UserLogin, UserRegister, Token, UserResponse, ChangePassword
from app.schemas.error import ErrorResponse
from app.services.auth_service import AuthService
from app.exceptions import AuthenticationException, ValidationException, DuplicateNationalIDError

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get current authenticated user from token.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
        user = auth_service.user_repo.get_by_id(UUID(user_id))
        if user is None:
            raise credentials_exception
            
        return user
    except Exception:
        raise credentials_exception


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["authentication"]
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with email and password authentication.
    The user will also be created in the main users table.
    
    Args:
        user_data: User registration data (fullname, email, password, national_id, phone_number)
        db: Database session (injected)
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        ValidationException: If validation fails (400)
        DuplicateNationalIDError: If national ID already exists (409)
        
    Validates: Requirements 6.1, 6.2, 6.3 - User creation with authentication
    """
    auth_service = AuthService(db)
    
    try:
        user = auth_service.register_user(user_data)
        
        return {
            "id": str(user.id),
            "fullname": user.fullname,
            "national_id": user.national_id,
            "phone_number": user.phone_number,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateNationalIDError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/auth/login",
    response_model=dict,  # Changed from Token to dict to include user object
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["authentication"]
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT token for authenticated requests.
    
    Args:
        login_data: User login credentials (email, password)
        db: Database session (injected)
        
    Returns:
        Token: JWT access token with user information
        
    Raises:
        AuthenticationException: If credentials are invalid (401)
        
    Validates: Requirement 6.5 - User authentication
    """
    auth_service = AuthService(db)
    
    try:
        response_data = auth_service.login_user(login_data)
        return response_data
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/auth/refresh",
    response_model=Token,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid token"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["authentication"]
)
def refresh_token(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token.
    
    Generates a new token for an authenticated user.
    
    Args:
        current_user: Current authenticated user
        db: Database session (injected)
        
    Returns:
        Token: New JWT access token
        
    Raises:
        HTTPException: If token is invalid (401)
    """
    auth_service = AuthService(db)
    
    # Create new token for the user
    token_data = {
        "user_id": str(current_user.id),
        "email": current_user.email
    }
    
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=timedelta(hours=24)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours in seconds
        "user": {
            "id": str(current_user.id),
            "fullname": current_user.fullname,
            "email": current_user.email,
            "national_id": current_user.national_id,
            "phone_number": current_user.phone_number
        }
    }


@router.get(
    "/auth/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid token"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["authentication"]
)
def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Returns the profile information of the currently authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current user information
        
    Raises:
        HTTPException: If token is invalid (401)
    """
    return UserResponse(
        id=current_user.id,
        fullname=current_user.fullname,
        national_id=current_user.national_id,
        phone_number=current_user.phone_number,
        email=current_user.email,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post(
    "/auth/change-password",
    responses={
        200: {"description": "Password changed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid current password"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["authentication"]
)
def change_password(
    change_password_data: ChangePassword,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    
    Allows authenticated users to change their password by providing the current password
    and a new password.
    
    Args:
        change_password_data: Current and new password data
        current_user: Current authenticated user
        db: Database session (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is invalid (401)
        HTTPException: If new password is too weak (400)
    """
    auth_service = AuthService(db)
    
    try:
        # Verify current password
        if not auth_service.verify_password(change_password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(change_password_data.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long"
            )
        
        # Change password
        auth_service.change_password(current_user.id, change_password_data.new_password)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
