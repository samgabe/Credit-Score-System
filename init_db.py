"""
Database initialization script using Alembic migrations.
This script initializes the database by running all pending migrations.
"""
import sys
from alembic.config import Config
from alembic import command
from app.config import get_settings


def init_database():
    """
    Initialize the database by running Alembic migrations.
    This will create all tables and indexes defined in the migration files.
    """
    print("Initializing database with Alembic migrations...")
    
    # Get database URL from settings
    settings = get_settings()
    print(f"Database URL: {settings.database_url.split('@')[1]}")  # Hide credentials
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    try:
        # Run migrations to latest version
        print("\nRunning migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database initialized successfully")
        print("\nAll tables and indexes have been created.")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)


def reset_database():
    """
    Reset the database by downgrading all migrations and then upgrading again.
    WARNING: This will delete all data in the database!
    """
    print("WARNING: This will delete all data in the database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != "yes":
        print("Database reset cancelled.")
        return
    
    print("\nResetting database...")
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    try:
        # Downgrade to base (remove all tables)
        print("Removing all tables...")
        command.downgrade(alembic_cfg, "base")
        print("✓ All tables removed")
        
        # Upgrade to head (recreate all tables)
        print("\nRecreating all tables...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database reset successfully")
        
    except Exception as e:
        print(f"✗ Error resetting database: {e}", file=sys.stderr)
        sys.exit(1)


def show_current_revision():
    """Show the current database revision."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        command.current(alembic_cfg)
    except Exception as e:
        print(f"✗ Error getting current revision: {e}", file=sys.stderr)
        sys.exit(1)


def show_migration_history():
    """Show the migration history."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        command.history(alembic_cfg)
    except Exception as e:
        print(f"✗ Error getting migration history: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization and management")
    parser.add_argument(
        "action",
        choices=["init", "reset", "current", "history"],
        help="Action to perform: init (initialize), reset (drop and recreate), current (show current revision), history (show migration history)"
    )
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_database()
    elif args.action == "reset":
        reset_database()
    elif args.action == "current":
        show_current_revision()
    elif args.action == "history":
        show_migration_history()
