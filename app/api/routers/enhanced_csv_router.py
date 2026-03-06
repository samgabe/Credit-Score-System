"""
CSV Upload Router for the Credit Score API.
Handles intelligent CSV file processing with flexible column mapping and data validation.
"""

import os
import csv
import shutil
from typing import List, Dict, Optional
from decimal import Decimal
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.schemas.error import ErrorResponse
from app.config import get_settings
from datetime import datetime
from uuid import UUID
from app.models.credit_subject import CreditSubject
from app.models.repayment import Repayment, RepaymentStatus
from app.models.mpesa_transaction import MpesaTransaction
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.fine import Fine, FineStatus
from app.api.routers.system_auth_router import get_current_system_user, require_role
from app.models.system_user import SystemUser
from app.services.smart_csv_processor import SmartCSVProcessor

router = APIRouter(tags=["smart-csv"])

# Enhanced CSV file types with smart detection
SMART_CSV_TYPES = {
    'credit_subjects': {
        'display_name': 'Credit Subjects (Clients)',
        'description': 'Client information for credit scoring',
        'example_headers': ['id', 'full_name', 'national_id', 'phone_number', 'email']
    },
    'repayments': {
        'display_name': 'Loan Repayments',
        'description': 'Loan payment history and status',
        'example_headers': ['id', 'credit_subject_id', 'amount', 'loan_reference', 'due_date', 'status']
    },
    'mpesa_transactions': {
        'display_name': 'M-Pesa Transactions',
        'description': 'Mobile money transaction records',
        'example_headers': ['id', 'credit_subject_id', 'transaction_type', 'amount', 'reference', 'transaction_date']
    },
    'payments': {
        'display_name': 'General Payments',
        'description': 'All payment types and categories',
        'example_headers': ['id', 'credit_subject_id', 'amount', 'payment_type', 'status', 'payment_date']
    },
    'fines': {
        'display_name': 'Fines and Penalties',
        'description': 'Fine records and payment status',
        'example_headers': ['id', 'credit_subject_id', 'amount', 'reason', 'status']
    }
}


@router.get("/types")
async def get_supported_csv_types():
    """Get information about supported CSV types and expected formats."""
    return {
        "supported_types": SMART_CSV_TYPES,
        "features": {
            "auto_detection": "Automatically detects CSV type from column headers",
            "flexible_mapping": "Handles various column naming conventions",
            "data_validation": "Comprehensive data validation and sanitization",
            "duplicate_prevention": "Prevents client data duplication",
            "integrity_checks": "Ensures referential integrity"
        }
    }


