"""
System Authentication Service for the Credit Score API.
Handles authentication and authorization for system users.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.system_user import SystemUser, UserRole
from app.repositories.system_user_repository import SystemUserRepository
from app.schemas.system_user import SystemUserLogin, SystemUserRegister
from app.config import get_settings
from app.exceptions import AuthenticationException, ValidationException, DuplicateEmailError

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SystemAuthService:
    """
    Service for system user authentication and authorization operations.
    
    Handles login, registration, token management, and password operations
    for system administrators and operators.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the SystemAuthService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.system_user_repo = SystemUserRepository(db)
    
    def register_user(self, user_data: SystemUserRegister) -> SystemUser:
        """
        Register a new system user.
        
        Args:
            user_data: User registration data
            
        Returns:
            SystemUser: Created system user
            
        Raises:
            ValidationException: If validation fails
            DuplicateEmailError: If email already exists
        """
        # Validate input
        if not user_data.email or not user_data.password:
            raise ValidationException("Email and password are required")
        
        if len(user_data.password) < 6:
            raise ValidationException("Password must be at least 6 characters long")
        
        # Check if email already exists
        existing_user = self.system_user_repo.get_by_email(user_data.email)
        if existing_user:
            raise DuplicateEmailError(f"Email {user_data.email} already exists")
        
        # Hash password
        password_hash = self.hash_password(user_data.password)
        
        # Create system user
        system_user = self.system_user_repo.create(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.fullname,
            role=user_data.role or UserRole.OPERATOR.value
        )
        
        return system_user
    
    def login_user(self, login_data: SystemUserLogin) -> Dict[str, Any]:
        """
        Authenticate a system user and return token with user info.
        
        Args:
            login_data: User login credentials
            
        Returns:
            Dict: Access token and user information
            
        Raises:
            AuthenticationException: If credentials are invalid
        """
        # Find user by email
        user = self.system_user_repo.get_by_email(login_data.email)
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Verify password
        if not self.verify_password(login_data.password, user.password_hash):
            raise AuthenticationException("Invalid email or password")
        
        # Create access token
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
        
        access_token = self.create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 hours in seconds
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        }
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            str: JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Dict: Decoded token data
            
        Raises:
            AuthenticationException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            raise AuthenticationException("Invalid token")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain password.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        # Truncate password to bcrypt's 72-byte limit if needed
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        return pwd_context.hash(password)
    
    def change_password(self, user_id: UUID, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: UUID of the user
            new_password: New plain text password
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            ValidationException: If new password is too weak
        """
        if len(new_password) < 6:
            raise ValidationException("Password must be at least 6 characters long")
        
        # Hash new password
        password_hash = self.hash_password(new_password)
        
        # Update user
        updated_user = self.system_user_repo.update(
            user_id=user_id,
            password_hash=password_hash
        )
        
        return updated_user is not None
    
    def get_user_by_token(self, token: str) -> Optional[SystemUser]:
        """
        Get a system user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            Optional[SystemUser]: System user if token is valid, None otherwise
        """
        try:
            payload = self.decode_token(token)
            user_id = payload.get("user_id")
            
            if user_id is None:
                return None
            
            return self.system_user_repo.get_by_id(UUID(user_id))
        except Exception:
            return None
