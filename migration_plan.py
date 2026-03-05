#!/usr/bin/env python3
"""
Quick migration script to separate system users from credit subjects.
This creates the initial system user and migrates existing users appropriately.
"""

import uuid
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from app.database import get_db_url
from app.models.user import User
from app.models.credit_score import CreditScore

def create_system_user_table():
    """Create system_users table."""
    sql = """
    CREATE TABLE IF NOT EXISTS system_users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'operator',
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    # Execute this in your migration

def create_credit_subjects_table():
    """Create credit_subjects table."""
    sql = """
    CREATE TABLE IF NOT EXISTS credit_subjects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        external_id VARCHAR(255),
        full_name VARCHAR(255) NOT NULL,
        national_id VARCHAR(50),
        phone_number VARCHAR(20),
        email VARCHAR(255),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    # Execute this in your migration

def create_initial_admin():
    """Create the initial system administrator."""
    # This would be done via your user creation API
    admin_data = {
        "email": "admin@creditscore.com",
        "password": "SecureAdmin123!",  # Change this!
        "full_name": "System Administrator", 
        "role": "admin"
    }
    return admin_data

def migrate_existing_users():
    """Migrate existing users to credit_subjects."""
    # Logic to move users with credit scores to credit_subjects table
    # Keep only actual system users in system_users table
    pass

if __name__ == "__main__":
    print("This script outlines the migration approach.")
    print("Run the actual migrations using Alembic.")
