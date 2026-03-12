"""
Database schema definitions and table creation.

Defines the schema for all tables used in the analytics platform.
Supports both DuckDB and PostgreSQL.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Schema Definitions
# ============================================================================

EMPLOYEES_SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    email VARCHAR PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    practice VARCHAR NOT NULL,
    level VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SESSIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    organization_id VARCHAR,
    terminal_type VARCHAR,
    os_type VARCHAR,
    os_version VARCHAR,
    host_arch VARCHAR,
    host_name VARCHAR,
    service_version VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    event_count INTEGER DEFAULT 0,
    FOREIGN KEY (email) REFERENCES employees(email)
);
"""

API_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_requests (
    session_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    model VARCHAR NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_creation_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cost_usd DOUBLE NOT NULL,
    duration_ms INTEGER NOT NULL
);
"""

TOOL_DECISIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_decisions (
    session_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    tool_name VARCHAR NOT NULL,
    decision VARCHAR NOT NULL,
    source VARCHAR
);
"""

TOOL_RESULTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_results (
    session_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    tool_name VARCHAR NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms INTEGER NOT NULL,
    decision_source VARCHAR,
    decision_type VARCHAR,
    result_size_bytes INTEGER
);
"""

USER_PROMPTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_prompts (
    session_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    prompt_length INTEGER NOT NULL
);
"""

API_ERRORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_errors (
    session_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    model VARCHAR,
    error_message VARCHAR,
    status_code VARCHAR,
    attempt INTEGER,
    duration_ms INTEGER
);
"""

# Indexes for common queries
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_api_requests_timestamp ON api_requests(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_api_requests_email ON api_requests(email);",
    "CREATE INDEX IF NOT EXISTS idx_api_requests_model ON api_requests(model);",
    "CREATE INDEX IF NOT EXISTS idx_api_requests_session ON api_requests(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_tool_decisions_timestamp ON tool_decisions(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_tool_decisions_tool ON tool_decisions(tool_name);",
    "CREATE INDEX IF NOT EXISTS idx_tool_results_timestamp ON tool_results(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_tool_results_tool ON tool_results(tool_name);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(email);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);",
    "CREATE INDEX IF NOT EXISTS idx_user_prompts_timestamp ON user_prompts(timestamp);",
]

ALL_SCHEMAS = [
    ("employees", EMPLOYEES_SCHEMA),
    ("sessions", SESSIONS_SCHEMA),
    ("api_requests", API_REQUESTS_SCHEMA),
    ("tool_decisions", TOOL_DECISIONS_SCHEMA),
    ("tool_results", TOOL_RESULTS_SCHEMA),
    ("user_prompts", USER_PROMPTS_SCHEMA),
    ("api_errors", API_ERRORS_SCHEMA),
]


def create_all_tables(connection) -> None:
    """Create all tables in the database."""
    for table_name, schema in ALL_SCHEMAS:
        logger.info(f"Creating table: {table_name}")
        connection.execute(schema)

    for index_sql in INDEXES:
        try:
            connection.execute(index_sql)
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    logger.info("All tables and indexes created successfully")


def drop_all_tables(connection) -> None:
    """Drop all tables from the database."""
    tables = ["api_errors", "user_prompts", "tool_results", "tool_decisions",
              "api_requests", "sessions", "employees"]
    for table in tables:
        logger.info(f"Dropping table: {table}")
        connection.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    logger.info("All tables dropped")
