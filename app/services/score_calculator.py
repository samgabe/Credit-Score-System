"""
Credit Score Calculator Service

This service calculates credit scores based on aggregated factor data.
It implements the credit score calculation logic as specified in the design document,
using weighted factors to produce a final score in the range 0-850.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4
"""

from dataclasses import dataclass
from app.models.factor_data import (
    RepaymentData,
    MpesaData,
    ConsistencyData,
    FineData
)


@dataclass
class CreditScoreResult:
    """
    Result of credit score calculation containing total score and factor contributions.
    
    Attributes:
        total_score: Final credit score (0-850)
        category: Score category (Poor, Fair, Good, Excellent)
        repayment_factor: Contribution from repayment history (0-297.5)
        mpesa_factor: Contribution from M-Pesa transactions (0-170)
        consistency_factor: Contribution from payment consistency (0-212.5)
        fine_factor: Contribution from fines (0-170)
    """
    total_score: int
    category: str
    repayment_factor: float
    mpesa_factor: float
    consistency_factor: float
    fine_factor: float


class CreditScoreCalculator:
    """
    Calculates credit scores from aggregated factor data.
    
    This calculator implements the credit scoring algorithm using weighted factors:
    - Repayment history: 35% weight (max 297.5 points)
    - M-Pesa transactions: 20% weight (max 170 points)
    - Payment consistency: 25% weight (max 212.5 points)
    - Fines: 20% weight (max 170 points)
    
    The final score is always in the range 0-850.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4
    """
    
    # Weight constants (Requirements 3.1, 3.2, 3.3, 3.4)
    REPAYMENT_WEIGHT = 0.35    # 35%
    MPESA_WEIGHT = 0.20        # 20%
    CONSISTENCY_WEIGHT = 0.25  # 25%
    FINE_WEIGHT = 0.20         # 20%
    
    # Maximum score constant (Requirement 3.5)
    MAX_SCORE = 850
    
    def calculate_score(
        self,
        repayment_data: RepaymentData,
        mpesa_data: MpesaData,
        consistency_data: ConsistencyData,
        fine_data: FineData
    ) -> CreditScoreResult:
        """
        Calculate credit score from factor data.
        
        Combines all factor contributions using their respective weights to produce
        a final score. Ensures the score is always within the valid range 0-850.
        
        Args:
            repayment_data: Aggregated repayment history data
            mpesa_data: Aggregated M-Pesa transaction data
            consistency_data: Aggregated payment consistency data
            fine_data: Aggregated fine history data
            
        Returns:
            CreditScoreResult: Complete score result with factor breakdown
            
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
        """
        # Calculate individual factor contributions
        repayment_factor = self.calculate_repayment_factor(repayment_data)
        mpesa_factor = self.calculate_mpesa_factor(mpesa_data)
        consistency_factor = self.calculate_consistency_factor(consistency_data)
        fine_factor = self.calculate_fine_factor(fine_data)
        
        # Calculate total score by summing all factor contributions
        total_score = (
            repayment_factor +
            mpesa_factor +
            consistency_factor +
            fine_factor
        )
        
        # Ensure score is within valid range 0-850 (Requirement 3.5)
        total_score = max(0, min(self.MAX_SCORE, int(total_score)))
        
        # Categorize the score (Requirements 4.1, 4.2, 4.3, 4.4)
        category = self.categorize_score(total_score)
        
        return CreditScoreResult(
            total_score=total_score,
            category=category,
            repayment_factor=repayment_factor,
            mpesa_factor=mpesa_factor,
            consistency_factor=consistency_factor,
            fine_factor=fine_factor
        )
    
    def calculate_repayment_factor(self, data: RepaymentData) -> float:
        """
        Calculate repayment contribution (max 297.5 points = 35% of 850).
        
        Formula:
        - On-time payment rate: 70% of factor weight (208.25 points max)
        - Default rate penalty: 30% of factor weight (89.25 points max)
        
        For users with no credit history, provide a neutral baseline score
        rather than zero, as absence of negative history shouldn't be penalizing.
        
        Args:
            data: Aggregated repayment history data
            
        Returns:
            float: Repayment factor contribution (0-297.5)
            
        Requirement: 3.1
        """
        max_factor_score = self.MAX_SCORE * self.REPAYMENT_WEIGHT  # 297.5
        
        # Handle case with no repayments - give neutral baseline score
        # rather than zero, as no history is better than bad history
        if data.total_payments == 0:
            # Give 50% of maximum possible points as neutral baseline
            return max_factor_score * 0.5
        
        # On-time payment rate contributes 70% of factor weight
        on_time_contribution = data.on_time_rate * max_factor_score * 0.70
        
        # Default rate penalty (30% of factor weight)
        # Calculate default rate
        default_rate = data.defaulted_payments / data.total_payments if data.total_payments > 0 else 0.0
        
        # Penalty reduces remaining 30% based on default rate
        # If no defaults, get full 30%; if all defaults, get 0%
        default_contribution = (1.0 - default_rate) * max_factor_score * 0.30
        
        # Total repayment factor
        total_factor = on_time_contribution + default_contribution
        
        # Ensure within bounds
        return max(0.0, min(max_factor_score, total_factor))
    
    def calculate_mpesa_factor(self, data: MpesaData) -> float:
        """
        Calculate M-Pesa contribution (max 170 points = 20% of 850).
        
        Formula:
        - Transaction frequency: 50% of factor weight (85 points max)
        - Transaction volume: 50% of factor weight (85 points max)
        
        Higher transaction frequency and volume indicate active financial behavior.
        
        Args:
            data: Aggregated M-Pesa transaction data
            
        Returns:
            float: M-Pesa factor contribution (0-170)
            
        Requirement: 3.2
        """
        max_factor_score = self.MAX_SCORE * self.MPESA_WEIGHT  # 170
        
        # Handle case with no transactions - give neutral baseline score
        if data.transaction_count == 0:
            # Give 40% of maximum possible points as neutral baseline
            # M-Pesa activity is less critical than repayment history
            return max_factor_score * 0.4
        
        # Transaction frequency contributes 50% of factor weight
        # Normalize frequency: assume 30 transactions per month is excellent
        # frequency_days: lower is better (more frequent transactions)
        # Convert to frequency score: more transactions = higher score
        frequency_score = 0.0
        if data.frequency_days > 0:
            # Calculate transactions per month (30 days)
            transactions_per_month = 30.0 / data.frequency_days
            # Normalize to 0-1 scale (30 transactions/month = 1.0)
            normalized_frequency = min(transactions_per_month / 30.0, 1.0)
            frequency_score = normalized_frequency * max_factor_score * 0.50
        else:
            # If frequency_days is 0, use transaction count directly
            # Normalize: 30+ transactions = perfect score
            normalized_frequency = min(data.transaction_count / 30.0, 1.0)
            frequency_score = normalized_frequency * max_factor_score * 0.50
        
        # Transaction volume contributes 50% of factor weight
        # Normalize volume: assume $10,000 total volume is excellent
        normalized_volume = min(data.total_volume / 10000.0, 1.0)
        volume_score = normalized_volume * max_factor_score * 0.50
        
        # Total M-Pesa factor
        total_factor = frequency_score + volume_score
        
        # Ensure within bounds
        return max(0.0, min(max_factor_score, total_factor))
    
    def calculate_consistency_factor(self, data: ConsistencyData) -> float:
        """
        Calculate consistency contribution (max 212.5 points = 25% of 850).
        
        Formula:
        - Payment regularity: 60% of factor weight (127.5 points max)
        - Gap between payments: 40% of factor weight (85 points max)
        
        Regular payment patterns with smaller gaps score higher.
        
        Args:
            data: Aggregated payment consistency data
            
        Returns:
            float: Consistency factor contribution (0-212.5)
            
        Requirement: 3.3
        """
        max_factor_score = self.MAX_SCORE * self.CONSISTENCY_WEIGHT  # 212.5
        
        # Handle case with no payments - give neutral baseline score
        if data.payment_count == 0:
            # Give 45% of maximum possible points as neutral baseline
            # Payment consistency is important but absence isn't penalizing
            return max_factor_score * 0.45
        
        # Payment regularity contributes 60% of factor weight
        # regularity_score is already 0-1 from the aggregator
        regularity_contribution = data.regularity_score * max_factor_score * 0.60
        
        # Gap between payments contributes 40% of factor weight
        # Smaller gaps are better
        # Normalize: assume 30 days average gap is excellent, 90+ days is poor
        gap_score = 0.0
        if data.average_gap_days > 0:
            # Inverse relationship: smaller gap = higher score
            # 0-30 days = 1.0, 90+ days = 0.0
            normalized_gap = max(0.0, min(1.0, (90.0 - data.average_gap_days) / 60.0))
            gap_score = normalized_gap * max_factor_score * 0.40
        else:
            # If average gap is 0 (single payment or same-day payments), give full score
            gap_score = max_factor_score * 0.40
        
        # Total consistency factor
        total_factor = regularity_contribution + gap_score
        
        # Ensure within bounds
        return max(0.0, min(max_factor_score, total_factor))
    
    def calculate_fine_factor(self, data: FineData) -> float:
        """
        Calculate fine contribution (max 170 points = 20% of 850).
        
        Formula:
        - Unpaid fines penalty: 60% of factor weight (102 points max)
        - Fine frequency penalty: 40% of factor weight (68 points max)
        
        Fewer fines and lower unpaid rates result in higher scores.
        
        Args:
            data: Aggregated fine history data
            
        Returns:
            float: Fine factor contribution (0-170)
            
        Requirement: 3.4
        """
        max_factor_score = self.MAX_SCORE * self.FINE_WEIGHT  # 170
        
        # Handle case with no fines (no fines = perfect score for this factor)
        if data.total_fines == 0:
            return max_factor_score
        
        # Unpaid fines penalty: 60% of factor weight
        # Lower unpaid rate = higher score
        unpaid_contribution = (1.0 - data.unpaid_rate) * max_factor_score * 0.60
        
        # Fine frequency penalty: 40% of factor weight
        # Normalize: 0 fines = 1.0, 10+ fines = 0.0
        normalized_fine_frequency = max(0.0, min(1.0, (10.0 - data.total_fines) / 10.0))
        frequency_contribution = normalized_fine_frequency * max_factor_score * 0.40
        
        # Total fine factor
        total_factor = unpaid_contribution + frequency_contribution
        
        # Ensure within bounds
        return max(0.0, min(max_factor_score, total_factor))
    
    def categorize_score(self, score: int) -> str:
        """
        Categorize a credit score into Poor, Fair, Good, or Excellent.
        
        Categories (Requirements 4.1, 4.2, 4.3, 4.4):
        - Poor: 0-549
        - Fair: 550-649
        - Good: 650-749
        - Excellent: 750-850
        
        Args:
            score: Credit score value (0-850)
            
        Returns:
            str: Score category
            
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        if score <= 549:
            return "Poor"
        elif score <= 649:
            return "Fair"
        elif score <= 749:
            return "Good"
        else:  # 750-850
            return "Excellent"
