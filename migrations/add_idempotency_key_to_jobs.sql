-- Add idempotency_key column to jobs table
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255);

-- Create index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key ON jobs (idempotency_key);

-- Update existing rows with a default value if needed
-- UPDATE jobs SET idempotency_key = gen_random_uuid()::text WHERE idempotency_key IS NULL;
