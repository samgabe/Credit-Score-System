"""
System User Repository for the Credit Score API.
Handles data access operations for SystemUser entities.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.system_user import SystemUser, UserRole


class SystemUserRepository:
    """
    Repository for SystemUser entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the SystemUserRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = UserRole.OPERATOR.value
    ) -> SystemUser:
        """
        Create a new system user.
        
        Args:
            email: User's email address
            password_hash: Hashed password
            full_name: User's full name
            role: User role (admin, operator, viewer)
            
        Returns:
            SystemUser: The created system user object
        """
        system_user = SystemUser(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )
        self.db.add(system_user)
        self.db.commit()
        self.db.refresh(system_user)
        return system_user
    
    def get_by_email(self, email: str) -> Optional[SystemUser]:
        """
        Retrieve a system user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[SystemUser]: System user if found, None otherwise
        """
        return self.db.query(SystemUser).filter(
            and_(SystemUser.email == email, SystemUser.is_active == True)
        ).first()
    
    def get_by_id(self, user_id: UUID) -> Optional[SystemUser]:
        """
        Retrieve a system user by ID.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Optional[SystemUser]: System user if found, None otherwise
        """
        return self.db.query(SystemUser).filter(
            and_(SystemUser.id == user_id, SystemUser.is_active == True)
        ).first()
    
    def get_all(self) -> List[SystemUser]:
        """
        Retrieve all active system users.
        
        Returns:
            List[SystemUser]: List of all active system users
        """
        return self.db.query(SystemUser).filter(
            SystemUser.is_active == True
        ).all()
    
    def update(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[SystemUser]:
        """
        Update a system user's information.
        
        Args:
            user_id: UUID of the user to update
            email: New email address (optional)
            full_name: New full name (optional)
            role: New role (optional)
            is_active: New active status (optional)
            
        Returns:
            Optional[SystemUser]: Updated system user if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Soft delete a system user by setting is_active to False.
        
        Args:
            user_id: UUID of the user to delete
            
        Returns:
            bool: True if user was deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
