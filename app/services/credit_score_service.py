"""
Credit Score Service

This service orchestrates credit score calculation and storage operations.
It coordinates between the Factor Data Aggregator, Credit Score Calculator,
and Credit Score Repository to provide a complete credit scoring workflow.

Requirements: 3.6, 3.7, 5.3, 5.4, 7.1, 7.2, 7.5
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from app.services.factor_data_aggregator import FactorDataAggregator
from app.services.score_calculator import CreditScoreCalculator
from app.repositories.credit_score_repository import CreditScoreRepository
from app.models.credit_score import CreditScore


class CreditScoreService:
    """
    Service for managing credit score calculation and retrieval operations.
    
    This service orchestrates the credit scoring workflow:
    1. Retrieves factor data from existing system components
    2. Calculates credit score using the calculator
    3. Stores the result in the database
    4. Provides access to current and historical scores
    
    Requirements: 3.6, 3.7, 5.3, 5.4, 7.1, 7.2, 7.5
    """
    
    def __init__(
        self,
        factor_aggregator: FactorDataAggregator,
        calculator: CreditScoreCalculator,
        credit_score_repository: CreditScoreRepository
    ):
        """
        Initialize the CreditScoreService with dependencies.
        
        Args:
            factor_aggregator: Service for retrieving factor data from existing systems
            calculator: Service for calculating credit scores from factor data
            credit_score_repository: Repository for credit score data persistence
        """
        self.factor_aggregator = factor_aggregator
        self.calculator = calculator
        self.credit_score_repository = credit_score_repository
    
    def calculate_and_store_score(self, user_id: UUID) -> CreditScore:
        """
        Calculate credit score for a user and store it in the database.
        
        This method orchestrates the complete credit scoring workflow:
        1. Retrieves factor data from the aggregator
        2. Calculates the credit score using the calculator
        3. Stores the result in the repository
        4. Returns the stored credit score
        
        The method handles both complete and partial data scenarios:
        - If all factor data is available, calculates a complete score
        - If some factor data is missing, calculates a partial score
        
        Args:
            user_id: UUID of the user to calculate score for
            
        Returns:
            CreditScore: The calculated and stored credit score object
            
        Requirements: 3.6, 3.7, 7.1
        """
        # Step 1: Retrieve factor data from aggregator
        repayment_data = self.factor_aggregator.get_repayment_data(user_id)
        mpesa_data = self.factor_aggregator.get_mpesa_data(user_id)
        consistency_data = self.factor_aggregator.get_payment_consistency_data(user_id)
        fine_data = self.factor_aggregator.get_fine_data(user_id)
        
        # Step 2: Calculate score using calculator
        score_result = self.calculator.calculate_score(
            repayment_data=repayment_data,
            mpesa_data=mpesa_data,
            consistency_data=consistency_data,
            fine_data=fine_data
        )
        
        # Step 3: Store result in repository
        credit_score = self.credit_score_repository.create(
            user_id=user_id,
            score=score_result.total_score,
            category=score_result.category,
            repayment_factor=score_result.repayment_factor,
            mpesa_factor=score_result.mpesa_factor,
            consistency_factor=score_result.consistency_factor,
            fine_factor=score_result.fine_factor
        )
        
        # Step 4: Return stored credit score
        return credit_score
    
    def get_latest_score(self, user_id: UUID) -> Optional[CreditScore]:
        """
        Retrieve the most recent credit score for a user.
        
        Returns None if the user has no credit score, allowing the caller
        to handle the "no score available" case appropriately.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Optional[CreditScore]: Most recent credit score if available, None otherwise
            
        Requirements: 5.3, 7.1, 7.2
        """
        return self.credit_score_repository.get_latest_by_user_id(user_id)
    
    def get_score_history(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CreditScore]:
        """
        Retrieve credit score history for a user within an optional date range.
        
        If no date range is specified, returns all historical scores for the user.
        If start_date is specified, returns scores from that date forward.
        If end_date is specified, returns scores up to that date.
        If both are specified, returns scores within the range (inclusive).
        
        Args:
            user_id: UUID of the user
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            List[CreditScore]: List of credit scores sorted by date (most recent first)
            
        Requirements: 5.4, 7.5
        """
        return self.credit_score_repository.get_history_by_user_id(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
