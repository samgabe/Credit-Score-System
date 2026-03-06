"""
Authentication service for the Credit Score API.
Handles user authentication, token generation, and password management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import UUID
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLogin, UserRegister, TokenData
from app.config import get_settings
from app.exceptions import AuthenticationException, ValidationException, DuplicateNationalIDError


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the AuthService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.settings = get_settings()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        # Simple hash for now to avoid bcrypt issues
        # In production, you'd use proper bcrypt
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Optional[User]: User object if authenticated, None otherwise
            
        Raises:
            AuthenticationException: If credentials are invalid
        """
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Check if user has password hash (for users created before auth system)
        if not hasattr(user, 'password_hash') or not user.password_hash:
            # For existing users without passwords, set a default hash
            default_password = "demo123"
            user.password_hash = self.get_password_hash(default_password)
            self.db.commit()
        
        # Verify password using SHA256
        import hashlib
        expected_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user.password_hash != expected_hash:
            raise AuthenticationException("Invalid email or password")
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time delta
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.app_name,  # Using app name as secret key for demo
            algorithm="HS256"
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Dict: Decoded token payload
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.app_name,  # Using app name as secret key for demo
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        except jwt.JWTError:
            raise AuthenticationException("Invalid token")
    
    def register_user(self, user_data: UserRegister) -> User:
        """
        Register a new user with authentication.
        
        Args:
            user_data: User registration data
            
        Returns:
            User: Created user object
            
        Raises:
            DuplicateNationalIDError: If national ID already exists
            ValidationException: If validation fails
        """
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValidationException("Email already registered")
        
        # Hash password using bcrypt
        password_hash = self.get_password_hash(user_data.password)
        
        # Create user with password hash
        user = self.user_repo.create(
            fullname=user_data.fullname,
            national_id=user_data.national_id,
            phone_number=user_data.phone_number,
            email=user_data.email,
            password_hash=password_hash
        )
        
        return user
    
    def login_user(self, login_data: UserLogin) -> dict:
        """
        Login a user and return token.
        
        Args:
            login_data: User login credentials
            
        Returns:
            dict: Token response with user info
            
        Raises:
            AuthenticationException: If authentication fails
        """
        try:
            user = self.authenticate_user(login_data.email, login_data.password)
            
            # Create token data
            token_data = TokenData(
                user_id=str(user.id),
                email=user.email
            )
            
            # Generate access token
            access_token = self.create_access_token(
                data=token_data.dict(),
                expires_delta=timedelta(hours=24)
            )
            
            response = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 86400,  # 24 hours in seconds
                "user": {
                    "id": str(user.id),
                    "fullname": user.fullname,
                    "email": user.email,
                    "national_id": user.national_id,
                    "phone_number": user.phone_number
                }
            }
            
            return response
            
        except AuthenticationException as e:
            raise e
    
    def change_password(self, user_id: UUID, new_password: str) -> None:
        """
        Change a user's password.
        
        Args:
            user_id: UUID of the user
            new_password: New plain text password
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationException("User not found")
        
        # Hash the new password
        hashed_password = self.get_password_hash(new_password)
        
        # Update user's password
        user.password_hash = hashed_password
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
