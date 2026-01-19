"""
Custom exceptions for the Credit Score API.
"""


class NotFoundException(Exception):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        self.message = f"{resource} with ID {identifier} does not exist"
        super().__init__(self.message)


class UserNotFoundError(NotFoundException):
    """Exception raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__("User", user_id)


class AuthenticationException(Exception):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class ValidationException(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# Alias for ValidationException to match design document naming
ValidationError = ValidationException


class DuplicateNationalIDError(Exception):
    """Exception raised when attempting to create a user with a duplicate national ID."""
    
    def __init__(self, national_id: int):
        self.national_id = national_id
        self.message = f"A user with national ID {national_id} already exists"
        super().__init__(self.message)


class NoScoreAvailable(Exception):
    """Exception raised when no credit score is available for a user."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.message = f"No credit score found for user {user_id}"
        super().__init__(self.message)


class CalculationError(Exception):
    """Exception raised when credit score calculation fails."""
    
    def __init__(self, message: str = "Failed to calculate credit score", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
