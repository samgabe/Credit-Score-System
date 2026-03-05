"""
System User model for the Credit Score API.
Handles authentication and authorization for system administrators and operators.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(enum.Enum):
    """Enum for system user roles."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class SystemUser(Base):
    """
    System User model representing administrators and operators who can login to the system.
    
    Attributes:
        id: Unique identifier (UUID)
        email: Email address for login (unique)
        password_hash: Hashed password for authentication
        full_name: User's full name
        role: User role (admin, operator, viewer)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "system_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.OPERATOR.value)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SystemUser(id={self.id}, email={self.email}, role={self.role})>"
    
    def has_permission(self, required_role: str) -> bool:
        """
        Check if user has the required role or higher.
        
        Args:
            required_role: Minimum required role (viewer, operator, admin)
            
        Returns:
            bool: True if user has sufficient permissions
        """
        role_hierarchy = {
            UserRole.VIEWER.value: 1,
            UserRole.OPERATOR.value: 2,
            UserRole.ADMIN.value: 3
        }
        
        user_role_level = role_hierarchy.get(self.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)
        
        return user_role_level >= required_role_level
