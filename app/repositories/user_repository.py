"""
User Repository for the Credit Score API.
Handles data access operations for User entities.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.exceptions import ValidationException, DuplicateNationalIDError


class UserRepository:
    """
    Repository for User entity CRUD operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the UserRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, fullname: str, national_id: int, phone_number: str, email: Optional[str] = None, password_hash: Optional[str] = None) -> User:
        """
        Create a new user in the database.
        
        Args:
            fullname: User's full name
            national_id: User's unique national identification number
            phone_number: User's phone number
            email: User's email address (optional)
            password_hash: User's password hash (optional)
            
        Returns:
            User: Created user object
            
        Raises:
            IntegrityError: If national_id already exists
            
        Validates: Requirements 6.1, 6.2, 6.3 - User creation
        """
        user = User(
            fullname=fullname,
            national_id=national_id,
            phone_number=phone_number,
            email=email,
            password_hash=password_hash
        )
        
        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            # Handle race condition where duplicate was inserted between check and insert
            if "national_id" in str(e.orig):
                raise DuplicateNationalIDError(national_id)
            raise
    
    def update(self, user_id: UUID, fullname: Optional[str] = None, phone_number: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        """
        Update a user's profile information.
        Note: national_id cannot be changed as per requirements.
        
        Args:
            user_id: UUID of the user to update
            fullname: New full name (optional)
            phone_number: New phone number (optional)
            
        Returns:
            Optional[User]: Updated user object if found, None otherwise
            
        Validates: Requirements 6.4, 6.5
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        if fullname is not None:
            user.fullname = fullname
        if phone_number is not None:
            user.phone_number = phone_number
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_all(self) -> list[User]:
        """
        Retrieve all users from the database.
        
        Returns:
            list[User]: List of all users in the database
            
        Validates: Requirement 6.4 - User listing functionality
        """
        return self.db.query(User).all()
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Retrieve a user by their unique identifier.
        
        Args:
            user_id: UUID of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
            
        Validates: Requirements 1.2, 1.4
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: Email address of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
            
        Validates: Requirements 1.2, 1.4
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_national_id(self, national_id: int) -> Optional[User]:
        """
        Retrieve a user by their national identification number.
        
        Args:
            national_id: National ID of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
            
        Validates: Requirements 6.1, 6.2
        """
        return self.db.query(User).filter(User.national_id == national_id).first()
