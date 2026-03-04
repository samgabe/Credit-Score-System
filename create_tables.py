"""
Script to create all database tables.
"""
from app.database import Base, engine
from app.models import (
    User, Repayment, MpesaTransaction, 
    Fine, CreditScore, Payment
)

def create_tables():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")
    
    # List created tables
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    create_tables()
