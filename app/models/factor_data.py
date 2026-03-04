"""
Factor Data Transfer Objects for Credit Score Calculation

These dataclasses represent aggregated data from various system components
used in credit score calculations. They serve as the interface between
the Data Integration Layer and the Credit Score Calculator.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

from dataclasses import dataclass


@dataclass
class RepaymentData:
    """
    Aggregated repayment history data for a user.
    
    Used to calculate the repayment factor (35% weight) in credit scoring.
    Requirements: 2.1
    """
    total_payments: int
    on_time_payments: int
    late_payments: int
    defaulted_payments: int
    on_time_rate: float  # Calculated: on_time / total


@dataclass
class MpesaData:
    """
    Aggregated M-Pesa transaction data for a user.
    
    Used to calculate the M-Pesa factor (20% weight) in credit scoring.
    Requirements: 2.2
    """
    transaction_count: int
    total_volume: float
    average_transaction: float
    frequency_days: float  # Average days between transactions


@dataclass
class ConsistencyData:
    """
    Aggregated payment consistency metrics for a user.
    
    Used to calculate the consistency factor (25% weight) in credit scoring.
    Requirements: 2.3
    """
    payment_count: int
    average_gap_days: float
    max_gap_days: int
    regularity_score: float  # 0-1, based on standard deviation


@dataclass
class FineData:
    """
    Aggregated fine history data for a user.
    
    Used to calculate the fine factor (20% weight) in credit scoring.
    Requirements: 2.4
    """
    total_fines: int
    unpaid_fines: int
    total_fine_amount: float
    unpaid_fine_amount: float
    unpaid_rate: float  # Calculated: unpaid / total
