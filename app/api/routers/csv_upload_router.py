"""
CSV Upload Router for the Credit Score API.
Handles CSV file uploads, validation, and processing for credit score calculations.
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
from app.models.user import User
from app.models.repayment import Repayment, RepaymentStatus
from app.models.mpesa_transaction import MpesaTransaction, TransactionType
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.fine import Fine, FineStatus

router = APIRouter(prefix="/csv-upload", tags=["csv-upload"])

# Required CSV file types and their expected headers
CSV_FILE_TYPES = {
    'users': {
        'required_headers': ['id', 'fullname', 'national_id', 'phone_number', 'email'],
        'optional_headers': ['created_at', 'updated_at'],
        'filename': 'users.csv'
    },
    'repayments': {
        'required_headers': ['id', 'user_id', 'amount', 'loan_reference', 'due_date', 'status'],
        'optional_headers': ['payment_date', 'days_overdue', 'created_at'],
        'filename': 'repayments.csv'
    },
    'mpesa_transactions': {
        'required_headers': ['id', 'user_id', 'transaction_type', 'amount', 'reference', 'transaction_date'],
        'optional_headers': ['created_at'],
        'filename': 'mpesa_transactions.csv'
    },
    'payments': {
        'required_headers': ['id', 'user_id', 'amount', 'payment_type', 'status', 'payment_date'],
        'optional_headers': ['created_at'],
        'filename': 'payments.csv'
    },
    'fines': {
        'required_headers': ['id', 'user_id', 'amount', 'reason', 'status'],
        'optional_headers': ['assessed_date', 'paid_date', 'created_at'],
        'filename': 'fines.csv'
    }
}


def parse_and_validate_csv_content(file_type: str, content: bytes, csv_config: Dict) -> Dict:
    """
    Parse CSV bytes, validate headers and sample row data.
    Returns a dict with parsed headers and rows.
    """
    try:
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(csv_content.splitlines())
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "ENCODING_ERROR",
                "message": "CSV file must be UTF-8 encoded",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "CSV_PARSE_ERROR",
                "message": f"Error parsing CSV file: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    headers = csv_reader.fieldnames or []
    missing_headers = set(csv_config['required_headers']) - set(headers)
    if missing_headers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "MISSING_HEADERS",
                "message": f"CSV file is missing required headers: {', '.join(missing_headers)}",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "required_headers": csv_config['required_headers'],
                    "found_headers": headers,
                    "missing_headers": list(missing_headers)
                }
            }
        )

    rows = list(csv_reader)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "EMPTY_CSV",
                "message": "CSV file contains no data rows",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    validation_errors = validate_csv_data(file_type, rows)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "DATA_VALIDATION_ERROR",
                "message": "CSV data validation failed",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"validation_errors": validation_errors}
            }
        )

    return {"headers": headers, "rows": rows}


@router.post(
    "/{file_type}",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or format"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_csv_file(
    file_type: str,
    file: UploadFile = File(...),
    sync_to_db: bool = Query(False, description="If true, also upsert uploaded rows into database tables"),
    db: Session = Depends(get_db)
):
    """
    Upload and process a CSV file for credit score data.
    
    Args:
        file_type: Type of CSV file (users, repayments, mpesa_transactions, payments, fines)
        file: CSV file to upload
        
    Returns:
        Dict: Upload result with processing statistics
        
    Validates: CSV format, required headers, data types
    """
    try:
        # Validate file type
        if file_type not in CSV_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": f"Invalid file type. Must be one of: {', '.join(CSV_FILE_TYPES.keys())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
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
        
        # Get CSV configuration
        csv_config = CSV_FILE_TYPES[file_type]
        settings = get_settings()
        csv_directory = settings.csv_directory
        
        # Ensure CSV directory exists
        os.makedirs(csv_directory, exist_ok=True)
        
        # Read and validate CSV content
        content = await file.read()
        
        parsed = parse_and_validate_csv_content(file_type=file_type, content=content, csv_config=csv_config)
        headers = parsed["headers"]
        rows = parsed["rows"]
        
        # Backup existing file if it exists
        target_file = os.path.join(csv_directory, csv_config['filename'])
        if os.path.exists(target_file):
            backup_file = f"{target_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(target_file, backup_file)
        
        # Save the uploaded file
        with open(target_file, 'wb') as f:
            f.write(content)
        
        db_sync_stats = None
        if sync_to_db:
            missing_users = validate_db_sync_prerequisites(file_type=file_type, rows=rows, db=db)
            if missing_users:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error_code": "MISSING_REFERENCED_USERS",
                        "message": "Cannot sync to DB: some user_id values do not exist in users table. Upload/sync users.csv first.",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": {
                            "missing_user_ids": missing_users[:20],
                            "missing_count": len(missing_users)
                        }
                    }
                )
            try:
                db_sync_stats = sync_csv_to_database(file_type=file_type, rows=rows, db=db)
            except IntegrityError as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error_code": "DB_SYNC_CONSTRAINT_ERROR",
                        "message": "Database sync failed due to constraint violation",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": {"error": str(e.orig)}
                    }
                )

        response = {
            "message": f"CSV file '{file.filename}' uploaded successfully",
            "file_type": file_type,
            "filename": csv_config['filename'],
            "rows_processed": len(rows),
            "headers_found": headers,
            "timestamp": datetime.utcnow().isoformat()
        }
        if db_sync_stats is not None:
            response["db_sync"] = db_sync_stats

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "UPLOAD_ERROR",
                "message": "Failed to upload CSV file",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/sync-pack/{pack_name}",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation or constraint error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def sync_csv_pack(
    pack_name: str,
    sync_to_db: bool = Query(True, description="If true, upsert pack rows into DB as well"),
    db: Session = Depends(get_db)
):
    """
    Import all CSV files from a named pack directory under csv_data in safe dependency order:
    users -> repayments -> mpesa_transactions -> payments -> fines.
    """
    try:
        settings = get_settings()
        csv_directory = settings.csv_directory
        pack_dir = os.path.join(csv_directory, pack_name)

        if not os.path.isdir(pack_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "PACK_NOT_FOUND",
                    "message": f"CSV pack directory not found: {pack_dir}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        ordered_types = ["users", "repayments", "mpesa_transactions", "payments", "fines"]
        results = []

        for file_type in ordered_types:
            config = CSV_FILE_TYPES[file_type]
            src_path = os.path.join(pack_dir, config["filename"])
            dst_path = os.path.join(csv_directory, config["filename"])

            if not os.path.exists(src_path):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error_code": "PACK_FILE_MISSING",
                        "message": f"Required pack file missing: {config['filename']}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            with open(src_path, "rb") as f:
                content = f.read()

            parsed = parse_and_validate_csv_content(file_type=file_type, content=content, csv_config=config)
            headers = parsed["headers"]
            rows = parsed["rows"]

            if os.path.exists(dst_path):
                backup_file = f"{dst_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(dst_path, backup_file)
            with open(dst_path, "wb") as f:
                f.write(content)

            file_result = {
                "file_type": file_type,
                "filename": config["filename"],
                "rows_processed": len(rows),
                "headers_found": headers
            }

            if sync_to_db:
                missing_users = validate_db_sync_prerequisites(file_type=file_type, rows=rows, db=db)
                if missing_users:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "error_code": "MISSING_REFERENCED_USERS",
                            "message": f"Cannot sync '{file_type}' to DB: missing user references.",
                            "timestamp": datetime.utcnow().isoformat(),
                            "details": {
                                "file_type": file_type,
                                "missing_user_ids": missing_users[:20],
                                "missing_count": len(missing_users)
                            }
                        }
                    )
                try:
                    file_result["db_sync"] = sync_csv_to_database(file_type=file_type, rows=rows, db=db)
                except IntegrityError as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "error_code": "DB_SYNC_CONSTRAINT_ERROR",
                            "message": f"Database sync failed for '{file_type}' due to constraint violation",
                            "timestamp": datetime.utcnow().isoformat(),
                            "details": {"error": str(e.orig)}
                        }
                    )

            results.append(file_result)

        return {
            "message": f"CSV pack '{pack_name}' imported successfully",
            "pack_name": pack_name,
            "sync_to_db": sync_to_db,
            "files": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PACK_SYNC_ERROR",
                "message": "Failed to sync CSV pack",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error": str(e)}
            }
        )

def validate_csv_data(file_type: str, rows: List[Dict]) -> List[str]:
    """
    Validate CSV data based on file type.
    
    Args:
        file_type: Type of CSV file
        rows: List of data rows
        
    Returns:
        List[str]: List of validation error messages
    """
    errors = []
    
    for i, row in enumerate(rows[:10]):  # Validate first 10 rows
        row_num = i + 2  # CSV row numbers start at 2 (after header)
        
        if file_type == 'users':
            errors.extend(validate_user_row(row, row_num))
        elif file_type == 'repayments':
            errors.extend(validate_repayment_row(row, row_num))
        elif file_type == 'mpesa_transactions':
            errors.extend(validate_mpesa_row(row, row_num))
        elif file_type == 'payments':
            errors.extend(validate_payment_row(row, row_num))
        elif file_type == 'fines':
            errors.extend(validate_fine_row(row, row_num))
    
    return errors


def validate_db_sync_prerequisites(file_type: str, rows: List[Dict], db: Session) -> List[str]:
    """
    Validate cross-table prerequisites before DB sync.
    Currently checks referenced user IDs for non-users files.
    """
    if file_type == "users":
        return []

    user_ids = {
        str(uid)
        for uid in (_parse_uuid(row.get("user_id")) for row in rows)
        if uid is not None
    }
    if not user_ids:
        return []

    existing = db.execute(
        select(User.id).where(User.id.in_([UUID(uid) for uid in user_ids]))
    ).scalars().all()
    existing_str = {str(uid) for uid in existing}
    missing = sorted(user_ids - existing_str)
    return missing


def _parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(str(value))
    except Exception:
        return None


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_date(value: Optional[str]):
    dt = _parse_datetime(value)
    return dt.date() if dt else None


def sync_csv_to_database(file_type: str, rows: List[Dict], db: Session) -> Dict[str, int]:
    """
    Upsert CSV rows into database tables.
    Notes:
    - Uses model-compatible enum mappings where CSV enums are broader.
    - Keeps existing endpoint behavior unless sync_to_db=true is provided.
    """
    inserted = 0
    updated = 0

    for row in rows:
        row_id = _parse_uuid(row.get("id"))
        if not row_id:
            continue

        if file_type == "users":
            model = db.get(User, row_id)
            if model is None:
                model = User(id=row_id)
                db.add(model)
                inserted += 1
            else:
                updated += 1

            model.fullname = row.get("fullname") or model.fullname
            model.national_id = int(row.get("national_id", model.national_id or 0))
            model.phone_number = row.get("phone_number") or model.phone_number
            model.email = row.get("email") or model.email
            model.created_at = _parse_datetime(row.get("created_at")) or model.created_at or datetime.utcnow()
            model.updated_at = _parse_datetime(row.get("updated_at")) or datetime.utcnow()

        elif file_type == "repayments":
            model = db.get(Repayment, row_id)
            if model is None:
                model = Repayment(id=row_id)
                db.add(model)
                inserted += 1
            else:
                updated += 1

            csv_status = row.get("status", "late")
            mapped_status = RepaymentStatus.on_time if csv_status == "on_time" else RepaymentStatus.late
            due_date = _parse_date(row.get("due_date")) or datetime.utcnow().date()
            payment_date = _parse_date(row.get("payment_date")) or due_date

            model.user_id = _parse_uuid(row.get("user_id")) or model.user_id
            model.amount = _parse_decimal(row.get("amount"))
            model.loan_reference = row.get("loan_reference") or model.loan_reference
            model.due_date = due_date
            model.payment_date = payment_date
            model.status = mapped_status
            model.days_overdue = int(row.get("days_overdue") or 0)
            model.created_at = _parse_datetime(row.get("created_at")) or model.created_at or datetime.utcnow()

        elif file_type == "mpesa_transactions":
            model = db.get(MpesaTransaction, row_id)
            if model is None:
                model = MpesaTransaction(id=row_id)
                db.add(model)
                inserted += 1
            else:
                updated += 1

            # CSV supports: deposit, withdrawal, transfer, payment.
            # DB model supports: incoming/outgoing.
            tx_type = (row.get("transaction_type") or "").lower()
            mapped_type = TransactionType.incoming if tx_type == "deposit" else TransactionType.outgoing

            model.user_id = _parse_uuid(row.get("user_id")) or model.user_id
            model.transaction_type = mapped_type
            model.amount = _parse_decimal(row.get("amount"))
            model.reference = row.get("reference") or model.reference
            model.transaction_date = _parse_datetime(row.get("transaction_date")) or model.transaction_date or datetime.utcnow()
            model.created_at = _parse_datetime(row.get("created_at")) or model.created_at or datetime.utcnow()

        elif file_type == "payments":
            model = db.get(Payment, row_id)
            if model is None:
                model = Payment(id=row_id)
                db.add(model)
                inserted += 1
            else:
                updated += 1

            # CSV supports: loan_payment, fine_payment, service_payment.
            # DB model supports: repayment, fine, other.
            csv_payment_type = (row.get("payment_type") or "").lower()
            payment_type_map = {
                "loan_payment": PaymentType.repayment,
                "fine_payment": PaymentType.fine,
                "service_payment": PaymentType.other,
            }

            model.user_id = _parse_uuid(row.get("user_id")) or model.user_id
            model.amount = _parse_decimal(row.get("amount"))
            model.payment_type = payment_type_map.get(csv_payment_type, PaymentType.other)
            model.status = PaymentStatus((row.get("status") or "pending").lower())
            model.payment_date = _parse_datetime(row.get("payment_date")) or model.payment_date or datetime.utcnow()
            model.created_at = _parse_datetime(row.get("created_at")) or model.created_at or datetime.utcnow()

        elif file_type == "fines":
            model = db.get(Fine, row_id)
            if model is None:
                model = Fine(id=row_id)
                db.add(model)
                inserted += 1
            else:
                updated += 1

            # CSV supports disputed but DB model has unpaid/paid only.
            csv_status = (row.get("status") or "unpaid").lower()
            mapped_status = FineStatus.paid if csv_status == "paid" else FineStatus.unpaid

            assessed_date = _parse_date(row.get("assessed_date")) or (_parse_datetime(row.get("created_at")) or datetime.utcnow()).date()
            paid_date = _parse_date(row.get("paid_date"))

            model.user_id = _parse_uuid(row.get("user_id")) or model.user_id
            model.amount = _parse_decimal(row.get("amount"))
            model.reason = row.get("reason") or model.reason
            model.status = mapped_status
            model.assessed_date = assessed_date
            model.paid_date = paid_date
            model.created_at = _parse_datetime(row.get("created_at")) or model.created_at or datetime.utcnow()

    db.commit()
    return {
        "synced": inserted + updated,
        "inserted": inserted,
        "updated": updated
    }

def validate_user_row(row: Dict, row_num: int) -> List[str]:
    """Validate a user row."""
    errors = []
    
    # Validate UUID
    try:
        UUID(row['id'])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid UUID format in 'id' column")
    
    # Validate national_id
    try:
        int(row['national_id'])
    except ValueError:
        errors.append(f"Row {row_num}: 'national_id' must be a number")
    
    # Validate phone number format (basic check)
    phone = row.get('phone_number', '')
    if not phone.startswith('+') and not phone.isdigit():
        errors.append(f"Row {row_num}: 'phone_number' should start with '+' or contain only digits")
    
    # Validate email format (basic check)
    email = row.get('email', '')
    if '@' not in email or '.' not in email:
        errors.append(f"Row {row_num}: Invalid email format in 'email' column")
    
    return errors

def validate_repayment_row(row: Dict, row_num: int) -> List[str]:
    """Validate a repayment row."""
    errors = []
    
    # Validate UUID
    try:
        UUID(row['user_id'])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid UUID format in 'user_id' column")
    
    # Validate amount
    try:
        float(row['amount'])
    except ValueError:
        errors.append(f"Row {row_num}: 'amount' must be a number")
    
    # Validate status
    valid_statuses = ['on_time', 'late', 'defaulted']
    if row['status'] not in valid_statuses:
        errors.append(f"Row {row_num}: 'status' must be one of: {', '.join(valid_statuses)}")
    
    return errors

def validate_mpesa_row(row: Dict, row_num: int) -> List[str]:
    """Validate an M-Pesa transaction row."""
    errors = []
    
    # Validate UUID
    try:
        UUID(row['user_id'])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid UUID format in 'user_id' column")
    
    # Validate amount
    try:
        float(row['amount'])
    except ValueError:
        errors.append(f"Row {row_num}: 'amount' must be a number")
    
    # Validate transaction type
    valid_types = ['deposit', 'withdrawal', 'transfer', 'payment']
    if row['transaction_type'] not in valid_types:
        errors.append(f"Row {row_num}: 'transaction_type' must be one of: {', '.join(valid_types)}")
    
    return errors

def validate_payment_row(row: Dict, row_num: int) -> List[str]:
    """Validate a payment row."""
    errors = []
    
    # Validate UUID
    try:
        UUID(row['user_id'])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid UUID format in 'user_id' column")
    
    # Validate amount
    try:
        float(row['amount'])
    except ValueError:
        errors.append(f"Row {row_num}: 'amount' must be a number")
    
    # Validate payment type
    valid_types = ['loan_payment', 'fine_payment', 'service_payment']
    if row['payment_type'] not in valid_types:
        errors.append(f"Row {row_num}: 'payment_type' must be one of: {', '.join(valid_types)}")
    
    # Validate status
    valid_statuses = ['pending', 'completed', 'failed']
    if row['status'] not in valid_statuses:
        errors.append(f"Row {row_num}: 'status' must be one of: {', '.join(valid_statuses)}")
    
    return errors

def validate_fine_row(row: Dict, row_num: int) -> List[str]:
    """Validate a fine row."""
    errors = []
    
    # Validate UUID
    try:
        UUID(row['user_id'])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid UUID format in 'user_id' column")
    
    # Validate amount
    try:
        float(row['amount'])
    except ValueError:
        errors.append(f"Row {row_num}: 'amount' must be a number")
    
    # Validate status
    valid_statuses = ['unpaid', 'paid', 'disputed']
    if row['status'] not in valid_statuses:
        errors.append(f"Row {row_num}: 'status' must be one of: {', '.join(valid_statuses)}")
    
    return errors

@router.get(
    "/templates",
    responses={
        200: {"description": "CSV templates information"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_csv_templates():
    """
    Get information about required CSV templates.
    
    Returns:
        Dict: CSV template requirements for all file types
    """
    return {
        "templates": CSV_FILE_TYPES,
        "general_requirements": {
            "encoding": "UTF-8",
            "delimiter": "comma (,)",
            "headers": "first row must contain column headers",
            "date_format": "ISO format (YYYY-MM-DDTHH:MM:SS)"
        }
    }
