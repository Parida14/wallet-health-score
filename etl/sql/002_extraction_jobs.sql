-- Extraction Jobs table for tracking on-demand wallet ETL requests

CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_address
    ON extraction_jobs (address, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status
    ON extraction_jobs (status);
