"""
Configuration management for the Credit Score API.
Handles environment variables and application settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://user:password@localhost:5432/credit_score_db"
    test_database_url: str = "postgresql://user:password@localhost:5432/credit_score_test_db"
    
    # Application Configuration
    app_name: str = "Credit Score API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database Connection Pool Settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Data Source Configuration
    data_source: str = "database"  # Options: "database" or "csv"
    csv_directory: str = "csv_data"  # Directory containing CSV files when using CSV data source
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
