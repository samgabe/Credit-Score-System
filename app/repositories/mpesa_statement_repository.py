"""
Repository for Individual Client M-Pesa Statement Data
Replaces aggregated data with client-specific transaction storage
"""
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.models.mpesa_statement import MpesaStatement
from app.models.mpesa_transaction import MpesaTransaction
from app.services.mpesa_statement_parser import MpesaTransaction as ParsedTransaction
import logging

logger = logging.getLogger(__name__)

class MpesaStatementRepository:
    """Repository for individual client M-Pesa statements and transactions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_statement(self, credit_subject_id: uuid.UUID, customer_name: str, 
                       mobile_number: str, statement_date: datetime, 
                       statement_period: str, file_path: str) -> MpesaStatement:
        """
        Create a new M-Pesa statement record for a specific client
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            customer_name: Name from statement
            mobile_number: Mobile number from statement
            statement_date: Date of statement
            statement_period: Statement period
            file_path: Path to uploaded statement file
            
        Returns:
            Created MpesaStatement record
        """
        try:
            # Deactivate any existing statements for this client
            self._deactivate_existing_statements(credit_subject_id)
            
            statement = MpesaStatement(
                id=uuid.uuid4(),
                credit_subject_id=credit_subject_id,
                customer_name=customer_name,
                mobile_number=mobile_number,
                statement_date=statement_date,
                statement_period=statement_period,
                file_path=file_path,
                upload_date=datetime.now(),
                is_active=True
            )
            
            self.db.add(statement)
            self.db.commit()
            self.db.refresh(statement)
            
            logger.info(f"Created M-Pesa statement for client {credit_subject_id}")
            return statement
            
        except Exception as e:
            logger.error(f"Error creating M-Pesa statement: {str(e)}")
            self.db.rollback()
            raise
    
    def save_transactions(self, statement_id: uuid.UUID, 
                        parsed_transactions: List[ParsedTransaction]) -> List[MpesaTransaction]:
        """
        Save parsed transactions for a specific statement
        
        Args:
            statement_id: ID of the statement
            parsed_transactions: List of parsed transactions
            
        Returns:
            List of saved transaction records
        """
        try:
            transactions = []
            
            for parsed_tx in parsed_transactions:
                transaction = MpesaTransaction(
                    id=parsed_tx.id,
                    statement_id=statement_id,
                    receipt_no=parsed_tx.receipt_no,
                    completion_time=parsed_tx.completion_time,
                    transaction_type=parsed_tx.transaction_type,
                    details=parsed_tx.details,
                    recipient=parsed_tx.recipient,
                    amount=parsed_tx.amount,
                    status=parsed_tx.status,
                    is_paid_in=parsed_tx.is_paid_in,
                    is_paid_out=parsed_tx.is_paid_out
                )
                
                self.db.add(transaction)
                transactions.append(transaction)
            
            self.db.commit()
            
            for tx in transactions:
                self.db.refresh(tx)
            
            logger.info(f"Saved {len(transactions)} transactions for statement {statement_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error saving transactions: {str(e)}")
            self.db.rollback()
            raise
    
    def get_client_transactions(self, credit_subject_id: uuid.UUID, 
                              limit: Optional[int] = None) -> List[MpesaTransaction]:
        """
        Get all transactions for a specific client from their latest statement
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            limit: Optional limit on number of transactions
            
        Returns:
            List of client's transactions
        """
        try:
            # Get the active statement for this client
            active_statement = self.db.query(MpesaStatement).filter(
                and_(
                    MpesaStatement.credit_subject_id == credit_subject_id,
                    MpesaStatement.is_active == True
                )
            ).first()
            
            if not active_statement:
                logger.warning(f"No active statement found for client {credit_subject_id}")
                return []
            
            # Get transactions for the active statement
            query = self.db.query(MpesaTransaction).filter(
                MpesaTransaction.statement_id == active_statement.id
            ).order_by(desc(MpesaTransaction.completion_time))
            
            if limit:
                query = query.limit(limit)
            
            transactions = query.all()
            logger.info(f"Retrieved {len(transactions)} transactions for client {credit_subject_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting client transactions: {str(e)}")
            raise
    
    def get_client_statement(self, credit_subject_id: uuid.UUID) -> Optional[MpesaStatement]:
        """
        Get the active statement for a specific client
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Active MpesaStatement or None
        """
        try:
            statement = self.db.query(MpesaStatement).filter(
                and_(
                    MpesaStatement.credit_subject_id == credit_subject_id,
                    MpesaStatement.is_active == True
                )
            ).first()
            
            return statement
            
        except Exception as e:
            logger.error(f"Error getting client statement: {str(e)}")
            raise
    
    def get_client_transaction_summary(self, credit_subject_id: uuid.UUID) -> dict:
        """
        Get transaction summary for a specific client
        
        Args:
            credit_subject_id: ID of the credit subject (client)
            
        Returns:
            Dictionary with transaction summary
        """
        try:
            transactions = self.get_client_transactions(credit_subject_id)
            
            if not transactions:
                return {
                    'total_transactions': 0,
                    'total_paid_in': 0.0,
                    'total_paid_out': 0.0,
                    'net_amount': 0.0,
                    'transaction_types': {},
                    'unique_recipients': 0
                }
            
            total_paid_in = sum(t.amount for t in transactions if t.is_paid_in)
            total_paid_out = sum(t.amount for t in transactions if t.is_paid_out)
            
            # Transaction types breakdown
            transaction_types = {}
            for tx in transactions:
                tx_type = tx.transaction_type
                if tx_type not in transaction_types:
                    transaction_types[tx_type] = {'count': 0, 'total_amount': 0.0}
                transaction_types[tx_type]['count'] += 1
                transaction_types[tx_type]['total_amount'] += tx.amount
            
            unique_recipients = len(set(t.recipient for t in transactions if t.recipient))
            
            return {
                'total_transactions': len(transactions),
                'total_paid_in': total_paid_in,
                'total_paid_out': total_paid_out,
                'net_amount': total_paid_in - total_paid_out,
                'transaction_types': transaction_types,
                'unique_recipients': unique_recipients,
                'date_range': {
                    'start': min(t.completion_time for t in transactions).isoformat(),
                    'end': max(t.completion_time for t in transactions).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting client transaction summary: {str(e)}")
            raise
    
    def get_all_clients_with_statements(self) -> List[uuid.UUID]:
        """
        Get list of all clients who have statements
        
        Returns:
            List of credit subject IDs with statements
        """
        try:
            statements = self.db.query(MpesaStatement.credit_subject_id).filter(
                MpesaStatement.is_active == True
            ).distinct().all()
            
            return [stmt.credit_subject_id for stmt in statements]
            
        except Exception as e:
            logger.error(f"Error getting clients with statements: {str(e)}")
            raise
    
    def _deactivate_existing_statements(self, credit_subject_id: uuid.UUID):
        """Deactivate existing statements for a client"""
        try:
            self.db.query(MpesaStatement).filter(
                MpesaStatement.credit_subject_id == credit_subject_id
            ).update({'is_active': False})
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error deactivating existing statements: {str(e)}")
            raise
    
    def delete_statement(self, statement_id: uuid.UUID) -> bool:
        """
        Delete a statement and its transactions
        
        Args:
            statement_id: ID of the statement to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            # Delete transactions first
            self.db.query(MpesaTransaction).filter(
                MpesaTransaction.statement_id == statement_id
            ).delete()
            
            # Delete statement
            self.db.query(MpesaStatement).filter(
                MpesaStatement.id == statement_id
            ).delete()
            
            self.db.commit()
            logger.info(f"Deleted statement {statement_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting statement: {str(e)}")
            self.db.rollback()
            return False
    
    def get_all_statements_for_subject(self, credit_subject_id: str) -> List[MpesaStatement]:
        """
        Get all statements for a credit subject.
        
        Args:
            credit_subject_id: ID of the credit subject
            
        Returns:
            List of statements for the subject
        """
        try:
            uuid_id = UUID(credit_subject_id)
            return self.db.query(MpesaStatement).filter(
                MpesaStatement.credit_subject_id == uuid_id
            ).order_by(desc(MpesaStatement.upload_date)).all()
        except (ValueError, AttributeError):
            return []
    
    def get_transactions_for_statement(self, statement_id: str) -> List[MpesaTransaction]:
        """
        Get all transactions for a specific statement.
        
        Args:
            statement_id: ID of the statement
            
        Returns:
            List of transactions for the statement
        """
        try:
            uuid_id = UUID(statement_id)
            return self.db.query(MpesaTransaction).filter(
                MpesaTransaction.statement_id == uuid_id
            ).order_by(desc(MpesaTransaction.completion_time)).all()
        except (ValueError, AttributeError):
            return []
