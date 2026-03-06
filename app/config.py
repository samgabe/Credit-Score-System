"""
Configuration management for Credit Score API.
Handles environment variables and application settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "credit_score_db"
    db_user: str = "user"
    db_password: str = "password"
    
    # Construct database URL from components
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def test_database_url(self) -> str:
        return f"postgresql://{self.test_db_user}:{self.test_db_password}@{self.test_db_host}:{self.test_db_port}/{self.test_db_name}"
    
    # Application Configuration
    app_name: str = "Credit Score API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # JWT Configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # Database Connection Pool Settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Data Source Configuration
    data_source: str = "database"  # Options: "database" or "csv"
    csv_directory: str = "csv_data"  # Directory containing CSV files when using CSV data source
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security Configuration
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB in bytes
    upload_directory: str = "uploads"
    
    # Credit Score Configuration
    min_credit_score: int = 300
    max_credit_score: int = 850
    default_credit_score: int = 500
    
    # Analytics Configuration
    analytics_cache_ttl: int = 300  # 5 minutes
    analytics_batch_size: int = 1000
    
    # Development Configuration
    development_mode: bool = False
    enable_profiling: bool = False
    enable_debug_routes: bool = False
    
    # Test Database Configuration
    test_db_host: str = "localhost"
    test_db_port: int = 5432
    test_db_name: str = "credit_score_test_db"
    test_db_user: str = "user"
    test_db_password: str = "password"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Email Configuration (optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@creditscore.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
