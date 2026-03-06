"""
Database connection and session management using SQLAlchemy.
Provides database engine, session factory, and dependency injection for FastAPI.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    echo=False,  # Disable SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI endpoints.
    Provides a database session and ensures proper cleanup.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users/{user_id}")
        def get_user(user_id: UUID, db: Session = Depends(get_db)):
            return db.query(User).filter(User.id == user_id).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    # Import all models to ensure they're registered with Base
    from app.models.user import User
    from app.models.system_user import SystemUser
    from app.models.credit_subject import CreditSubject
    from app.models.credit_score import CreditScore, setup_credit_subject_relationship
    from app.models.repayment import Repayment
    from app.models.mpesa_transaction import MpesaTransaction
    from app.models.payment import Payment
    from app.models.fine import Fine
    from app.models.factor_data import RepaymentData, MpesaData, ConsistencyData, FineData
    
    # Set up relationships that have circular dependencies
    setup_credit_subject_relationship()
    
    Base.metadata.create_all(bind=engine)