@router.post("/analyze")
async def analyze_csv_file(
    file: UploadFile = File(...),
    csv_type: Optional[str] = Query(None, description="CSV type (optional - will auto-detect)"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Analyze CSV file without importing data.
    Returns structure, validation results, and mapping information.
    """
    try:
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_EXTENSION",
                    "message": "File must be a CSV file",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Read file content
        content = await file.read()
        
        # Process with smart processor
        processor = SmartCSVProcessor(db)
        result = processor.process_csv(content, csv_type)
        
        if result.get('errors'):
            return {
                "status": "validation_failed",
                "filename": file.filename,
                "analysis": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "validation_passed",
            "filename": file.filename,
            "analysis": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "ANALYSIS_ERROR",
                "message": f"Failed to analyze CSV: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post("/upload")
async def upload_csv_file(
    file: UploadFile = File(...),
    csv_type: Optional[str] = Query(None, description="CSV type (optional - will auto-detect)"),
    sync_to_db: Optional[bool] = Query(False, description="Import data to database"),
    validate_only: bool = Query(False, description="Validate without importing"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("operator"))
):
    """
    Upload and process CSV file with smart processing.
    
    Features:
    - Auto-detects CSV type from column headers
    - Handles various column naming conventions
    - Comprehensive data validation and sanitization
    - Prevents client data duplication
    - Ensures referential integrity
    """
    try:
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_EXTENSION",
                    "message": "File must be a CSV file",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Read and process CSV
        content = await file.read()
        processor = SmartCSVProcessor(db)
        result = processor.process_csv(content, csv_type)
        
        # Check for validation errors
        if result.get('errors'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "CSV validation failed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "validation_errors": result['errors'],
                        "warnings": result.get('warnings', [])
                    }
                }
            )
        
        # If validate_only, return here
        if validate_only:
            return {
                "message": f"CSV file '{file.filename}' validated successfully",
                "filename": file.filename,
                "csv_type": result['csv_type'],
                "analysis": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Save file to CSV directory
        settings = get_settings()
        csv_directory = settings.csv_directory
        os.makedirs(csv_directory, exist_ok=True)
        
        # Determine filename
        detected_type = result['csv_type']
        csv_config = SMART_CSV_TYPES[detected_type]
        target_filename = f"{detected_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        target_file = os.path.join(csv_directory, target_filename)
        
        # Backup existing file if needed
        if os.path.exists(target_file):
            backup_file = f"{target_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(target_file, backup_file)
        
        # Save uploaded file
        with open(target_file, 'wb') as f:
            f.write(content)
        
        # Sync to database if requested
        sync_stats = None
        if sync_to_db:
            try:
                sync_stats = sync_to_database(
                    csv_type=detected_type,
                    rows=result['parsed_rows'],
                    db=db
                )
            except Exception as e:
                db.rollback()
                raise
        
        response = {
            "message": f"CSV file '{file.filename}' processed successfully",
            "filename": file.filename,
            "csv_type": detected_type,
            "saved_as": target_filename,
            "column_mapping": result['column_mapping'],
            "rows_processed": len(result['parsed_rows']),
            "warnings": result.get('warnings', []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if sync_stats is not None:
            response["database_sync"] = sync_stats
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "UPLOAD_ERROR",
                "message": f"Failed to process CSV: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def sync_to_database(csv_type: str, rows: List[Dict], db: Session) -> Dict[str, int]:
    """
    Database sync that handles various data structures and ensures integrity.
    """
    inserted = 0
    updated = 0
    errors = 0
    
    try:
        for i, row in enumerate(rows):
            try:
                if csv_type == "credit_subjects":
                    result = sync_credit_subject(row, db)
                elif csv_type == "repayments":
                    result = sync_repayment(row, db)
                elif csv_type == "mpesa_transactions":
                    result = sync_mpesa_transaction(row, db)
                elif csv_type == "payments":
                    result = sync_payment(row, db)
                elif csv_type == "fines":
                    result = sync_fine(row, db)
                else:
                    continue
                
                if result == "inserted":
                    inserted += 1
                elif result == "updated":
                    updated += 1
                    
            except Exception as e:
                errors += 1
                continue
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e
    
    return {
        "inserted": inserted,
        "updated": updated,
        "errors": errors,
        "total": len(rows)
    }


def sync_credit_subject(row: Dict, db: Session) -> str:
    """Sync credit subject with smart handling."""
    subject_id = row.get('id')
    
    # Check if exists
    subject = db.get(CreditSubject, subject_id)
    if subject is None:
        subject = CreditSubject(id=subject_id)
        db.add(subject)
        result = "inserted"
    else:
        result = "updated"
    
    # Update fields
    subject.full_name = row.get('full_name', subject.full_name)
    subject.national_id = row.get('national_id', subject.national_id)
    subject.phone_number = row.get('phone_number', subject.phone_number)
    subject.email = row.get('email', subject.email)
    subject.external_id = row.get('external_id', subject.external_id)
    subject.created_at = row.get('created_at', subject.created_at) or datetime.utcnow()
    subject.updated_at = datetime.utcnow()
    
    return result


def sync_repayment(row: Dict, db: Session) -> str:
    """Sync repayment with smart handling."""
    repayment_id = row.get('id')
    
    repayment = db.get(Repayment, repayment_id)
    if repayment is None:
        repayment = Repayment(id=repayment_id)
        db.add(repayment)
        result = "inserted"
    else:
        result = "updated"
    
    # Update fields
    repayment.credit_subject_id = row.get('credit_subject_id', repayment.credit_subject_id)
    repayment.amount = row.get('amount', repayment.amount)
    repayment.loan_reference = row.get('loan_reference', repayment.loan_reference)
    repayment.due_date = row.get('due_date', repayment.due_date)
    repayment.payment_date = row.get('payment_date') or repayment.due_date  # Default to due_date if not provided
    
    # Handle enum properly
    status_value = row.get('status', 'late')
    try:
        repayment.status = RepaymentStatus(status_value)
    except ValueError:
        repayment.status = RepaymentStatus.late
    
    repayment.days_overdue = row.get('days_overdue', repayment.days_overdue or 0)
    repayment.created_at = row.get('created_at', repayment.created_at) or datetime.utcnow()
    
    return result


def sync_mpesa_transaction(row: Dict, db: Session) -> str:
    """Sync M-Pesa transaction with smart handling."""
    tx_id = row.get('id')
    
    transaction = db.get(MpesaTransaction, tx_id)
    if transaction is None:
        transaction = MpesaTransaction(id=tx_id)
        db.add(transaction)
        result = "inserted"
    else:
        result = "updated"
    
    # Update fields
    transaction.credit_subject_id = row.get('credit_subject_id', transaction.credit_subject_id)
    transaction.transaction_type = row.get('transaction_type', transaction.transaction_type)
    transaction.amount = row.get('amount', transaction.amount)
    transaction.reference = row.get('reference', transaction.reference)
    transaction.transaction_date = row.get('transaction_date', transaction.transaction_date)
    transaction.created_at = row.get('created_at', transaction.created_at) or datetime.utcnow()
    
    return result


def sync_payment(row: Dict, db: Session) -> str:
    """Sync payment with smart handling."""
    payment_id = row.get('id')
    
    payment = db.get(Payment, payment_id)
    if payment is None:
        payment = Payment(id=payment_id)
        db.add(payment)
        result = "inserted"
    else:
        result = "updated"
    
    # Update fields
    payment.credit_subject_id = row.get('credit_subject_id', payment.credit_subject_id)
    payment.amount = row.get('amount', payment.amount)
    payment.payment_type = PaymentType(row.get('payment_type', 'other'))
    payment.status = PaymentStatus(row.get('status', 'pending'))
    payment.payment_date = row.get('payment_date', payment.payment_date)
    payment.created_at = row.get('created_at', payment.created_at) or datetime.utcnow()
    
    return result


def sync_fine(row: Dict, db: Session) -> str:
    """Sync fine with smart handling."""
    fine_id = row.get('id')
    
    fine = db.get(Fine, fine_id)
    if fine is None:
        fine = Fine(id=fine_id)
        db.add(fine)
        result = "inserted"
    else:
        result = "updated"
    
    # Update fields
    fine.credit_subject_id = row.get('credit_subject_id', fine.credit_subject_id)
    fine.amount = row.get('amount', fine.amount)
    fine.reason = row.get('reason', fine.reason)
    fine.status = FineStatus(row.get('status', 'unpaid'))
    fine.assessed_date = row.get('assessed_date', fine.assessed_date)
    fine.paid_date = row.get('paid_date', fine.paid_date)
    fine.created_at = row.get('created_at', fine.created_at) or datetime.utcnow()
    
    return result
