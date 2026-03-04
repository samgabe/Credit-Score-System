"""
CSV Data Loader Service for Credit Score Calculation

This service loads data from CSV files instead of database repositories
to provide factor data for credit score calculations. It implements
the same interface as the FactorDataAggregator but uses CSV files as data source.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import csv
import os
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, date
from statistics import stdev
from app.models.factor_data import (
    RepaymentData,
    MpesaData,
    ConsistencyData,
    FineData
)
from app.models.repayment import RepaymentStatus
from app.models.fine import FineStatus
from app.models.payment import PaymentStatus
from app.models.mpesa_transaction import TransactionType
from app.models.payment import PaymentType


class CSVDataLoader:
    """
    Loads data from CSV files for credit score calculation.
    
    This class implements the same interface as FactorDataAggregator
    but uses CSV files as the data source instead of database repositories.
    
    CSV Files Expected:
    - users.csv: id, fullname, national_id, phone_number, email, created_at, updated_at
    - repayments.csv: id, user_id, amount, loan_reference, due_date, payment_date, status, days_overdue, created_at
    - mpesa_transactions.csv: id, user_id, transaction_type, amount, reference, transaction_date, created_at
    - payments.csv: id, user_id, amount, payment_type, status, payment_date, created_at
    - fines.csv: id, user_id, amount, reason, status, assessed_date, paid_date, created_at
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    def __init__(self, csv_directory: str = "csv_data"):
        """
        Initialize the CSVDataLoader with CSV file directory.
        
        Args:
            csv_directory: Directory containing CSV files
        """
        self.csv_directory = csv_directory
        self._ensure_csv_directory()
    
    def _ensure_csv_directory(self):
        """Ensure CSV directory exists."""
        if not os.path.exists(self.csv_directory):
            os.makedirs(self.csv_directory)
    
    def _load_csv_data(self, filename: str) -> List[Dict]:
        """
        Load data from a CSV file.
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            List[Dict]: List of row data as dictionaries
        """
        file_path = os.path.join(self.csv_directory, filename)
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                return list(reader)
        except Exception as e:
            print(f"Error loading CSV file {filename}: {e}")
            return []
    
    def _parse_uuid(self, uuid_str: str) -> UUID:
        """Parse UUID string to UUID object."""
        try:
            return UUID(uuid_str)
        except:
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _parse_date_only(self, date_str: str) -> date:
        """Parse date string to date object."""
        try:
            return datetime.fromisoformat(date_str).date()
        except:
            return None
    
    def _parse_float(self, value_str: str) -> float:
        """Parse string to float."""
        try:
            return float(value_str)
        except:
            return 0.0
    
    def _parse_int(self, value_str: str) -> int:
        """Parse string to int."""
        try:
            return int(value_str)
        except:
            return 0
    
    def get_repayment_data(self, user_id: UUID) -> RepaymentData:
        """
        Retrieve and aggregate repayment history data for a user from CSV.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            RepaymentData: Aggregated repayment metrics
        """
        try:
            repayments_data = self._load_csv_data("repayments.csv")
            
            # Filter repayments for the specific user
            user_repayments = [
                r for r in repayments_data 
                if self._parse_uuid(r['user_id']) == user_id
            ]
            
            # Handle case where user has no repayments
            if not user_repayments:
                return RepaymentData(
                    total_payments=0,
                    on_time_payments=0,
                    late_payments=0,
                    defaulted_payments=0,
                    on_time_rate=0.0
                )
            
            # Count repayments by status
            on_time_count = sum(1 for r in user_repayments if r['status'] == RepaymentStatus.on_time.value)
            late_count = sum(1 for r in user_repayments if r['status'] == RepaymentStatus.late.value)
            
            # For now, we consider payments more than 30 days overdue as defaulted
            defaulted_count = sum(
                1 for r in user_repayments 
                if r['status'] == RepaymentStatus.late.value and self._parse_int(r['days_overdue']) > 30
            )
            
            total_count = len(user_repayments)
            on_time_rate = on_time_count / total_count if total_count > 0 else 0.0
            
            return RepaymentData(
                total_payments=total_count,
                on_time_payments=on_time_count,
                late_payments=late_count,
                defaulted_payments=defaulted_count,
                on_time_rate=on_time_rate
            )
        except Exception as e:
            print(f"Error retrieving repayment data for user {user_id}: {e}")
            return RepaymentData(
                total_payments=0,
                on_time_payments=0,
                late_payments=0,
                defaulted_payments=0,
                on_time_rate=0.0
            )
    
    def get_mpesa_data(self, user_id: UUID) -> MpesaData:
        """
        Retrieve and aggregate M-Pesa transaction data for a user from CSV.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            MpesaData: Aggregated M-Pesa transaction metrics
        """
        try:
            transactions_data = self._load_csv_data("mpesa_transactions.csv")
            
            # Filter transactions for the specific user
            user_transactions = [
                t for t in transactions_data 
                if self._parse_uuid(t['user_id']) == user_id
            ]
            
            # Handle case where user has no M-Pesa transactions
            if not user_transactions:
                return MpesaData(
                    transaction_count=0,
                    total_volume=0.0,
                    average_transaction=0.0,
                    frequency_days=0.0
                )
            
            # Calculate transaction metrics
            transaction_count = len(user_transactions)
            total_volume = sum(self._parse_float(t['amount']) for t in user_transactions)
            average_transaction = total_volume / transaction_count if transaction_count > 0 else 0.0
            
            # Calculate frequency (average days between transactions)
            frequency_days = 0.0
            if transaction_count > 1:
                # Sort transactions by date
                sorted_transactions = sorted(
                    user_transactions, 
                    key=lambda t: self._parse_date(t['transaction_date']) or datetime.min
                )
                
                # Calculate gaps between consecutive transactions
                gaps = []
                for i in range(1, len(sorted_transactions)):
                    prev_date = self._parse_date(sorted_transactions[i-1]['transaction_date'])
                    curr_date = self._parse_date(sorted_transactions[i]['transaction_date'])
                    if prev_date and curr_date:
                        gap = (curr_date - prev_date).days
                        gaps.append(gap)
                
                frequency_days = sum(gaps) / len(gaps) if gaps else 0.0
            
            return MpesaData(
                transaction_count=transaction_count,
                total_volume=total_volume,
                average_transaction=average_transaction,
                frequency_days=frequency_days
            )
        except Exception as e:
            print(f"Error retrieving M-Pesa data for user {user_id}: {e}")
            return MpesaData(
                transaction_count=0,
                total_volume=0.0,
                average_transaction=0.0,
                frequency_days=0.0
            )
    
    def get_payment_consistency_data(self, user_id: UUID) -> ConsistencyData:
        """
        Retrieve and aggregate payment consistency metrics for a user from CSV.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            ConsistencyData: Aggregated payment consistency metrics
        """
        try:
            payments_data = self._load_csv_data("payments.csv")
            
            # Filter payments for the specific user
            user_payments = [
                p for p in payments_data 
                if self._parse_uuid(p['user_id']) == user_id
            ]
            
            # Filter to only completed payments
            completed_payments = [
                p for p in user_payments 
                if p['status'] == PaymentStatus.completed.value
            ]
            
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
                    regularity_score=1.0
                )
            
            # Sort payments by date
            sorted_payments = sorted(
                completed_payments, 
                key=lambda p: self._parse_date(p['payment_date']) or datetime.min
            )
            
            # Calculate gaps between consecutive payments
            gaps = []
            for i in range(1, len(sorted_payments)):
                prev_date = self._parse_date(sorted_payments[i-1]['payment_date'])
                curr_date = self._parse_date(sorted_payments[i]['payment_date'])
                if prev_date and curr_date:
                    gap = (curr_date - prev_date).days
                    gaps.append(gap)
            
            average_gap_days = sum(gaps) / len(gaps) if gaps else 0.0
            max_gap_days = max(gaps) if gaps else 0
            
            # Calculate regularity score (0-1) based on standard deviation
            regularity_score = 0.0
            if len(gaps) > 1:
                try:
                    gap_stdev = stdev(gaps)
                    if average_gap_days > 0:
                        regularity_score = max(0.0, min(1.0, 1.0 / (1.0 + gap_stdev / average_gap_days)))
                    else:
                        regularity_score = 1.0
                except:
                    regularity_score = 1.0
            elif len(gaps) == 1:
                regularity_score = 1.0
            
            return ConsistencyData(
                payment_count=payment_count,
                average_gap_days=average_gap_days,
                max_gap_days=max_gap_days,
                regularity_score=regularity_score
            )
        except Exception as e:
            print(f"Error retrieving payment consistency data for user {user_id}: {e}")
            return ConsistencyData(
                payment_count=0,
                average_gap_days=0.0,
                max_gap_days=0,
                regularity_score=0.0
            )
    
    def get_fine_data(self, user_id: UUID) -> FineData:
        """
        Retrieve and aggregate fine history data for a user from CSV.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            FineData: Aggregated fine metrics
        """
        try:
            fines_data = self._load_csv_data("fines.csv")
            
            # Filter fines for the specific user
            user_fines = [
                f for f in fines_data 
                if self._parse_uuid(f['user_id']) == user_id
            ]
            
            # Handle case where user has no fines
            if not user_fines:
                return FineData(
                    total_fines=0,
                    unpaid_fines=0,
                    total_fine_amount=0.0,
                    unpaid_fine_amount=0.0,
                    unpaid_rate=0.0
                )
            
            # Calculate fine metrics
            total_fines = len(user_fines)
            unpaid_fines = sum(1 for f in user_fines if f['status'] == FineStatus.unpaid.value)
            total_fine_amount = sum(self._parse_float(f['amount']) for f in user_fines)
            unpaid_fine_amount = sum(
                self._parse_float(f['amount']) 
                for f in user_fines 
                if f['status'] == FineStatus.unpaid.value
            )
            unpaid_rate = unpaid_fines / total_fines if total_fines > 0 else 0.0
            
            return FineData(
                total_fines=total_fines,
                unpaid_fines=unpaid_fines,
                total_fine_amount=total_fine_amount,
                unpaid_fine_amount=unpaid_fine_amount,
                unpaid_rate=unpaid_rate
            )
        except Exception as e:
            print(f"Error retrieving fine data for user {user_id}: {e}")
            return FineData(
                total_fines=0,
                unpaid_fines=0,
                total_fine_amount=0.0,
                unpaid_fine_amount=0.0,
                unpaid_rate=0.0
            )
    
    def get_user_by_id(self, user_id: UUID) -> Optional[Dict]:
        """
        Get user data by ID from CSV.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        users_data = self._load_csv_data("users.csv")
        for user in users_data:
            if self._parse_uuid(user['id']) == user_id:
                return user
        return None
    
    def get_user_by_national_id(self, national_id: int) -> Optional[Dict]:
        """
        Get user data by national ID from CSV.
        
        Args:
            national_id: National ID of the user
            
        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        users_data = self._load_csv_data("users.csv")
        for user in users_data:
            if self._parse_int(user['national_id']) == national_id:
                return user
        return None
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all users from CSV.
        
        Returns:
            List[Dict]: List of all user data
        """
        return self._load_csv_data("users.csv")
