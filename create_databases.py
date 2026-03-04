"""
Database creation script for Credit Score API.
Creates the required PostgreSQL databases if they don't exist.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import get_settings

settings = get_settings()

def parse_database_url(url: str) -> dict:
    """Parse PostgreSQL URL into connection parameters."""
    # Format: postgresql://user:password@host:port/database
    url = url.replace('postgresql://', '')
    auth, location = url.split('@')
    user, password = auth.split(':')
    host_port, database = location.split('/')
    host, port = host_port.split(':')
    
    return {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }

def create_database(db_name: str, conn_params: dict):
    """Create a PostgreSQL database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (postgres database)
        conn = psycopg2.connect(
            user=conn_params['user'],
            password=conn_params['password'],
            host=conn_params['host'],
            port=conn_params['port'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"✓ Database '{db_name}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"✓ Created database '{db_name}'")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database '{db_name}': {e}")
        return False

def main():
    """Create both production and test databases."""
    print("=" * 60)
    print("Credit Score API - Database Setup")
    print("=" * 60)
    
    # Parse database URLs
    prod_params = parse_database_url(settings.database_url)
    test_params = parse_database_url(settings.test_database_url)
    
    print(f"\nConnecting to PostgreSQL at {prod_params['host']}:{prod_params['port']}")
    print(f"User: {prod_params['user']}\n")
    
    # Create databases
    success = []
    success.append(create_database(prod_params['database'], prod_params))
    success.append(create_database(test_params['database'], test_params))
    
    print("\n" + "=" * 60)
    if all(success):
        print("✓ Database setup complete!")
        print("\nDatabases ready:")
        print(f"  - {prod_params['database']} (production)")
        print(f"  - {test_params['database']} (testing)")
    else:
        print("✗ Database setup failed")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Credentials in .env are correct")
        print("  3. User has permission to create databases")

if __name__ == "__main__":
    main()
