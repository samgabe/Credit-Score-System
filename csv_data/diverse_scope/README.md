# Diverse Scope CSV Pack

This pack is designed to broaden demo/test coverage of the credit scoring system with realistic mixed behavior patterns.

## Files
- `users.csv` (12 users)
- `repayments.csv` (18 records)
- `mpesa_transactions.csv` (18 records)
- `payments.csv` (16 records)
- `fines.csv` (8 records)

## Scenario Coverage
- Strong repayment discipline (`on_time` heavy)
- Mixed repayment patterns (`late` + recovered)
- High-risk/default patterns (`defaulted`, unpaid fines)
- Disputed fine case (`status=disputed`)
- Inconsistent payment outcomes (`pending`, `failed`, `completed`)
- Broad M-Pesa behavior (`deposit`, `withdrawal`, `transfer`, `payment`)

## Quick Use
1. Upload these files through the Settings -> CSV upload section (matching each file type).
2. Switch backend source to CSV mode if needed:
   - `python3 backend/switch_data_source.py csv`
3. Restart backend and run analytics/score calculations.

## Notes
- All status/type values align with backend validation rules.
- All `user_id` references map to `users.csv`.
- Dates are in ISO format.
