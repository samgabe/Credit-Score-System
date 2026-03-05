"""
M-Pesa Statement Upload Router
Handles uploading and processing of individual client M-Pesa statements
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.mpesa_statement import MpesaStatement
from app.models.credit_subject import CreditSubject
from app.repositories.mpesa_statement_repository import MpesaStatementRepository
from app.services.mpesa_statement_parser import MpesaStatementParser
from app.services.individual_factor_calculator import IndividualFactorCalculator
from app.services.credit_score_service import CreditScoreService
from app.schemas.credit_subject import CreditSubjectResponse
from app.schemas.credit_score import CreditScoreResponse
from app.exceptions import CalculationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mpesa-statements", tags=["mpesa-statements"])

@router.post("/upload")
async def upload_mpesa_statement(
    file: UploadFile = File(..., description="M-Pesa statement PDF file"),
    credit_subject_id: str = Form(..., description="Credit subject ID"),
    db: Session = Depends(get_db)
):
    """
    Upload and process M-Pesa statement for a specific credit subject.
    
    Args:
        file: M-Pesa statement PDF file
        credit_subject_id: ID of the credit subject
        
    Returns:
        JSON response with processing results
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Validate credit subject exists
        credit_subject = db.query(CreditSubject).filter(CreditSubject.id == credit_subject_id).first()
        if not credit_subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit subject not found"
            )
        
        # Save uploaded file
        upload_dir = "uploads/mpesa_statements"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = f"{upload_dir}/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse statement
        parser = MpesaStatementParser()
        
        # Extract text from PDF (requires PyPDF2 or similar)
        import subprocess
        try:
            result = subprocess.run(
                ["pdftotext", file_path, "-"],
                capture_output=True,
                text=True,
                check=True
            )
            pdf_text = result.stdout
        except FileNotFoundError:
            # Fallback: try reading as text (for testing)
            with open(file_path, 'r') as f:
                pdf_text = f.read()
        
        # Parse statement text
        statement_summary, transactions = parser.parse_statement_text(pdf_text)
        
        # Save to database
        mpesa_repo = MpesaStatementRepository(db)
        statement = mpesa_repo.create_statement(
            credit_subject_id=uuid.UUID(credit_subject_id),
            customer_name=statement_summary.customer_name,
            mobile_number=statement_summary.mobile_number,
            statement_date=statement_summary.statement_date,
            statement_period=statement_summary.statement_period,
            file_path=file_path
        )
        
        # Save transactions
        saved_transactions = mpesa_repo.save_transactions(statement.id, transactions)
        
        # Calculate individual factors
        factor_calculator = IndividualFactorCalculator(db)
        factors = factor_calculator.calculate_all_factors(uuid.UUID(credit_subject_id))
        
        # Calculate new credit score
        credit_score_service = CreditScoreService(
            factor_aggregator=None,  # Not needed for individual scoring
            calculator=None,  # Will be created internally
            credit_score_repository=None,  # Will be created internally
            credit_subject_repository=None,
            db=db
        )
        
        try:
            new_score = credit_score_service.calculate_credit_score_for_subject(uuid.UUID(credit_subject_id))
        except Exception as e:
            logger.error(f"Error calculating credit score: {str(e)}")
            new_score = None
        
        return JSONResponse({
            "success": True,
            "message": "M-Pesa statement uploaded and processed successfully",
            "data": {
                "statement_id": str(statement.id),
                "credit_subject": {
                    "id": str(credit_subject.id),
                    "full_name": credit_subject.full_name,
                    "email": credit_subject.email
                },
                "statement_summary": {
                    "customer_name": statement_summary.customer_name,
                    "mobile_number": statement_summary.mobile_number,
                    "statement_period": statement_summary.statement_period,
                    "total_paid_in": statement_summary.total_paid_in,
                    "total_paid_out": statement_summary.total_paid_out
                },
                "transactions_count": len(saved_transactions),
                "factors": factors,
                "new_credit_score": {
                    "id": str(new_score.id) if new_score else None,
                    "score": new_score.score if new_score else None,
                    "category": new_score.category if new_score else None
                } if new_score else None
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing M-Pesa statement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing statement: {str(e)}"
        )

@router.get("/subject/{credit_subject_id}")
async def get_subject_statements(
    credit_subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all M-Pesa statements for a credit subject.
    
    Args:
        credit_subject_id: ID of the credit subject
        
    Returns:
        List of M-Pesa statements for the subject
    """
    try:
        mpesa_repo = MpesaStatementRepository(db)
        statements = mpesa_repo.get_all_statements_for_subject(credit_subject_id)
        
        return JSONResponse({
            "success": True,
            "data": [
                {
                    "id": str(stmt.id),
                    "customer_name": stmt.customer_name,
                    "mobile_number": stmt.mobile_number,
                    "statement_period": stmt.statement_period,
                    "statement_date": stmt.statement_date.isoformat(),
                    "upload_date": stmt.upload_date.isoformat(),
                    "is_active": stmt.is_active,
                    "file_path": stmt.file_path
                }
                for stmt in statements
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting statements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statements: {str(e)}"
        )

@router.get("/{statement_id}/transactions")
async def get_statement_transactions(
    statement_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific M-Pesa statement.
    
    Args:
        statement_id: ID of the statement
        
    Returns:
        List of transactions for the statement
    """
    try:
        mpesa_repo = MpesaStatementRepository(db)
        transactions = mpesa_repo.get_transactions_for_statement(statement_id)
        
        return JSONResponse({
            "success": True,
            "data": [
                {
                    "id": str(tx.id),
                    "receipt_no": tx.receipt_no,
                    "completion_time": tx.completion_time.isoformat(),
                    "transaction_type": tx.transaction_type,
                    "details": tx.details,
                    "recipient": tx.recipient,
                    "amount": float(tx.amount),
                    "status": tx.status,
                    "is_paid_in": tx.is_paid_in,
                    "is_paid_out": tx.is_paid_out
                }
                for tx in transactions
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )
