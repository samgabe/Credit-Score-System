# Proposed Database Schema Changes

## Current Issues:
- Single `users` table mixing system users and credit-scored users
- Authentication conflicts between user types
- No role-based access control

## Proposed Solution:

### 1. System Users Table (for login/administration)
```sql
CREATE TABLE system_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'operator', -- admin, operator, viewer
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Credit Subjects Table (for scoring)
```sql
CREATE TABLE credit_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255), -- For CSV import reference
    full_name VARCHAR(255) NOT NULL,
    national_id VARCHAR(50),
    phone_number VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Updated Foreign Key References
```sql
-- Update credit_scores table
ALTER TABLE credit_scores 
DROP CONSTRAINT IF EXISTS credit_scores_user_id_fkey,
ADD COLUMN credit_subject_id UUID REFERENCES credit_subjects(id);

-- Update factor data tables
ALTER TABLE repayments 
DROP CONSTRAINT IF EXISTS repayments_user_id_fkey,
ADD COLUMN credit_subject_id UUID REFERENCES credit_subjects(id);

-- Similar for mpesa_transactions, payments, fines
```

### 4. Migration Strategy
1. Create new tables
2. Migrate existing system users to `system_users`
3. Migrate credit-scored users to `credit_subjects`
4. Update foreign key references
5. Update application code
6. Test thoroughly
7. Drop old columns/constraints
