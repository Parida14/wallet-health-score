-- Wallet Score Health API - Initial schema (Phase 1)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    chain TEXT NOT NULL DEFAULT 'eth_mainnet',
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    hash TEXT PRIMARY KEY,
    address TEXT NOT NULL REFERENCES wallets(address) ON DELETE CASCADE,
    block_number BIGINT,
    timestamp TIMESTAMPTZ NOT NULL,
    gas_spent_usd NUMERIC(38, 18),
    tx_type TEXT,
    contracts_involved TEXT[] DEFAULT '{}',
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_address_timestamp
    ON transactions (address, timestamp DESC);

CREATE TABLE IF NOT EXISTS positions (
    address TEXT NOT NULL REFERENCES wallets(address) ON DELETE CASCADE,
    token TEXT NOT NULL,
    protocol TEXT,
    balance NUMERIC(78, 0),
    usd_value NUMERIC(38, 18),
    last_updated TIMESTAMPTZ NOT NULL,
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (address, token, COALESCE(protocol, ''))
);

CREATE TABLE IF NOT EXISTS features_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address TEXT NOT NULL REFERENCES wallets(address) ON DELETE CASCADE,
    date DATE NOT NULL,
    activity_score NUMERIC(5, 4),
    diversification_score NUMERIC(5, 4),
    risk_score NUMERIC(5, 4),
    profitability_score NUMERIC(5, 4),
    stability_score NUMERIC(5, 4),
    total_score NUMERIC(5, 4),
    metrics JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (address, date)
);

CREATE INDEX IF NOT EXISTS idx_features_daily_address_date
    ON features_daily (address, date DESC);
