"""
Quick migration utility script.
Provides shortcuts for common Alembic operations.
"""
import sys
import subprocess


def run_command(cmd):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def create_migration(message):
    """Create a new migration with autogenerate."""
    print(f"Creating migration: {message}")
    return run_command(f'alembic revision --autogenerate -m "{message}"')


def apply_migrations():
    """Apply all pending migrations."""
    print("Applying migrations...")
    return run_command("alembic upgrade head")


def rollback_migration():
    """Rollback the last migration."""
    print("Rolling back last migration...")
    return run_command("alembic downgrade -1")


def show_current():
    """Show current database revision."""
    print("Current database revision:")
    return run_command("alembic current")


def show_history():
    """Show migration history."""
    print("Migration history:")
    return run_command("alembic history")


def check_status():
    """Check if database is up to date."""
    print("Checking database status...")
    return run_command("alembic check")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [args]")
        print("\nCommands:")
        print("  create <message>  - Create a new migration")
        print("  apply             - Apply all pending migrations")
        print("  rollback          - Rollback the last migration")
        print("  current           - Show current database revision")
        print("  history           - Show migration history")
        print("  check             - Check if database is up to date")
        print("\nExamples:")
        print('  python migrate.py create "Add user preferences table"')
        print("  python migrate.py apply")
        print("  python migrate.py rollback")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            print('Usage: python migrate.py create "Description of changes"')
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        success = create_migration(message)
    elif command == "apply":
        success = apply_migrations()
    elif command == "rollback":
        success = rollback_migration()
    elif command == "current":
        success = show_current()
    elif command == "history":
        success = show_history()
    elif command == "check":
        success = check_status()
    else:
        print(f"Error: Unknown command '{command}'")
        print("Run 'python migrate.py' for usage information")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
