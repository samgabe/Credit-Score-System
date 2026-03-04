# Credit Score API

A FastAPI-based RESTful service that calculates and manages credit scores for users based on their financial behavior.

## Project Structure

```
credit-score-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and session management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routers/         # API endpoint routers
│   │       └── __init__.py
│   ├── models/              # SQLAlchemy database models
│   │   └── __init__.py
│   ├── schemas/             # Pydantic request/response schemas
│   │   └── __init__.py
│   ├── services/            # Business logic services
│   │   └── __init__.py
│   └── repositories/        # Data access layer
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── unit/                # Unit tests
│   │   └── __init__.py
│   ├── property/            # Property-based tests
│   │   └── __init__.py
│   └── integration/         # Integration tests
│       └── __init__.py
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update with your database credentials:

```bash
copy .env.example .env
```

Edit `.env` with your PostgreSQL connection details.

### 5. Set Up PostgreSQL Database

Run the database creation script:

```bash
python create_databases.py
```

This will automatically create both databases if they don't exist.

### 6. Initialize Database with Migrations

Run the database initialization script to create all tables and indexes:

```bash
python init_db.py init
```

This uses Alembic migrations to set up the database schema. For more information about database migrations, see `alembic/README.md`.

**Alternative Commands:**
- Show current database revision: `python init_db.py current`
- Show migration history: `python init_db.py history`
- Reset database (WARNING: deletes all data): `python init_db.py reset`

### 7. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 8. View API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Property-Based Tests Only

```bash
pytest tests/property/
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Database (via psycopg2-binary)
- **Pydantic**: Data validation using Python type annotations
- **Alembic**: Database migration tool
- **Hypothesis**: Property-based testing framework
- **Pytest**: Testing framework
- **Uvicorn**: ASGI server

## Database Migrations

This project uses Alembic for database migrations. Migrations allow you to:
- Track database schema changes over time
- Apply changes to the database in a controlled manner
- Rollback changes if needed
- Keep database schema in sync across environments

### Common Migration Commands

**Initialize database (first time):**
```bash
python init_db.py init
```

**Create a new migration after modifying models:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migrations:**
```bash
alembic downgrade -1
```

For more details, see `alembic/README.md`.

## API Endpoints

API endpoints will be documented here as they are implemented.

## Development

This project follows a layered architecture:

1. **API Layer**: FastAPI routers handling HTTP requests/responses
2. **Business Logic Layer**: Services containing core domain logic
3. **Data Access Layer**: Repositories abstracting database operations
4. **Database Layer**: PostgreSQL with SQLAlchemy ORM

## Requirements

- Python 3.9+
- PostgreSQL 12+
