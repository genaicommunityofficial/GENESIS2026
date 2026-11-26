-- GENESIS 2026 schema (PRD §14 + tables the PRD implies but doesn't define)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TYPE user_role AS ENUM ('PARTICIPANT','ADMIN');
CREATE TYPE user_status AS ENUM ('PENDING','ACTIVE','REJECTED','SUSPENDED');
CREATE TYPE order_side AS ENUM ('BUY','SELL','SHORT','COVER');
CREATE TYPE position_side AS ENUM ('LONG','SHORT');
CREATE TYPE topup_status AS ENUM ('PENDING','APPROVED','REJECTED');

CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  reg_number VARCHAR(50) UNIQUE,
  password_hash TEXT NOT NULL,                       -- added: PRD has login but no password column
  role user_role DEFAULT 'PARTICIPANT',
  status user_status DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE wallets (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  balance NUMERIC(14,2) NOT NULL DEFAULT 25000.00,
  collateral_locked NUMERIC(14,2) NOT NULL DEFAULT 0.00,
  total_credited NUMERIC(14,2) NOT NULL DEFAULT 25000.00,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT positive_balance CHECK (balance >= 0),
  CONSTRAINT positive_collateral CHECK (collateral_locked >= 0)
);
CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(150) NOT NULL,
  symbol VARCHAR(12) UNIQUE NOT NULL,
  sector VARCHAR(80) NOT NULL,
  pe_ratio NUMERIC(6,2),
  max_shares_per_user INT DEFAULT 40,
  price_floor NUMERIC(10,2) DEFAULT 10.00
);
CREATE TABLE stocks (
  company_id UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
  current_price NUMERIC(12,2) NOT NULL,
  anchor_price NUMERIC(12,2) NOT NULL,
  day_high NUMERIC(12,2) NOT NULL,
  day_low NUMERIC(12,2) NOT NULL,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT bounded_price CHECK (current_price >= 10.00)
);
CREATE TABLE holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  side position_side NOT NULL DEFAULT 'LONG',
  quantity INT NOT NULL,
  avg_entry_price NUMERIC(12,2) NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT positive_qty CHECK (quantity >= 0),
  CONSTRAINT unique_user_stock_side UNIQUE (user_id, company_id, side)
);
CREATE TABLE market_settings (
  id INT PRIMARY KEY DEFAULT 1,
  is_market_open BOOLEAN DEFAULT FALSE,
  is_leaderboard_frozen BOOLEAN DEFAULT FALSE,
  max_concentration_pct NUMERIC(5,2) DEFAULT 35.00,
  active_scenario_name VARCHAR(150) DEFAULT 'Normal Trading',
  CONSTRAINT single_row CHECK (id = 1)
);
INSERT INTO market_settings DEFAULT VALUES;

-- ---- tables the PRD mentions but does not define ----
CREATE TABLE transactions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id),
  company_id UUID NOT NULL REFERENCES companies(id),
  side order_side NOT NULL,
  quantity INT NOT NULL,
  price NUMERIC(12,2) NOT NULL,
  realized_pnl NUMERIC(14,2),
  forced BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON transactions(user_id, created_at DESC);
CREATE TABLE topup_requests (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES profiles(id),   -- UNIQUE = max 1 request per user
  status topup_status DEFAULT 'PENDING',
  decided_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  decided_at TIMESTAMPTZ
);
CREATE TABLE scenario_executions (
  id SERIAL PRIMARY KEY,
  scenario_id TEXT UNIQUE NOT NULL,                  -- UNIQUE = an era fires only once (idempotency)
  executed_by UUID REFERENCES profiles(id),
  executed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  actor_id UUID REFERENCES profiles(id),
  action TEXT NOT NULL,
  detail JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE leaderboard_snapshot (
  id INT PRIMARY KEY DEFAULT 1,
  payload JSONB NOT NULL DEFAULT '[]',
  taken_at TIMESTAMPTZ DEFAULT NOW()
);
