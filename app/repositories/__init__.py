"""
Data Access Layer - Repository Pattern Implementation
Provides abstraction for database operations.
"""
from app.repositories.user_repository import UserRepository
from app.repositories.repayment_repository import RepaymentRepository
from app.repositories.mpesa_transaction_repository import MpesaTransactionRepository
from app.repositories.fine_repository import FineRepository
from app.repositories.credit_score_repository import CreditScoreRepository
from app.repositories.payment_repository import PaymentRepository

__all__ = [
    "UserRepository",
    "RepaymentRepository",
    "MpesaTransactionRepository",
    "FineRepository",
    "CreditScoreRepository",
    "PaymentRepository",
]
