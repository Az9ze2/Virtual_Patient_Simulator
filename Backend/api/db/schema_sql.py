# Separate DROP and CREATE sections so admin tools can choose behavior
DROP_SCHEMA_SQL = r"""
-- Drop existing tables in dependency order
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS session_reports CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS cases CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS test_table CASCADE;
DROP TABLE IF EXISTS users_data CASCADE;
"""

CREATE_SCHEMA_SQL = r"""
-- Users
CREATE TABLE users (
  user_id VARCHAR PRIMARY KEY,
  student_id VARCHAR NOT NULL UNIQUE,
  name VARCHAR NOT NULL,
  email VARCHAR,
  preferences JSONB,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cases
CREATE TABLE cases (
  case_id VARCHAR PRIMARY KEY, -- Format: XX_YY
  case_name VARCHAR NOT NULL,
  case_type VARCHAR,
  case_data JSONB,
  import_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions
CREATE TABLE sessions (
  session_id VARCHAR PRIMARY KEY,
  user_id VARCHAR NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  case_id VARCHAR NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
  status VARCHAR NOT NULL DEFAULT 'active',
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  duration_seconds INTEGER,
  total_tokens INTEGER DEFAULT 0
);

-- Chat messages (message_id incremental)
CREATE TABLE chat_messages (
  message_id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  session_id VARCHAR NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  role VARCHAR NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  tokens_used INTEGER DEFAULT 0,
  response_time_ms INTEGER
);

-- Session reports
CREATE TABLE session_reports (
  report_id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  generated_at TIMESTAMP NOT NULL,
  summary JSONB
);

-- Audit log (log_id incremental)
CREATE TABLE audit_log (
  log_id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR REFERENCES users(user_id) ON DELETE SET NULL,
  session_id VARCHAR REFERENCES sessions(session_id) ON DELETE SET NULL,
  action_type VARCHAR NOT NULL,
  details TEXT,
  ip_address VARCHAR,
  performed_at TIMESTAMP NOT NULL
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_case ON sessions(case_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_session ON audit_log(session_id);
"""

# Full reset (drop then create)
SCHEMA_SQL = DROP_SCHEMA_SQL + "\n" + CREATE_SCHEMA_SQL
