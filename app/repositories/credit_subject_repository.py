"""
Credit Subject Repository for the Credit Score API.
Handles data access operations for CreditSubject entities.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.credit_subject import CreditSubject


class CreditSubjectRepository:
    """
    Repository for CreditSubject entity operations.
    Implements the Repository pattern to abstract database operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the CreditSubjectRepository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        full_name: str,
        national_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> CreditSubject:
        """
        Create a new credit subject.
        
        Args:
            full_name: Subject's full name
            national_id: National identification number
            phone_number: Phone number
            email: Email address
            external_id: External reference ID (from CSV import)
            
        Returns:
            CreditSubject: The created credit subject object
        """
        credit_subject = CreditSubject(
            full_name=full_name,
            national_id=national_id,
            phone_number=phone_number,
            email=email,
            external_id=external_id
        )
        self.db.add(credit_subject)
        self.db.commit()
        self.db.refresh(credit_subject)
        return credit_subject
    
    def get_by_id(self, subject_id: UUID) -> Optional[CreditSubject]:
        """
        Retrieve a credit subject by ID.
        
        Args:
            subject_id: UUID of the credit subject
            
        Returns:
            Optional[CreditSubject]: Credit subject if found, None otherwise
        """
        return self.db.query(CreditSubject).filter(
            CreditSubject.id == subject_id
        ).first()
    
    def get_by_external_id(self, external_id: str) -> Optional[CreditSubject]:
        """
        Retrieve a credit subject by external ID.
        
        Args:
            external_id: External reference ID
            
        Returns:
            Optional[CreditSubject]: Credit subject if found, None otherwise
        """
        return self.db.query(CreditSubject).filter(
            CreditSubject.external_id == external_id
        ).first()
    
    def get_by_national_id(self, national_id: str) -> Optional[CreditSubject]:
        """
        Retrieve a credit subject by national ID.
        
        Args:
            national_id: National identification number
            
        Returns:
            Optional[CreditSubject]: Credit subject if found, None otherwise
        """
        return self.db.query(CreditSubject).filter(
            CreditSubject.national_id == national_id
        ).first()
    
    def search(
        self,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CreditSubject]:
        """
        Search credit subjects by name, email, or phone.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[CreditSubject]: List of matching credit subjects
        """
        db_query = self.db.query(CreditSubject)
        
        if query:
            search_filter = or_(
                CreditSubject.full_name.ilike(f"%{query}%"),
                CreditSubject.email.ilike(f"%{query}%"),
                CreditSubject.phone_number.ilike(f"%{query}%"),
                CreditSubject.national_id.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        return db_query.limit(limit).offset(offset).all()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[CreditSubject]:
        """
        Retrieve all credit subjects with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[CreditSubject]: List of credit subjects
        """
        return self.db.query(CreditSubject).limit(limit).offset(offset).all()
    
    def update(
        self,
        subject_id: UUID,
        full_name: Optional[str] = None,
        national_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Optional[CreditSubject]:
        """
        Update a credit subject's information.
        
        Args:
            subject_id: UUID of the credit subject to update
            full_name: New full name (optional)
            national_id: New national ID (optional)
            phone_number: New phone number (optional)
            email: New email (optional)
            external_id: New external ID (optional)
            
        Returns:
            Optional[CreditSubject]: Updated credit subject if found, None otherwise
        """
        subject = self.get_by_id(subject_id)
        if not subject:
            return None
        
        if full_name is not None:
            subject.full_name = full_name
        if national_id is not None:
            subject.national_id = national_id
        if phone_number is not None:
            subject.phone_number = phone_number
        if email is not None:
            subject.email = email
        if external_id is not None:
            subject.external_id = external_id
        
        self.db.commit()
        self.db.refresh(subject)
        return subject
    
    def delete(self, subject_id: UUID) -> bool:
        """
        Delete a credit subject.
        
        Args:
            subject_id: UUID of the credit subject to delete
            
        Returns:
            bool: True if subject was deleted, False if not found
        """
        subject = self.get_by_id(subject_id)
        if not subject:
            return False
        
        self.db.delete(subject)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """
        Get total count of credit subjects.
        
        Returns:
            int: Total number of credit subjects
        """
        return self.db.query(CreditSubject).count()
