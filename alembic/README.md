# Database Migrations with Alembic

This directory contains database migration files managed by Alembic.

## Overview

Alembic is a database migration tool for SQLAlchemy. It allows you to:
- Track database schema changes over time
- Apply migrations to upgrade the database
- Rollback migrations to downgrade the database
- Generate migrations automatically from model changes

## Directory Structure

```
alembic/
├── versions/          # Migration files
├── env.py            # Alembic environment configuration
├── script.py.mako    # Template for new migrations
└── README.md         # This file
```

## Common Commands

### Initialize Database (First Time Setup)

```bash
python init_db.py init
```

This will run all migrations and create all tables in the database.

### Show Current Database Revision

```bash
python init_db.py current
```

### Show Migration History

```bash
python init_db.py history
```

### Reset Database (WARNING: Deletes all data!)

```bash
python init_db.py reset
```

### Create a New Migration

After modifying models in `app/models/`, generate a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

Upgrade to the latest version:

```bash
alembic upgrade head
```

Upgrade to a specific revision:

```bash
alembic upgrade <revision_id>
```

### Rollback Migrations

Downgrade by one revision:

```bash
alembic downgrade -1
```

Downgrade to a specific revision:

```bash
alembic downgrade <revision_id>
```

Downgrade to base (remove all tables):

```bash
alembic downgrade base
```

## Migration Files

Migration files are stored in `alembic/versions/` and contain:
- `upgrade()`: Function to apply the migration
- `downgrade()`: Function to rollback the migration

Each migration has a unique revision ID and references the previous migration.

## Configuration

Database connection is configured in:
- `alembic.ini`: Alembic configuration file
- `alembic/env.py`: Environment setup (imports models and config)
- `app/config.py`: Application configuration with database URL

The database URL is loaded from environment variables via `app/config.py`.

## Indexes

The following indexes are created for optimal query performance:

### Users Table
- `ix_users_email`: Index on email field (unique)

### Repayments Table
- `ix_repayments_user_id`: Index on user_id for fast user lookups
- `ix_repayments_created_at`: Index on created_at for date-based queries

### M-Pesa Transactions Table
- `ix_mpesa_transactions_user_id`: Index on user_id
- `ix_mpesa_transactions_created_at`: Index on created_at

### Fines Table
- `ix_fines_user_id`: Index on user_id
- `ix_fines_created_at`: Index on created_at

### Payments Table
- `ix_payments_user_id`: Index on user_id
- `ix_payments_created_at`: Index on created_at

### Credit Scores Table
- `ix_credit_scores_user_id`: Index on user_id
- `ix_credit_scores_user_calculated`: Composite index on (user_id, calculated_at) for efficient score history queries

## Best Practices

1. **Always review generated migrations** before applying them
2. **Test migrations** on a development database first
3. **Backup production data** before running migrations
4. **Never edit applied migrations** - create a new migration instead
5. **Keep migrations small** and focused on specific changes
6. **Write descriptive migration messages** for clarity

## Troubleshooting

### Migration conflicts
If you have migration conflicts, you may need to merge branches:
```bash
alembic merge <rev1> <rev2> -m "Merge migrations"
```

### Database out of sync
If your database schema doesn't match the migrations:
1. Check current revision: `python init_db.py current`
2. Check migration history: `python init_db.py history`
3. Apply missing migrations: `alembic upgrade head`

### Reset everything (development only)
```bash
python init_db.py reset
```

This will drop all tables and recreate them from scratch.
