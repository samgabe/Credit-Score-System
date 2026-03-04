"""
Data Source Factory for Credit Score Calculation

This factory creates the appropriate data source (database or CSV)
based on application configuration. It provides a unified interface
for both database and CSV data sources.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Union
from uuid import UUID
from app.config import get_settings
from app.services.factor_data_aggregator import FactorDataAggregator
from app.services.csv_data_loader import CSVDataLoader
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.fine_repository import FineRepository
from app.repositories.user_repository import UserRepository


class DataSourceFactory:
    """
    Factory for creating data sources based on configuration.
    
    This factory determines whether to use database repositories
    or CSV files based on the data_source configuration setting.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    def __init__(self):
        """Initialize the factory with settings."""
        self.settings = get_settings()
    
    def create_factor_data_aggregator(
        self,
        repayment_repository: RepaymentRepository = None,
        mpesa_transaction_repository: MpesaTransactionRepository = None,
        payment_repository: PaymentRepository = None,
        fine_repository: FineRepository = None
    ) -> Union[FactorDataAggregator, CSVDataLoader]:
        """
        Create the appropriate factor data aggregator based on configuration.
        
        Args:
            repayment_repository: Database repository for repayments (required for database mode)
            mpesa_transaction_repository: Database repository for M-Pesa transactions (required for database mode)
            payment_repository: Database repository for payments (required for database mode)
            fine_repository: Database repository for fines (required for database mode)
            
        Returns:
            Union[FactorDataAggregator, CSVDataLoader]: Appropriate data source
        """
        if self.settings.data_source.lower() == "csv":
            return CSVDataLoader(csv_directory=self.settings.csv_directory)
        elif self.settings.data_source.lower() == "database":
            # Validate that all required repositories are provided
            if not all([repayment_repository, mpesa_transaction_repository, payment_repository, fine_repository]):
                raise ValueError("All repositories must be provided when using database data source")
            
            return FactorDataAggregator(
                repayment_repository=repayment_repository,
                mpesa_transaction_repository=mpesa_transaction_repository,
                payment_repository=payment_repository,
                fine_repository=fine_repository
            )
        else:
            raise ValueError(f"Invalid data source configuration: {self.settings.data_source}. Must be 'database' or 'csv'")
    
    def create_user_repository(self, db_session=None) -> Union[UserRepository, CSVDataLoader]:
        """
        Create the appropriate user repository based on configuration.
        
        Args:
            db_session: Database session (required for database mode)
            
        Returns:
            Union[UserRepository, CSVDataLoader]: Appropriate user data source
        """
        if self.settings.data_source.lower() == "csv":
            return CSVDataLoader(csv_directory=self.settings.csv_directory)
        elif self.settings.data_source.lower() == "database":
            if not db_session:
                raise ValueError("Database session must be provided when using database data source")
            return UserRepository(db=db_session)
        else:
            raise ValueError(f"Invalid data source configuration: {self.settings.data_source}. Must be 'database' or 'csv'")
    
    def is_csv_mode(self) -> bool:
        """
        Check if the application is configured to use CSV data source.
        
        Returns:
            bool: True if using CSV mode, False otherwise
        """
        return self.settings.data_source.lower() == "csv"
    
    def is_database_mode(self) -> bool:
        """
        Check if the application is configured to use database data source.
        
        Returns:
            bool: True if using database mode, False otherwise
        """
        return self.settings.data_source.lower() == "database"
