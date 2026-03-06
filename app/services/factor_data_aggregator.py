"""
Factor Data Aggregator Service for Credit Score Calculation

This service retrieves and aggregates data from existing system repositories
to provide factor data for credit score calculations. It implements the
Data Integration Layer as specified in the design document.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from statistics import stdev
from app.models.factor_data import (
    RepaymentData,
    MpesaData,
    ConsistencyData,
    FineData
)
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.fine_repository import FineRepository
from app.models.repayment import RepaymentStatus
from app.models.fine import FineStatus
from app.models.payment import PaymentStatus


class FactorDataAggregator:
    """
    Aggregates data from existing system repositories for credit score calculation.
    
    This class implements the Data Integration Layer, retrieving data from
    existing repositories without modifying source data. It handles missing
    or incomplete data gracefully by returning empty structures.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    def __init__(
        self,
        repayment_repository: RepaymentRepository,
        mpesa_transaction_repository: MpesaTransactionRepository,
        payment_repository: PaymentRepository,
        fine_repository: FineRepository
    ):
        """
        Initialize the FactorDataAggregator with repository dependencies.
        
        Args:
            repayment_repository: Repository for repayment data access
            mpesa_transaction_repository: Repository for M-Pesa transaction data access
            payment_repository: Repository for payment data access
            fine_repository: Repository for fine data access
        """
        self.repayment_repository = repayment_repository
        self.mpesa_transaction_repository = mpesa_transaction_repository
        self.payment_repository = payment_repository
        self.fine_repository = fine_repository

    def get_repayment_data(self, user_id: UUID) -> RepaymentData:
        """
        Retrieve and aggregate repayment history data for a credit subject.
        
        Updated to work with credit subjects instead of system users.
        
        Calculates metrics including total payments, on-time payments,
        late payments, defaulted payments, and on-time rate.
        
        Handles missing/incomplete data gracefully by returning empty
        structures with zero values.
        
        Args:
            user_id: UUID of the credit subject (keeping parameter name for compatibility)
            
        Returns:
            RepaymentData: Aggregated repayment metrics
            
        Requirements: 2.1, 2.5
        """
        try:
            # Try to get repayments by credit_subject_id first (new approach)
            repayments = self.repayment_repository.get_by_credit_subject(user_id)
            
            # Fallback to user_id for legacy data
            if not repayments:
                repayments = self.repayment_repository.get_by_user(user_id)
            
            # Handle case where subject has no repayments
            if not repayments:
                return RepaymentData(
                    total_payments=0,
                    on_time_payments=0,
                    late_payments=0,
                    defaulted_payments=0,
                    on_time_rate=0.0
                )
            
            # Count repayments by status
            on_time_count = sum(1 for r in repayments if r.status == RepaymentStatus.on_time)
            late_count = sum(1 for r in repayments if r.status == RepaymentStatus.late)
            
            # For now, we consider payments more than 30 days overdue as defaulted
            defaulted_count = sum(1 for r in repayments if r.status == RepaymentStatus.late and r.days_overdue > 30)
            
            total_count = len(repayments)
            on_time_rate = on_time_count / total_count if total_count > 0 else 0.0
            
            return RepaymentData(
                total_payments=total_count,
                on_time_payments=on_time_count,
                late_payments=late_count,
                defaulted_payments=defaulted_count,
                on_time_rate=on_time_rate
            )
        except Exception as e:
            # Log error and return empty structure
            # In production, use proper logging
            return RepaymentData(
                total_payments=0,
                on_time_payments=0,
                late_payments=0,
                defaulted_payments=0,
                on_time_rate=0.0
            )

    def get_mpesa_data(self, user_id: UUID) -> MpesaData:
        """
        Retrieve and aggregate M-Pesa transaction data for a user.
        
        Calculates metrics including transaction count, total volume,
        average transaction amount, and transaction frequency.
        
        Handles missing/incomplete data gracefully by returning empty
        structures with zero values.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            MpesaData: Aggregated M-Pesa transaction metrics
            
        Requirements: 2.2, 2.5
        """
        try:
            transactions = self.mpesa_transaction_repository.get_by_user(user_id)
            
            # Handle case where user has no M-Pesa transactions
            if not transactions:
                return MpesaData(
                    transaction_count=0,
                    total_volume=0.0,
                    average_transaction=0.0,
                    frequency_days=0.0
                )
            
            # Calculate transaction metrics
            transaction_count = len(transactions)
            total_volume = sum(float(t.amount) for t in transactions)
            average_transaction = total_volume / transaction_count if transaction_count > 0 else 0.0
            
            # Calculate frequency (average days between transactions)
            frequency_days = 0.0
            if transaction_count > 1:
                # Sort transactions by date
                sorted_transactions = sorted(transactions, key=lambda t: t.transaction_date)
                
                # Calculate gaps between consecutive transactions
                gaps = []
                for i in range(1, len(sorted_transactions)):
                    gap = (sorted_transactions[i].transaction_date - sorted_transactions[i-1].transaction_date).days
                    gaps.append(gap)
                
                frequency_days = sum(gaps) / len(gaps) if gaps else 0.0
            
            return MpesaData(
                transaction_count=transaction_count,
                total_volume=total_volume,
                average_transaction=average_transaction,
                frequency_days=frequency_days
            )
        except Exception as e:
            # Log error and return empty structure
            return MpesaData(
                transaction_count=0,
                total_volume=0.0,
                average_transaction=0.0,
                frequency_days=0.0
            )

    def get_payment_consistency_data(self, user_id: UUID) -> ConsistencyData:
        """
        Retrieve and aggregate payment consistency metrics for a user.
        
        Calculates metrics including payment count, average gap between payments,
        maximum gap, and regularity score based on payment pattern consistency.
        
        Handles missing/incomplete data gracefully by returning empty
        structures with zero values.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            ConsistencyData: Aggregated payment consistency metrics
            
        Requirements: 2.3, 2.5
        """
        try:
            payments = self.payment_repository.get_by_user(user_id)
            
            # Filter to only completed payments
            completed_payments = [p for p in payments if p.status == PaymentStatus.completed]
            
            # Handle case where user has no completed payments
            if not completed_payments:
                return ConsistencyData(
                    payment_count=0,
                    average_gap_days=0.0,
                    max_gap_days=0,
                    regularity_score=0.0
                )
            
            payment_count = len(completed_payments)
            
            # If only one payment, return basic data
            if payment_count == 1:
                return ConsistencyData(
                    payment_count=payment_count,
                    average_gap_days=0.0,
                    max_gap_days=0,
                    regularity_score=1.0  # Single payment is perfectly regular
                )
            
            # Sort payments by date
            sorted_payments = sorted(completed_payments, key=lambda p: p.payment_date)
            
            # Calculate gaps between consecutive payments
            gaps = []
            for i in range(1, len(sorted_payments)):
                gap = (sorted_payments[i].payment_date - sorted_payments[i-1].payment_date).days
                gaps.append(gap)
            
            average_gap_days = sum(gaps) / len(gaps) if gaps else 0.0
            max_gap_days = max(gaps) if gaps else 0
            
            # Calculate regularity score (0-1) based on standard deviation
            # Lower standard deviation = more regular = higher score
            regularity_score = 0.0
            if len(gaps) > 1:
                try:
                    gap_stdev = stdev(gaps)
                    # Normalize: if stdev is 0, score is 1.0; as stdev increases, score decreases
                    # Using exponential decay: score = e^(-stdev/average_gap)
                    if average_gap_days > 0:
                        regularity_score = max(0.0, min(1.0, 1.0 / (1.0 + gap_stdev / average_gap_days)))
                    else:
                        regularity_score = 1.0
                except:
                    # If stdev calculation fails (e.g., all gaps are the same), perfect regularity
                    regularity_score = 1.0
            elif len(gaps) == 1:
                # Only two payments, consider it regular
                regularity_score = 1.0
            
            return ConsistencyData(
                payment_count=payment_count,
                average_gap_days=average_gap_days,
                max_gap_days=max_gap_days,
                regularity_score=regularity_score
            )
        except Exception as e:
            # Log error and return empty structure
            return ConsistencyData(
                payment_count=0,
                average_gap_days=0.0,
                max_gap_days=0,
                regularity_score=0.0
            )

    def get_fine_data(self, user_id: UUID) -> FineData:
        """
        Retrieve and aggregate fine history data for a user.
        
        Calculates metrics including total fines, unpaid fines, total fine amount,
        unpaid fine amount, and unpaid rate.
        
        Handles missing/incomplete data gracefully by returning empty
        structures with zero values.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            FineData: Aggregated fine metrics
            
        Requirements: 2.4, 2.5
        """
        try:
            fines = self.fine_repository.get_by_user(user_id)
            
            # Handle case where user has no fines
            if not fines:
                return FineData(
                    total_fines=0,
                    unpaid_fines=0,
                    total_fine_amount=0.0,
                    unpaid_fine_amount=0.0,
                    unpaid_rate=0.0
                )
            
            # Calculate fine metrics
            total_fines = len(fines)
            unpaid_fines = sum(1 for f in fines if f.status == FineStatus.unpaid)
            total_fine_amount = sum(float(f.amount) for f in fines)
            unpaid_fine_amount = sum(float(f.amount) for f in fines if f.status == FineStatus.unpaid)
            unpaid_rate = unpaid_fines / total_fines if total_fines > 0 else 0.0
            
            return FineData(
                total_fines=total_fines,
                unpaid_fines=unpaid_fines,
                total_fine_amount=total_fine_amount,
                unpaid_fine_amount=unpaid_fine_amount,
                unpaid_rate=unpaid_rate
            )
        except Exception as e:
            # Log error and return empty structure
            return FineData(
                total_fines=0,
                unpaid_fines=0,
                total_fine_amount=0.0,
                unpaid_fine_amount=0.0,
                unpaid_rate=0.0
            )
