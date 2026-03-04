"""
Main FastAPI application entry point.
Configures the application, middleware, and routes.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings
from app.database import init_db
from app.exceptions import NotFoundException, AuthenticationException, ValidationException, DuplicateNationalIDError, UserNotFoundError, NoScoreAvailable, CalculationError
from app.exception_handlers import (
    validation_exception_handler,
    not_found_exception_handler,
    authentication_exception_handler,
    database_exception_handler,
    general_exception_handler,
    duplicate_national_id_exception_handler,
    user_not_found_exception_handler,
    no_score_available_exception_handler,
    calculation_error_exception_handler
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(UserNotFoundError, user_not_found_exception_handler)
app.add_exception_handler(DuplicateNationalIDError, duplicate_national_id_exception_handler)
app.add_exception_handler(NoScoreAvailable, no_score_available_exception_handler)
app.add_exception_handler(CalculationError, calculation_error_exception_handler)
app.add_exception_handler(AuthenticationException, authentication_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("Initializing database connection...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info(f"Application ready - Debug mode: {settings.debug}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# Import routers
from app.api.routers.auth_router import router as auth_router
from app.api.routers.user_router import router as user_router
from app.api.routers.credit_score_router import router as credit_score_router
from app.api.routers.analytics_router import router as analytics_router
from app.api.routers.csv_upload_router import router as csv_upload_router

# Register all routers with /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(credit_score_router, prefix="/api/v1", tags=["credit-scores"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(csv_upload_router, prefix="/api/v1", tags=["csv-upload"])
