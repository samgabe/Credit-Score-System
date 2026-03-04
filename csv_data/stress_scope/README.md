# Stress Scope CSV Pack

Edge-case dataset to stress test scoring, analytics, and UI behavior.

## Files
- `users.csv` (10 users)
- `repayments.csv` (15 rows)
- `mpesa_transactions.csv` (14 rows)
- `payments.csv` (13 rows)
- `fines.csv` (6 rows)

## Designed Stress Patterns
- `Alpha Stable`: strong on-time + high liquidity
- `Beta Volatile`: mixed pattern (on-time + late + pending fine payment)
- `Gamma Default`: repeated defaults + unpaid penalty
- `Delta New`: very sparse new-user history
- `Epsilon Recovering`: late history then improved repayment
- `Zeta NoMpesa`: repayments/payments with little to no M-Pesa diversity
- `Eta FineHeavy`: late repayments + unpaid fines
- `Theta MicroPay`: small-value frequent-like profile
- `Iota HighVolume`: very high transaction/payment volumes
- `Kappa EdgeCase`: mixed completed+failed service payment with late repayment

## Usage
Upload each file from Settings -> CSV Upload under matching type.

If needed, switch backend to CSV mode:
- `python3 backend/switch_data_source.py csv`
