#!/usr/bin/env python3
"""
Create initial system administrator user.
This script should be run after database migration to create the first admin.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, engine
from app.models.system_user import SystemUser, UserRole
from app.services.system_auth_service import SystemAuthService
from app.config import get_settings

def create_initial_admin():
    """Create the initial system administrator."""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin_email = "admin@creditscore.com"
        system_user_repo = SystemUserRepository(db)
        existing_admin = system_user_repo.get_by_email(admin_email)
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists!")
            return
        
        # Create admin user
        auth_service = SystemAuthService(db)
        admin_data = SystemUserRegister(
            fullname="System Administrator",
            email=admin_email,
            password="Admin123",  # Even shorter password
            role=UserRole.ADMIN.value
        )
        
        admin_user = auth_service.register_user(admin_data)
        
        print(f"✅ Created admin user: {admin_user.email}")
        print(f"   ID: {admin_user.id}")
        print(f"   Role: {admin_user.role}")
        print(f"⚠️  Please change the default password!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Import here to avoid circular imports
    from app.repositories.system_user_repository import SystemUserRepository
    from app.schemas.system_user import SystemUserRegister
    
    print("Creating initial system administrator...")
    create_initial_admin()
    print("Done!")
