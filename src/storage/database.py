"""
Database connection and query execution module.

Provides a unified interface for DuckDB and PostgreSQL databases.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Any, List, Dict, Union
from contextlib import contextmanager

import duckdb
import pandas as pd
import polars as pl

from src.config import get_config, Config
from .schema import create_all_tables

logger = logging.getLogger(__name__)


class Database:
    """
    Database abstraction layer supporting DuckDB and PostgreSQL.

    Provides methods for executing queries, loading DataFrames,
    and managing connections.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize database connection."""
        self.config = config or get_config()
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._connection is None:
            db_path = self.config.paths.database_file
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Connecting to DuckDB at {db_path}")
            self._connection = duckdb.connect(str(db_path))
        return self._connection

    def initialize(self, force: bool = False) -> None:
        """Initialize database schema."""
        if self._initialized and not force:
            return

        logger.info("Initializing database schema...")
        create_all_tables(self.connection)
        self._initialized = True
        logger.info("Database initialized successfully")

    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query."""
        try:
            if params:
                return self.connection.execute(query, params)
            return self.connection.execute(query)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query[:200]}...")
            raise

    def query_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return results as pandas DataFrame."""
        result = self.execute(query, params)
        return result.fetchdf()

    def query_polars(self, query: str, params: Optional[tuple] = None) -> pl.DataFrame:
        """Execute query and return results as polars DataFrame."""
        result = self.execute(query, params)
        return result.pl()

    def insert_df(
        self,
        table: str,
        df: pd.DataFrame,
        if_exists: str = "append"
    ) -> int:
        """
        Insert a pandas DataFrame into a table.

        Args:
            table: Target table name
            df: DataFrame to insert
            if_exists: 'append', 'replace', or 'fail'

        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0

        if if_exists == "replace":
            self.execute(f"DELETE FROM {table}")

        # Register DataFrame as a view and insert
        self.connection.register("_temp_df", df)

        try:
            columns = ", ".join(df.columns)
            self.execute(f"INSERT INTO {table} ({columns}) SELECT * FROM _temp_df")
            rows_inserted = len(df)
            logger.debug(f"Inserted {rows_inserted} rows into {table}")
            return rows_inserted
        finally:
            self.connection.unregister("_temp_df")

    def insert_polars(
        self,
        table: str,
        df: pl.DataFrame,
        if_exists: str = "append"
    ) -> int:
        """Insert a polars DataFrame into a table."""
        return self.insert_df(table, df.to_pandas(), if_exists)

    def table_exists(self, table: str) -> bool:
        """Check if a table exists."""
        result = self.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            (table,)
        )
        return result.fetchone()[0] > 0

    def get_table_count(self, table: str) -> int:
        """Get row count for a table."""
        result = self.execute(f"SELECT COUNT(*) FROM {table}")
        return result.fetchone()[0]

    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        tables = ["employees", "sessions", "api_requests", "tool_decisions",
                  "tool_results", "user_prompts", "api_errors"]
        stats = {}
        for table in tables:
            try:
                stats[table] = self.get_table_count(table)
            except Exception:
                stats[table] = 0
        return stats

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def __enter__(self) -> Database:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# Global database instance
_database: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        _database = Database()
        _database.initialize()
    return _database


def reset_database() -> None:
    """Reset the global database instance."""
    global _database
    if _database:
        _database.close()
    _database = None
