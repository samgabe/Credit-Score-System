"""
Global exception handlers for the Credit Score API.
Handles validation errors, not found errors, authentication errors, and server errors.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Union
import logging

from app.exceptions import NotFoundException, AuthenticationException, ValidationException, DuplicateNationalIDError, UserNotFoundError, NoScoreAvailable, CalculationError
from app.schemas.error import ErrorResponse

# Configure logging
logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationException]
) -> JSONResponse:
    """
    Handler for validation errors (400).
    Handles both FastAPI's RequestValidationError and custom ValidationException.
    """
    if isinstance(exc, RequestValidationError):
        # Extract validation error details from Pydantic
        error_details = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_details[field] = error["msg"]
        
        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid request data",
            timestamp=datetime.utcnow(),
            details=error_details
        )
    else:
        # Custom ValidationException
        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message=exc.message,
            timestamp=datetime.utcnow(),
            details=exc.details
        )
    
    logger.warning(f"Validation error on {request.url}: {error_response.message}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(mode='json')
    )


async def not_found_exception_handler(
    request: Request, 
    exc: NotFoundException
) -> JSONResponse:
    """
    Handler for not found errors (404).
    """
    error_response = ErrorResponse(
        error_code="NOT_FOUND",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details={
            "resource": exc.resource,
            "identifier": exc.identifier
        }
    )
    
    logger.info(f"Resource not found on {request.url}: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump(mode='json')
    )


async def authentication_exception_handler(
    request: Request, 
    exc: AuthenticationException
) -> JSONResponse:
    """
    Handler for authentication errors (401).
    """
    error_response = ErrorResponse(
        error_code="AUTHENTICATION_FAILED",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details=None
    )
    
    logger.warning(f"Authentication failed on {request.url}: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(mode='json'),
        headers={"WWW-Authenticate": "Bearer"}
    )


async def database_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handler for database errors (500).
    """
    error_response = ErrorResponse(
        error_code="DATABASE_ERROR",
        message="A database error occurred",
        timestamp=datetime.utcnow(),
        details={"error_type": type(exc).__name__}
    )
    
    logger.error(
        f"Database error on {request.url}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Handler for unexpected server errors (500).
    Catches all unhandled exceptions.
    """
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        timestamp=datetime.utcnow(),
        details={"error_type": type(exc).__name__}
    )
    
    logger.error(
        f"Unexpected error on {request.url}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def duplicate_national_id_exception_handler(
    request: Request,
    exc: DuplicateNationalIDError
) -> JSONResponse:
    """
    Handler for duplicate national ID errors (409).
    """
    error_response = ErrorResponse(
        error_code="DUPLICATE_NATIONAL_ID",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details={"national_id": exc.national_id}
    )
    
    logger.warning(f"Duplicate national ID on {request.url}: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response.model_dump(mode='json')
    )


async def user_not_found_exception_handler(
    request: Request,
    exc: UserNotFoundError
) -> JSONResponse:
    """
    Handler for user not found errors (404).
    """
    error_response = ErrorResponse(
        error_code="USER_NOT_FOUND",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details={
            "resource": exc.resource,
            "identifier": exc.identifier
        }
    )
    
    logger.info(f"User not found on {request.url}: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump(mode='json')
    )


async def no_score_available_exception_handler(
    request: Request,
    exc: NoScoreAvailable
) -> JSONResponse:
    """
    Handler for no score available errors (404).
    """
    error_response = ErrorResponse(
        error_code="NO_SCORE_AVAILABLE",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details={"user_id": exc.user_id}
    )
    
    logger.info(f"No score available on {request.url}: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump(mode='json')
    )


async def calculation_error_exception_handler(
    request: Request,
    exc: CalculationError
) -> JSONResponse:
    """
    Handler for calculation errors (500).
    """
    error_response = ErrorResponse(
        error_code="CALCULATION_ERROR",
        message=exc.message,
        timestamp=datetime.utcnow(),
        details={"error_details": exc.details} if exc.details else None
    )
    
    logger.error(f"Calculation error on {request.url}: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )
