"""
Individual Client Factor Calculator
Replaces aggregated factors with client-specific analysis
"""
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.repositories.mpesa_statement_repository import MpesaStatementRepository
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.fine_repository import FineRepository
from app.services.mpesa_statement_parser import MpesaStatementParser

logger = logging.getLogger(__name__)

class IndividualFactorCalculator:
    """
    Calculates credit score factors based on individual client data only
    Replaces aggregated data approach with client-specific analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mpesa_repo = MpesaStatementRepository(db)
        self.repayment_repo = RepaymentRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.fine_repo = FineRepository(db)
        self.parser = MpesaStatementParser()
    
    def calculate_all_factors(self, credit_subject_id: uuid.UUID) -> Dict[str, float]:
        """
        Calculate all credit score factors for a specific client
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Dictionary containing all factor scores
        """
        try:
            factors = {
                'repayment_factor': self.calculate_repayment_factor(credit_subject_id),
                'mpesa_factor': self.calculate_mpesa_factor(credit_subject_id),
                'consistency_factor': self.calculate_consistency_factor(credit_subject_id),
                'fine_factor': self.calculate_fine_factor(credit_subject_id)
            }
            
            logger.info(f"Calculated factors for client {credit_subject_id}: {factors}")
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating factors for client {credit_subject_id}: {str(e)}")
            # Return default factors on error
            return {
                'repayment_factor': 50.0,
                'mpesa_factor': 50.0,
                'consistency_factor': 50.0,
                'fine_factor': 50.0
            }
    
    def calculate_repayment_factor(self, credit_subject_id: uuid.UUID) -> float:
        """
        Calculate repayment factor based on individual client's repayment history
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Repayment factor score (0-100)
        """
        try:
            # Get client's repayment history
            repayments = self.repayment_repo.get_by_credit_subject_id(str(credit_subject_id))
            
            if not repayments:
                logger.warning(f"No repayment history found for client {credit_subject_id}")
                return 50.0  # Neutral score
            
            # Calculate individual repayment metrics
            total_repayments = len(repayments)
            on_time_repayments = 0
            total_amount = 0.0
            paid_amount = 0.0
            
            for repayment in repayments:
                total_amount += repayment.amount
                if repayment.status.value == 'PAID':
                    paid_amount += repayment.amount
                    # Check if paid on time (within 5 days of due date)
                    if repayment.paid_date:
                        days_late = (repayment.paid_date - repayment.due_date).days
                        if days_late <= 5:
                            on_time_repayments += 1
            
            # Calculate repayment rate
            repayment_rate = (paid_amount / total_amount * 100) if total_amount > 0 else 0
            on_time_rate = (on_time_repayments / total_repayments * 100) if total_repayments > 0 else 0
            
            # Calculate factor score
            factor_score = (repayment_rate * 0.6) + (on_time_rate * 0.4)
            
            # Ensure score is within 0-100 range
            factor_score = max(0, min(100, factor_score))
            
            logger.info(f"Repayment factor for client {credit_subject_id}: {factor_score}")
            return factor_score
            
        except Exception as e:
            logger.error(f"Error calculating repayment factor: {str(e)}")
            return 50.0
    
    def calculate_mpesa_factor(self, credit_subject_id: uuid.UUID) -> float:
        """
        Calculate MPESA factor based on individual client's transaction behavior
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            MPESA factor score (0-100)
        """
        try:
            # Get client's transactions from their latest statement
            transactions = self.mpesa_repo.get_client_transactions(credit_subject_id)
            
            if not transactions:
                logger.warning(f"No MPESA transactions found for client {credit_subject_id}")
                return 50.0  # Neutral score
            
            # Analyze individual transaction behavior
            behavior_analysis = self.parser.analyze_client_behavior(transactions)
            
            # Calculate factor based on individual behavior patterns
            factor_score = 50.0  # Base score
            
            # Transaction frequency (moderate frequency is good)
            frequency = behavior_analysis.get('transaction_frequency', 0)
            if 1 <= frequency <= 10:  # 1-10 transactions per day is good
                factor_score += 10
            elif frequency > 10:  # Too many transactions might be risky
                factor_score -= 5
            
            # Transaction diversity (more diverse recipients is good)
            diversity = behavior_analysis.get('transaction_diversity', 0)
            if diversity >= 5:
                factor_score += 10
            elif diversity >= 3:
                factor_score += 5
            
            # Business hours ratio (transactions during business hours is good)
            business_hours_ratio = behavior_analysis.get('business_hours_ratio', 0)
            factor_score += business_hours_ratio * 10
            
            # Risk indicators (subtract points for each risk indicator)
            risk_indicators = behavior_analysis.get('risk_indicators', [])
            factor_score -= len(risk_indicators) * 5
            
            # Balance analysis (having some paid-in transactions is good)
            paid_in_count = behavior_analysis.get('paid_in_count', 0)
            total_transactions = behavior_analysis.get('total_transactions', 1)
            paid_in_ratio = paid_in_count / total_transactions
            factor_score += paid_in_ratio * 10
            
            # Ensure score is within 0-100 range
            factor_score = max(0, min(100, factor_score))
            
            logger.info(f"MPESA factor for client {credit_subject_id}: {factor_score}")
            return factor_score
            
        except Exception as e:
            logger.error(f"Error calculating MPESA factor: {str(e)}")
            return 50.0
    
    def calculate_consistency_factor(self, credit_subject_id: uuid.UUID) -> float:
        """
        Calculate consistency factor based on individual client's payment patterns
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Consistency factor score (0-100)
        """
        try:
            # Get client's payment history
            payments = self.payment_repo.get_by_credit_subject_id(str(credit_subject_id))
            
            if not payments:
                logger.warning(f"No payment history found for client {credit_subject_id}")
                return 50.0  # Neutral score
            
            # Calculate individual consistency metrics
            total_payments = len(payments)
            regular_payments = 0
            
            # Group payments by month to check regularity
            monthly_amounts = {}
            for payment in payments:
                month_key = payment.payment_date.strftime('%Y-%m')
                if month_key not in monthly_amounts:
                    monthly_amounts[month_key] = []
                monthly_amounts[month_key].append(payment.amount)
            
            # Check for consistent payment amounts
            amount_variance = 0
            if len(monthly_amounts) > 1:
                monthly_totals = [sum(amounts) for amounts in monthly_amounts.values()]
                avg_monthly = sum(monthly_totals) / len(monthly_totals)
                variance = sum((total - avg_monthly) ** 2 for total in monthly_totals) / len(monthly_totals)
                amount_variance = variance ** 0.5  # Standard deviation
            
            # Calculate consistency score
            base_score = 50.0
            
            # Regular monthly payments
            if len(monthly_amounts) >= 3:  # At least 3 months of history
                base_score += 20
            
            # Low variance in payment amounts
            if amount_variance < 1000:  # Low variance
                base_score += 15
            elif amount_variance < 5000:  # Moderate variance
                base_score += 10
            
            # Recent payments (last 30 days)
            recent_date = datetime.now() - timedelta(days=30)
            recent_payments = [p for p in payments if p.payment_date >= recent_date]
            if recent_payments:
                base_score += 15
            
            # Ensure score is within 0-100 range
            factor_score = max(0, min(100, base_score))
            
            logger.info(f"Consistency factor for client {credit_subject_id}: {factor_score}")
            return factor_score
            
        except Exception as e:
            logger.error(f"Error calculating consistency factor: {str(e)}")
            return 50.0
    
    def calculate_fine_factor(self, credit_subject_id: uuid.UUID) -> float:
        """
        Calculate fine factor based on individual client's fine history
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Fine factor score (0-100)
        """
        try:
            # Get client's fine history
            fines = self.fine_repo.get_by_credit_subject_id(str(credit_subject_id))
            
            if not fines:
                logger.info(f"No fines found for client {credit_subject_id} - good sign")
                return 100.0  # Perfect score
            
            # Calculate individual fine metrics
            total_fines = len(fines)
            paid_fines = 0
            total_fine_amount = 0.0
            paid_fine_amount = 0.0
            
            for fine in fines:
                total_fine_amount += fine.amount
                if fine.status.value == 'PAID':
                    paid_fines += 1
                    paid_fine_amount += fine.amount
            
            # Calculate fine payment rate
            payment_rate = (paid_fines / total_fines * 100) if total_fines > 0 else 0
            amount_payment_rate = (paid_fine_amount / total_fine_amount * 100) if total_fine_amount > 0 else 0
            
            # Calculate factor score (fewer fines is better)
            base_score = 100.0
            
            # Penalize for having fines
            if total_fines > 0:
                base_score -= total_fines * 10
            
            # Reward for paying fines
            base_score += (payment_rate * 0.3) + (amount_payment_rate * 0.2)
            
            # Ensure score is within 0-100 range
            factor_score = max(0, min(100, base_score))
            
            logger.info(f"Fine factor for client {credit_subject_id}: {factor_score}")
            return factor_score
            
        except Exception as e:
            logger.error(f"Error calculating fine factor: {str(e)}")
            return 50.0
    
    def get_client_factor_details(self, credit_subject_id: uuid.UUID) -> Dict:
        """
        Get detailed breakdown of all factors for a client
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Dictionary with detailed factor breakdown
        """
        try:
            factors = self.calculate_all_factors(credit_subject_id)
            
            # Get additional details for each factor
            details = {
                'credit_subject_id': str(credit_subject_id),
                'factors': factors,
                'factor_details': {
                    'repayment': self._get_repayment_details(credit_subject_id),
                    'mpesa': self._get_mpesa_details(credit_subject_id),
                    'consistency': self._get_consistency_details(credit_subject_id),
                    'fine': self._get_fine_details(credit_subject_id)
                },
                'calculated_at': datetime.now().isoformat()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting factor details: {str(e)}")
            return {}
    
    def _get_repayment_details(self, credit_subject_id: uuid.UUID) -> Dict:
        """Get detailed repayment information"""
        try:
            repayments = self.repayment_repo.get_by_credit_subject_id(credit_subject_id)
            if not repayments:
                return {'status': 'No repayment history'}
            
            total_amount = sum(r.amount for r in repayments)
            paid_amount = sum(r.amount for r in repayments if r.status.value == 'PAID')
            
            return {
                'total_repayments': len(repayments),
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting repayment details: {str(e)}")
            return {'error': 'Failed to get repayment details'}
    
    def _get_mpesa_details(self, credit_subject_id: uuid.UUID) -> Dict:
        """Get detailed MPESA transaction information"""
        try:
            transactions = self.mpesa_repo.get_client_transactions(credit_subject_id)
            if not transactions:
                return {'status': 'No MPESA statement uploaded'}
            
            summary = self.mpesa_repo.get_client_transaction_summary(credit_subject_id)
            behavior = self.parser.analyze_client_behavior(transactions)
            
            return {
                'statement_summary': summary,
                'behavior_analysis': behavior
            }
        except Exception as e:
            logger.error(f"Error getting MPESA details: {str(e)}")
            return {'error': 'Failed to get MPESA details'}
    
    def _get_consistency_details(self, credit_subject_id: uuid.UUID) -> Dict:
        """Get detailed consistency information"""
        try:
            payments = self.payment_repo.get_by_credit_subject_id(credit_subject_id)
            if not payments:
                return {'status': 'No payment history'}
            
            return {
                'total_payments': len(payments),
                'payment_frequency': len(payments),
                'latest_payment': max(p.payment_date for p in payments).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting consistency details: {str(e)}")
            return {'error': 'Failed to get consistency details'}
    
    def _get_fine_details(self, credit_subject_id: uuid.UUID) -> Dict:
        """Get detailed fine information"""
        try:
            fines = self.fine_repo.get_by_credit_subject_id(credit_subject_id)
            if not fines:
                return {'status': 'No fines - excellent'}
            
            total_amount = sum(f.amount for f in fines)
            paid_amount = sum(f.amount for f in fines if f.status.value == 'PAID')
            
            return {
                'total_fines': len(fines),
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting fine details: {str(e)}")
            return {'error': 'Failed to get fine details'}
