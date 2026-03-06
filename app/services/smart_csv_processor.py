"""
Smart CSV Data Processor
Handles flexible CSV structures and ensures data integrity for client-centric credit scoring system.
"""

import csv
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.credit_subject import CreditSubject
from app.models.repayment import Repayment, RepaymentStatus
from app.models.mpesa_transaction import MpesaTransaction
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.fine import Fine, FineStatus


class SmartCSVProcessor:
    """Intelligent CSV processor that handles various column mappings and ensures data integrity."""
    
    # Flexible column mappings for different CSV structures
    COLUMN_MAPPINGS = {
        'credit_subjects': {
            # ID field variations
            'id': ['id', 'uuid', 'client_id', 'subject_id', 'customer_id', 'user_id'],
            'full_name': ['full_name', 'name', 'fullname', 'client_name', 'customer_name', 'subject_name'],
            'national_id': ['national_id', 'national_id_number', 'id_number', 'nid', 'nationalid'],
            'phone_number': ['phone_number', 'phone', 'mobile', 'telephone', 'contact', 'phone_no'],
            'email': ['email', 'email_address', 'email_addr', 'mail', 'email_address'],
            'external_id': ['external_id', 'external_reference', 'ref_id', 'reference_id', 'ext_id']
        },
        'repayments': {
            'id': ['id', 'uuid', 'repayment_id', 'payment_id', 'transaction_id'],
            'credit_subject_id': ['credit_subject_id', 'client_id', 'customer_id', 'user_id', 'subject_id'],
            'amount': ['amount', 'payment_amount', 'loan_amount', 'principal', 'value'],
            'loan_reference': ['loan_reference', 'loan_ref', 'reference', 'loan_number', 'ref'],
            'due_date': ['due_date', 'payment_due', 'due', 'maturity_date', 'payment_due_date'],
            'status': ['status', 'payment_status', 'repayment_status', 'state'],
            'payment_date': ['payment_date', 'paid_date', 'settlement_date', 'date_paid'],
            'days_overdue': ['days_overdue', 'overdue_days', 'days_late', 'late_days']
        },
        'mpesa_transactions': {
            'id': ['id', 'uuid', 'transaction_id', 'mpesa_id', 'tx_id'],
            'credit_subject_id': ['credit_subject_id', 'client_id', 'customer_id', 'user_id', 'subject_id', 'customer'],
            'transaction_type': ['transaction_type', 'type', 'tx_type', 'payment_type'],
            'amount': ['amount', 'transaction_amount', 'value', 'sum'],
            'reference': ['reference', 'ref', 'reference_number', 'tx_reference', 'receipt'],
            'transaction_date': ['transaction_date', 'date', 'tx_date', 'payment_date', 'timestamp']
        },
        'payments': {
            'id': ['id', 'uuid', 'payment_id', 'transaction_id'],
            'credit_subject_id': ['credit_subject_id', 'client_id', 'customer_id', 'user_id', 'subject_id'],
            'amount': ['amount', 'payment_amount', 'value', 'sum'],
            'payment_type': ['payment_type', 'type', 'category', 'payment_category'],
            'status': ['status', 'payment_status', 'state'],
            'payment_date': ['payment_date', 'date', 'paid_date', 'transaction_date']
        },
        'fines': {
            'id': ['id', 'uuid', 'fine_id', 'penalty_id'],
            'credit_subject_id': ['credit_subject_id', 'client_id', 'customer_id', 'user_id', 'subject_id'],
            'amount': ['amount', 'fine_amount', 'penalty_amount', 'value'],
            'reason': ['reason', 'description', 'fine_reason', 'penalty_reason', 'details'],
            'status': ['status', 'fine_status', 'payment_status', 'state'],
            'assessed_date': ['assessed_date', 'issue_date', 'fine_date', 'date_issued'],
            'paid_date': ['paid_date', 'settlement_date', 'date_paid']
        }
    }
    
    # Data type patterns for validation
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\+?[\d\s\-\(\)]{10,}$',
        'national_id': r'^[\d\-A-Za-z]{5,20}$',
        'amount': r'^\d{1,10}(\.\d{1,4})?$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.errors = []
        self.warnings = []
    
    def detect_csv_type(self, headers: List[str]) -> Optional[str]:
        """Auto-detect CSV type based on column headers."""
        header_set = set(h.lower().strip() for h in headers)
        
        for csv_type, mappings in self.COLUMN_MAPPINGS.items():
            # Count matching columns
            matches = 0
            total_required = len(mappings)
            
            for field, possible_names in mappings.items():
                if any(name.lower() in header_set for name in possible_names):
                    matches += 1
            
            # If we match at least 60% of columns, consider it a match
            if matches / total_required >= 0.6:
                return csv_type
        
        return None
    
    def map_columns(self, headers: List[str], csv_type: str) -> Dict[str, str]:
        """Map CSV columns to database field names."""
        mapping = {}
        header_map = {h.lower().strip(): h for h in headers}
        
        for field, possible_names in self.COLUMN_MAPPINGS[csv_type].items():
            for name in possible_names:
                if name.lower() in header_map:
                    mapping[field] = header_map[name.lower()]
                    break
        
        return mapping
    
    def validate_and_parse_row(self, row: Dict[str, str], csv_type: str, column_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Validate and parse a single row of data."""
        try:
            parsed = {}
            
            for field, csv_column in column_mapping.items():
                raw_value = row.get(csv_column, '').strip()
                
                if not raw_value:
                    if field in ['id', 'credit_subject_id', 'full_name', 'amount']:
                        self.errors.append(f"Missing required field: {field}")
                        return None
                    continue
                
                # Parse based on field type
                if field == 'id' or field == 'credit_subject_id':
                    parsed[field] = self._parse_uuid(raw_value)
                elif field == 'amount':
                    parsed[field] = self._parse_amount(raw_value)
                elif field in ['due_date', 'payment_date', 'transaction_date', 'assessed_date', 'paid_date']:
                    parsed[field] = self._parse_date(raw_value)
                elif field in ['days_overdue']:
                    parsed[field] = self._parse_integer(raw_value)
                elif field == 'email':
                    parsed[field] = self._validate_email(raw_value)
                elif field == 'phone_number':
                    parsed[field] = self._validate_phone(raw_value)
                elif field == 'national_id':
                    parsed[field] = self._validate_national_id(raw_value)
                elif field == 'status':
                    parsed[field] = self._normalize_status(raw_value, csv_type)
                elif field == 'payment_type':
                    parsed[field] = self._normalize_payment_type(raw_value)
                elif field == 'transaction_type':
                    parsed[field] = self._normalize_transaction_type(raw_value)
                else:
                    parsed[field] = raw_value
            
            return parsed
            
        except Exception as e:
            self.errors.append(f"Error parsing row: {str(e)}")
            return None
    
    def _parse_uuid(self, value: str) -> UUID:
        """Parse UUID with validation and smart conversion."""
        value = value.strip()
        
        # Check if it's already a valid UUID
        if re.match(self.PATTERNS['uuid'], value, re.IGNORECASE):
            return UUID(value)
        
        # Try to generate UUID for simple strings/numbers
        if value.isdigit():
            # Convert number to UUID format
            num_str = str(int(value)).zfill(32)
            uuid_str = f"{num_str[:8]}-{num_str[8:12]}-{num_str[12:16]}-{num_str[16:20]}-{num_str[20:]}"
            return UUID(uuid_str)
        elif value.startswith('c') and value[1:].isdigit():
            # Handle c1001 format
            num_str = str(int(value[1:])).zfill(32)
            uuid_str = f"{num_str[:8]}-{num_str[8:12]}-{num_str[12:16]}-{num_str[16:20]}-{num_str[20:]}"
            return UUID(uuid_str)
        elif '-' in value and len(value) < 20:
            # Handle simple IDs like 1001-uuid-001
            # Extract numeric part and convert to UUID
            parts = value.split('-')
            for part in parts:
                if part.isdigit():
                    num_str = str(int(part)).zfill(32)
                    uuid_str = f"{num_str[:8]}-{num_str[8:12]}-{num_str[12:16]}-{num_str[16:20]}-{num_str[20:]}"
                    return UUID(uuid_str)
        
        # If all else fails, generate a UUID from the string hash
        import hashlib
        hash_str = hashlib.md5(value.encode()).hexdigest()
        uuid_str = f"{hash_str[:8]}-{hash_str[8:12]}-{hash_str[12:16]}-{hash_str[16:20]}-{hash_str[20:]}"
        return UUID(uuid_str)
    
    def _parse_amount(self, value: str) -> Decimal:
        """Parse amount with various formats."""
        # Remove currency symbols, commas, and whitespace
        clean_value = re.sub(r'[^\d.]', '', str(value))
        
        if not clean_value:
            return Decimal('0')
        
        try:
            return Decimal(clean_value)
        except:
            raise ValueError(f"Invalid amount format: {value}")
    
    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse date with various formats."""
        if not value or value.lower() in ['', 'null', 'none', 'n/a']:
            return None
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%m/%d/%Y',
            '%m-%d-%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        # If all formats fail, raise error
        raise ValueError(f"Invalid date format: {value}")
    
    def _parse_integer(self, value: str) -> int:
        """Parse integer value."""
        clean_value = re.sub(r'[^\d-]', '', str(value))
        return int(clean_value) if clean_value else 0
    
    def _validate_email(self, value: str) -> str:
        """Validate email format."""
        value = value.strip().lower()
        if not re.match(self.PATTERNS['email'], value):
            self.warnings.append(f"Invalid email format: {value}")
        return value
    
    def _validate_phone(self, value: str) -> str:
        """Validate and normalize phone number."""
        value = re.sub(r'[^\d\+]', '', str(value))
        
        # Ensure it starts with + for international numbers
        if not value.startswith('+') and len(value) >= 10:
            if len(value) == 10:  # Assume Kenyan number
                value = '+254' + value[1:]
            else:
                value = '+' + value
        
        if not re.match(self.PATTERNS['phone'], value):
            self.warnings.append(f"Invalid phone format: {value}")
        
        return value
    
    def _validate_national_id(self, value: str) -> str:
        """Validate national ID format."""
        value = str(value).strip()
        if not re.match(self.PATTERNS['national_id'], value):
            self.warnings.append(f"Invalid national ID format: {value}")
        return value
    
    def _normalize_status(self, value: str, csv_type: str) -> str:
        """Normalize status values."""
        value = str(value).strip().lower()
        
        if csv_type == 'repayments':
            if value in ['on_time', 'ontime', 'paid', 'complete']:
                return 'on_time'
            else:
                return 'late'
        elif csv_type == 'payments':
            if value in ['paid', 'complete', 'settled']:
                return 'paid'
            elif value in ['pending', 'waiting']:
                return 'pending'
            else:
                return 'failed'
        elif csv_type == 'fines':
            if value in ['paid', 'settled', 'cleared']:
                return 'paid'
            elif value in ['unpaid', 'outstanding', 'due']:
                return 'unpaid'
            else:
                return 'partial'
        
        return value
    
    def _normalize_payment_type(self, value: str) -> str:
        """Normalize payment type."""
        value = str(value).strip().lower()
        
        type_mapping = {
            'loan_payment': 'repayment',
            'loan': 'repayment',
            'repayment': 'repayment',
            'fine_payment': 'fine',
            'fine': 'fine',
            'penalty': 'fine',
            'service_payment': 'other',
            'service': 'other',
            'other': 'other'
        }
        
        return type_mapping.get(value, 'other')
    
    def _normalize_transaction_type(self, value: str) -> str:
        """Normalize M-Pesa transaction type."""
        value = str(value).strip().lower()
        
        if value in ['deposit', 'credit', 'inbound', 'received']:
            return 'incoming'
        elif value in ['withdrawal', 'debit', 'outbound', 'sent']:
            return 'outgoing'
        else:
            return 'other'
    
    def validate_client_uniqueness(self, clients: List[Dict[str, Any]]) -> List[str]:
        """Validate client uniqueness constraints."""
        errors = []
        
        # Check database for existing records
        national_ids = [c['national_id'] for c in clients if c.get('national_id')]
        phones = [c['phone_number'] for c in clients if c.get('phone_number')]
        emails = [c['email'] for c in clients if c.get('email')]
        
        if national_ids:
            existing = self.db.execute(
                select(CreditSubject.national_id).where(
                    CreditSubject.national_id.in_(national_ids)
                )
            ).scalars().all()
            duplicates = set(national_ids) & set(existing)
            if duplicates:
                errors.append(f"Duplicate national IDs: {list(duplicates)}")
        
        if phones:
            existing = self.db.execute(
                select(CreditSubject.phone_number).where(
                    CreditSubject.phone_number.in_(phones)
                )
            ).scalars().all()
            duplicates = set(phones) & set(existing)
            if duplicates:
                errors.append(f"Duplicate phone numbers: {list(duplicates)}")
        
        if emails:
            existing = self.db.execute(
                select(CreditSubject.email).where(
                    CreditSubject.email.in_(emails)
                )
            ).scalars().all()
            duplicates = set(emails) & set(existing)
            if duplicates:
                errors.append(f"Duplicate emails: {list(duplicates)}")
        
        return errors
    
    def validate_financial_data_references(self, financial_data: List[Dict[str, Any]]) -> List[str]:
        """Validate that financial data references existing clients."""
        subject_ids = {d['credit_subject_id'] for d in financial_data if d.get('credit_subject_id')}
        
        if not subject_ids:
            return ["No valid credit_subject_id found in financial data"]
        
        existing = self.db.execute(
            select(CreditSubject.id).where(CreditSubject.id.in_(subject_ids))
        ).scalars().all()
        
        missing = subject_ids - set(existing)
        if missing:
            return [f"Financial data references non-existent clients: {list(missing)[:10]}..."]
        
        return []
    
    def process_csv(self, content: bytes, csv_type: Optional[str] = None) -> Dict[str, Any]:
        """Main CSV processing method."""
        try:
            # Parse CSV
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            headers = csv_reader.fieldnames or []
            rows = list(csv_reader)
            
            if not rows:
                raise ValueError("CSV file contains no data rows")
            
            # Auto-detect CSV type if not provided
            if not csv_type:
                csv_type = self.detect_csv_type(headers)
                if not csv_type:
                    raise ValueError("Could not auto-detect CSV type. Please specify manually.")
            
            # Map columns
            column_mapping = self.map_columns(headers, csv_type)
            missing_fields = set(self.COLUMN_MAPPINGS[csv_type].keys()) - set(column_mapping.keys())
            
            if missing_fields:
                self.warnings.append(f"Missing optional fields: {list(missing_fields)}")
            
            # Parse and validate rows
            parsed_rows = []
            for i, row in enumerate(rows):
                parsed = self.validate_and_parse_row(row, csv_type, column_mapping)
                if parsed:
                    parsed_rows.append(parsed)
            
            # Additional validations based on type
            if csv_type == 'credit_subjects':
                client_errors = self.validate_client_uniqueness(parsed_rows)
                self.errors.extend(client_errors)
            else:
                ref_errors = self.validate_financial_data_references(parsed_rows)
                self.errors.extend(ref_errors)
            
            return {
                'csv_type': csv_type,
                'headers': headers,
                'column_mapping': column_mapping,
                'parsed_rows': parsed_rows,
                'errors': self.errors,
                'warnings': self.warnings,
                'stats': {
                    'total_rows': len(rows),
                    'parsed_rows': len(parsed_rows),
                    'error_count': len(self.errors),
                    'warning_count': len(self.warnings)
                }
            }
            
        except Exception as e:
            self.errors.append(f"CSV processing failed: {str(e)}")
            return {
                'errors': self.errors,
                'warnings': self.warnings
            }
