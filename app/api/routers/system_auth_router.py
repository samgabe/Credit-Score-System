"""
System Authentication Router for the Credit Score API.
Handles system user registration, login, and token management.
"""
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.system_user import SystemUserLogin, SystemUserRegister, SystemPasswordChange
from app.schemas.error import ErrorResponse
from app.services.system_auth_service import SystemAuthService
from app.exceptions import AuthenticationException, ValidationException, DuplicateEmailError
from app.models.system_user import SystemUser

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="system-auth/token")


def get_current_system_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get current authenticated system user from token.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        SystemUser: Current authenticated system user
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = SystemAuthService(db)
        payload = auth_service.decode_token(token)
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
        user = auth_service.system_user_repo.get_by_id(UUID(user_id))
        if user is None:
            raise credentials_exception
            
        return user
    except Exception:
        raise credentials_exception


def require_role(required_role: str):
    """
    Dependency factory to require specific user role.
    
    Args:
        required_role: Minimum required role (viewer, operator, admin)
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: SystemUser = Depends(get_current_system_user)):
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker


@router.post(
    "/system-auth/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["system-authentication"]
)
def register_system_user(
    user_data: SystemUserRegister,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("admin"))
):
    """
    Register a new system user (admin only).
    
    Creates a new system user account with email and password authentication.
    Only administrators can create new system users.
    
    Args:
        user_data: User registration data (fullname, email, password)
        db: Database session (injected)
        current_user: Current authenticated system user (must be admin)
        
    Returns:
        dict: Created system user information
        
    Raises:
        HTTPException: If validation fails or email already exists
    """
    auth_service = SystemAuthService(db)
    
    try:
        user = auth_service.register_user(user_data)
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/system-auth/login",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["system-authentication"]
)
def login_system_user(
    login_data: SystemUserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate system user and return access token.
    
    Validates system user credentials and returns a JWT token for authenticated requests.
    
    Args:
        login_data: User login credentials (email, password)
        db: Database session (injected)
        
    Returns:
        dict: JWT access token with user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = SystemAuthService(db)
    
    try:
        response_data = auth_service.login_user(login_data)
        return response_data
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get(
    "/system-auth/me",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid token"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["system-authentication"]
)
def get_current_system_user_info(
    current_user: SystemUser = Depends(get_current_system_user)
):
    """
    Get current authenticated system user information.
    
    Returns the profile information of the currently authenticated system user.
    
    Args:
        current_user: Current authenticated system user
        
    Returns:
        dict: Current system user information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat()
    }


@router.post(
    "/system-auth/change-password",
    responses={
        200: {"description": "Password changed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid current password"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["system-authentication"]
)
def change_system_user_password(
    change_password_data: SystemPasswordChange,
    current_user: SystemUser = Depends(get_current_system_user),
    db: Session = Depends(get_db)
):
    """
    Change the current system user's password.
    
    Allows authenticated system users to change their password.
    
    Args:
        change_password_data: Current and new password data
        current_user: Current authenticated system user
        db: Database session (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is invalid or new password is too weak
    """
    auth_service = SystemAuthService(db)
    
    try:
        # Verify current password
        if not auth_service.verify_password(change_password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Change password
        auth_service.change_password(current_user.id, change_password_data.new_password)
        
        return {"message": "Password changed successfully"}
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get(
    "/system-auth/users",
    response_model=list,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["system-authentication"]
)
def list_system_users(
    current_user: SystemUser = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all system users (admin only).
    
    Returns a list of all system users in the system.
    Only administrators can access this endpoint.
    
    Args:
        current_user: Current authenticated system user (must be admin)
        db: Database session (injected)
        
    Returns:
        list: List of system users
    """
    from app.repositories.system_user_repository import SystemUserRepository
    system_user_repo = SystemUserRepository(db)
    users = system_user_repo.get_all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
        for user in users
    ]
