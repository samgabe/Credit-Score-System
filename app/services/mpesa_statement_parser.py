"""
M-Pesa Statement Parser for Individual Client Analysis
Extracts and analyzes client-specific M-Pesa transactions from statements
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MpesaTransaction:
    """Individual M-Pesa transaction extracted from statement"""
    id: uuid.UUID
    receipt_no: str
    completion_time: datetime
    transaction_type: str
    details: str
    recipient: Optional[str]
    amount: float
    status: str
    is_paid_in: bool
    is_paid_out: bool

@dataclass
class MpesaStatementSummary:
    """Summary of M-Pesa statement"""
    customer_name: str
    mobile_number: str
    statement_date: datetime
    statement_period: str
    total_paid_in: float
    total_paid_out: float
    transaction_types: Dict[str, Dict[str, float]]

class MpesaStatementParser:
    """Parser for individual client M-Pesa statements"""
    
    def __init__(self):
        self.transaction_patterns = {
            'Customer Transfer': r'Customer Transfer to (\d+\*\*\*\d+) (.+)',
            'Customer Payment': r'Customer Payment to (.+?) (\d+\*\*\*\d+|[\d\*]+) - (.+)',
            'Customer Bundle': r'Customer Bundle Purchase to (\d+) (.+)',
            'Customer Airtime': r'Customer Airtime Purchase',
            'Transfer of Funds Charge': r'Transfer of Funds Charge',
            'Pay Bill': r'Customer Payment to Small Business'
        }
    
    def parse_statement_text(self, text: str) -> Tuple[MpesaStatementSummary, List[MpesaTransaction]]:
        """
        Parse M-Pesa statement text and extract summary and transactions
        
        Args:
            text: Extracted text from M-Pesa statement PDF
            
        Returns:
            Tuple of (statement_summary, transactions_list)
        """
        try:
            # Extract summary information
            summary = self._extract_summary(text)
            
            # Extract transactions
            transactions = self._extract_transactions(text)
            
            logger.info(f"Parsed {len(transactions)} transactions from statement")
            return summary, transactions
            
        except Exception as e:
            logger.error(f"Error parsing M-Pesa statement: {str(e)}")
            raise ValueError(f"Failed to parse statement: {str(e)}")
    
    def _extract_summary(self, text: str) -> MpesaStatementSummary:
        """Extract summary information from statement text"""
        lines = text.split('\n')
        
        customer_name = ""
        mobile_number = ""
        statement_date = None
        statement_period = ""
        total_paid_in = 0.0
        total_paid_out = 0.0
        transaction_types = {}
        
        for i, line in enumerate(lines):
            # Customer information - handle the actual PDF format
            if line.strip() == "Customer Name:":
                # The actual name is 5 lines after "Customer Name:" (line 8)
                if i+5 < len(lines):
                    customer_name = lines[i+5].strip()
            elif line.strip() == "Mobile Number:":
                # The actual number is 5 lines after "Mobile Number:" (line 9)
                if i+5 < len(lines):
                    mobile_number = lines[i+5].strip()
            elif line.strip() == "Date of Statement:":
                # The actual date is 5 lines after "Date of Statement:" (line 10)
                if i+5 < len(lines):
                    date_str = lines[i+5].strip()
                    statement_date = self._parse_date(date_str)
            elif line.strip() == "Statement Period:":
                # The actual period is 5 lines after "Statement Period:" (line 11)
                if i+5 < len(lines):
                    statement_period = lines[i+5].strip()
            
            # Transaction summary - handle the actual PDF format
            elif line.strip() == "TOTAL:":
                # Look for PAID IN and PAID OUT values
                for j in range(i, min(i+20, len(lines))):
                    if lines[j].strip() == "PAID IN":
                        # PAID IN values are on the next lines
                        paid_in_values = []
                        for k in range(j+1, min(j+10, len(lines))):
                            line_content = lines[k].strip()
                            if line_content.replace('.', '').replace(',', '').replace(' ', '').isdigit():
                                paid_in_values.append(line_content)
                            elif line_content == "PAID OUT":
                                break
                        # Sum all paid in values
                        total_paid_in = sum(float(val.replace(',', '')) for val in paid_in_values)
                    
                    elif lines[j].strip() == "PAID OUT":
                        # PAID OUT values are on the next lines
                        paid_out_values = []
                        for k in range(j+1, min(j+10, len(lines))):
                            line_content = lines[k].strip()
                            if line_content.replace('.', '').replace(',', '').replace(' ', '').isdigit():
                                paid_out_values.append(line_content)
                            elif line_content in ["DETAILED STATEMENT", ""] or k >= len(lines)-1:
                                break
                        # Sum all paid out values
                        total_paid_out = sum(float(val.replace(',', '')) for val in paid_out_values)
                        break
        
        return MpesaStatementSummary(
            customer_name=customer_name,
            mobile_number=mobile_number,
            statement_date=statement_date or datetime.now(),
            statement_period=statement_period,
            total_paid_in=total_paid_in,
            total_paid_out=total_paid_out,
            transaction_types=transaction_types
        )
    
    def _extract_transactions(self, text: str) -> List[MpesaTransaction]:
        """Extract individual transactions from statement text"""
        transactions = []
        lines = text.split('\n')
        
        current_receipt = ""
        current_time = None
        current_details = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Receipt number pattern
            receipt_match = re.match(r'^[A-Z0-9]+$', line)
            if receipt_match and len(line) >= 8:
                current_receipt = line
                continue
            
            # Date and time pattern
            time_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+)', line)
            if time_match:
                if current_time and current_details:  # Save previous transaction
                    transaction = self._parse_transaction(current_receipt, current_time, current_details)
                    if transaction:
                        transactions.append(transaction)
                
                current_time = time_match.group(1)
                current_details = time_match.group(2)
                continue
            
            # Continuation of details (multi-line)
            if current_time and line and not line.startswith('Page') and not receipt_match:
                current_details += " " + line.strip()
            
            # Check for amount lines (numbers with decimals)
            if current_time and line.strip():
                amount_match = re.search(r'([\d,]+\.\d{2})', line.strip())
                if amount_match:
                    # Add this amount to the current details
                    current_details += " " + line.strip()
                    continue
            
            # Check for "Withdraw Balance" or "Paid in" lines
            if current_time and ("Withdraw Balance" in line or "Paid in" in line):
                current_details += " " + line.strip()
                continue
            
            # Check for "COMPLETED" line - this usually indicates end of transaction
            if current_time and "COMPLETED" in line:
                current_details += " " + line.strip()
                # Parse the accumulated transaction
                transaction = self._parse_transaction(current_receipt, current_time, current_details)
                if transaction:
                    transactions.append(transaction)
                
                current_time = None  # Reset after processing a transaction
                current_details = ""
        
        # Don't forget the last transaction
        if current_time and current_details:
            transaction = self._parse_transaction(current_receipt, current_time, current_details)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def _extract_amount_from_details(self, details: str) -> float:
        """
        Extract amount from transaction details.
        
        Args:
            details: Transaction details string
            
        Returns:
            Extracted amount as float
        """
        try:
            import re
            
            # Pattern 1: "Withdraw Balance" followed by "n" and then amount on next line
            # Handle the actual PDF format where "n" is on a separate line
            lines = details.split('\n')
            for i, line in enumerate(lines):
                if "Withdraw Balance" in line:
                    # Look for the amount in the next few lines
                    for j in range(i+1, min(i+4, len(lines))):
                        amount_match = re.search(r'([\d,]+\.\d{2})', lines[j])
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            return amount
            
            # Pattern 2: "Paid in" followed by amount
            paid_in_match = re.search(r'Paid in\s+([\d,]+\.\d{2})', details)
            if paid_in_match:
                amount = float(paid_in_match.group(1).replace(',', ''))
                return amount
            
            # Pattern 3: Look for any amount in the details
            all_amounts = re.findall(r'([\d,]+\.\d{2})', details)
            if all_amounts:
                # Return the largest amount (likely the transaction amount)
                amounts_float = [float(a.replace(',', '')) for a in all_amounts]
                return max(amounts_float)
            
            return 0.0
        except Exception as e:
            return 0.0
    
    def _parse_transaction(self, receipt_no: str, time_str: str, details: str) -> Optional[MpesaTransaction]:
        """Parse individual transaction details"""
        try:
            completion_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            # Determine transaction type and extract information
            transaction_type = "Unknown"
            recipient = None
            amount = 0.0
            # Extract amount using the new method
            amount = self._extract_amount_from_details(details)
            
            # Initialize variables
            transaction_type = "Unknown"
            recipient = None
            is_paid_in = False
            is_paid_out = True
            
            # Determine transaction type and direction
            if "Customer Transfer to" in details:
                transaction_type = "Customer Transfer"
                is_paid_out = True
                is_paid_in = False
                recipient_match = re.search(r'Customer Transfer to (\d+\*\*\*\d+) (.+)', details)
                recipient = recipient_match.group(2) if recipient_match else None
            elif "Customer Payment to" in details:
                transaction_type = "Customer Payment"
                is_paid_out = True
                is_paid_in = False
                recipient_match = re.search(r'Customer Payment to (.+?) (\d+\*\*\*\d+|\d+\*+) - (.+)', details)
                if recipient_match:
                    recipient = f"{recipient_match.group(1)} - {recipient_match.group(2)}"
            elif "Customer Bundle Purchase" in details:
                transaction_type = "Bundle Purchase"
                is_paid_out = True
                is_paid_in = False
            elif "Customer Airtime Purchase" in details:
                transaction_type = "Airtime Purchase"
                is_paid_out = True
                is_paid_in = False
            elif "Transfer of Funds Charge" in details:
                transaction_type = "Transaction Fee"
                is_paid_out = True
                is_paid_in = False
            elif "B2C Payment" in details:
                transaction_type = "B2C Payment"
                is_paid_in = True
                is_paid_out = False
            elif "Paid in" in details:
                transaction_type = "Deposit"
                is_paid_in = True
                is_paid_out = False
            elif "Withdraw Balance" in details:
                transaction_type = "Withdrawal"
                is_paid_out = True
                is_paid_in = False
            else:
                transaction_type = "Unknown"
                is_paid_out = True  # Default assumption
                is_paid_in = False
            
            return MpesaTransaction(
                id=uuid.uuid4(),
                receipt_no=receipt_no,
                completion_time=completion_time,
                transaction_type=transaction_type,
                details=details,
                recipient=recipient,
                amount=amount,
                status="COMPLETED",  # Assume completed for now
                is_paid_in=is_paid_in,
                is_paid_out=is_paid_out
            )
            
        except Exception as e:
            logger.error(f"Error parsing transaction: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string"""
        try:
            return datetime.strptime(date_str, '%dth %b %Y')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d %b %Y')
            except ValueError:
                return None
    
    def analyze_client_behavior(self, transactions: List[MpesaTransaction]) -> Dict:
        """
        Analyze individual client's transaction behavior for credit scoring
        
        Args:
            transactions: List of client's transactions
            
        Returns:
            Dictionary containing behavioral analysis
        """
        if not transactions:
            return {
                'transaction_frequency': 0,
                'average_transaction_amount': 0,
                'payment_consistency': 0,
                'transaction_diversity': 0,
                'risk_indicators': []
            }
        
        # Calculate individual metrics
        total_transactions = len(transactions)
        paid_in_transactions = [t for t in transactions if t.is_paid_in]
        paid_out_transactions = [t for t in transactions if t.is_paid_out]
        
        # Transaction frequency (transactions per day)
        if transactions:
            date_range = (max(t.completion_time for t in transactions) - 
                         min(t.completion_time for t in transactions)).days
            frequency = total_transactions / max(date_range, 1)
        else:
            frequency = 0
        
        # Average amounts
        avg_paid_in = sum(t.amount for t in paid_in_transactions) / max(len(paid_in_transactions), 1)
        avg_paid_out = sum(t.amount for t in paid_out_transactions) / max(len(paid_out_transactions), 1)
        
        # Transaction diversity (unique recipients)
        unique_recipients = len(set(t.recipient for t in transactions if t.recipient))
        
        # Time pattern analysis
        business_hours_transactions = [t for t in transactions 
                                     if 9 <= t.completion_time.hour <= 17]
        business_hours_ratio = len(business_hours_transactions) / total_transactions
        
        # Risk indicators
        risk_indicators = []
        
        # High frequency small transactions (potential gambling)
        small_transactions = [t for t in transactions if t.amount < 100]
        if len(small_transactions) / total_transactions > 0.7:
            risk_indicators.append("High frequency small transactions")
        
        # Late night transactions
        late_night_transactions = [t for t in transactions 
                                if t.completion_time.hour >= 22 or t.completion_time.hour <= 5]
        if len(late_night_transactions) / total_transactions > 0.2:
            risk_indicators.append("Late night transaction pattern")
        
        return {
            'transaction_frequency': frequency,
            'average_paid_in': avg_paid_in,
            'average_paid_out': avg_paid_out,
            'transaction_diversity': unique_recipients,
            'business_hours_ratio': business_hours_ratio,
            'risk_indicators': risk_indicators,
            'total_transactions': total_transactions,
            'paid_in_count': len(paid_in_transactions),
            'paid_out_count': len(paid_out_transactions)
        }
