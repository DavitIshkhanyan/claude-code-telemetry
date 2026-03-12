"""
Data ingestion pipeline module.

Orchestrates the full ingestion process from raw files to database.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

import pandas as pd

from src.config import get_config, Config
from src.storage import Database, get_database
from .parser import TelemetryParser
from .validators import DataValidator

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    End-to-end data ingestion pipeline.

    Handles:
    - Loading employees data
    - Parsing telemetry logs
    - Validating events
    - Loading data into database tables
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        database: Optional[Database] = None
    ):
        """
        Initialize ingestion pipeline.

        Args:
            config: Configuration object
            database: Database instance (creates default if not provided)
        """
        self.config = config or get_config()
        self.db = database or get_database()
        self.parser = TelemetryParser(validate=True)
        self.validator = DataValidator(
            skip_invalid=self.config.ingestion.skip_invalid_records
        )

        # Data buffers
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._api_requests: List[Dict[str, Any]] = []
        self._tool_decisions: List[Dict[str, Any]] = []
        self._tool_results: List[Dict[str, Any]] = []
        self._user_prompts: List[Dict[str, Any]] = []
        self._api_errors: List[Dict[str, Any]] = []

    def run(
        self,
        telemetry_path: Optional[Path] = None,
        employees_path: Optional[Path] = None,
        reset_db: bool = False
    ) -> Dict[str, int]:
        """
        Run the full ingestion pipeline.

        Args:
            telemetry_path: Path to telemetry_logs.jsonl
            employees_path: Path to employees.csv
            reset_db: If True, clear existing data before loading

        Returns:
            Dictionary with counts of records loaded per table
        """
        telemetry_path = telemetry_path or self.config.paths.telemetry_file
        employees_path = employees_path or self.config.paths.employees_file

        logger.info("=" * 60)
        logger.info("Starting ingestion pipeline")
        logger.info("=" * 60)

        # Initialize database
        self.db.initialize(force=reset_db)

        # Step 1: Load employees
        employees_count = self._load_employees(employees_path)
        logger.info(f"Loaded {employees_count} employees")

        # Step 2: Parse and process telemetry
        self._process_telemetry(telemetry_path)

        # Step 3: Load data into tables
        results = self._load_all_tables()

        # Log summary
        self.validator.log_summary()
        logger.info("=" * 60)
        logger.info("Ingestion complete!")
        logger.info(f"Results: {results}")
        logger.info("=" * 60)

        return results

    def _load_employees(self, employees_path: Path) -> int:
        """Load employees from CSV."""
        logger.info(f"Loading employees from {employees_path}")

        df = pd.read_csv(employees_path)
        df["created_at"] = datetime.now()

        # Clear existing and load
        self.db.execute("DELETE FROM employees")
        return self.db.insert_df("employees", df)

    def _process_telemetry(self, telemetry_path: Path) -> None:
        """Parse telemetry file and extract records."""
        logger.info(f"Processing telemetry from {telemetry_path}")

        event_counts = defaultdict(int)

        for event in self.parser.parse_file(telemetry_path):
            body = event.get("body", "")
            event_counts[body] += 1

            # Validate event
            validation = self.validator.validate_event(event)
            if not validation.is_valid and not self.config.ingestion.skip_invalid_records:
                continue

            # Extract and store by event type
            self._extract_session_info(event)

            if body == "claude_code.api_request":
                self._api_requests.append(self.parser.extract_api_request(event))
            elif body == "claude_code.tool_decision":
                self._tool_decisions.append(self.parser.extract_tool_decision(event))
            elif body == "claude_code.tool_result":
                self._tool_results.append(self.parser.extract_tool_result(event))
            elif body == "claude_code.user_prompt":
                self._user_prompts.append(self.parser.extract_user_prompt(event))
            elif body == "claude_code.api_error":
                self._api_errors.append(self.parser.extract_api_error(event))

        # Log event type distribution
        logger.info("Event type distribution:")
        for event_type, count in sorted(event_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {event_type}: {count:,}")

    def _extract_session_info(self, event: Dict[str, Any]) -> None:
        """Extract and update session metadata from event."""
        session_info = self.parser.extract_session_info(event)
        session_id = session_info["session_id"]

        if not session_id:
            return

        if session_id not in self._sessions:
            self._sessions[session_id] = {
                **session_info,
                "started_at": None,
                "ended_at": None,
                "event_count": 0,
            }

        session = self._sessions[session_id]
        session["event_count"] += 1

        # Update time range
        attrs = event.get("attributes", {})
        ts_str = attrs.get("event.timestamp")
        if ts_str:
            try:
                ts = self.parser.parse_timestamp(ts_str)
                if session["started_at"] is None or ts < session["started_at"]:
                    session["started_at"] = ts
                if session["ended_at"] is None or ts > session["ended_at"]:
                    session["ended_at"] = ts
            except Exception:
                pass

    def _load_all_tables(self) -> Dict[str, int]:
        """Load all buffered data into database tables."""
        results = {}

        # Sessions
        if self._sessions:
            sessions_df = pd.DataFrame(list(self._sessions.values()))
            self.db.execute("DELETE FROM sessions")
            results["sessions"] = self.db.insert_df("sessions", sessions_df)
            logger.info(f"Loaded {results['sessions']} sessions")

        # API Requests
        if self._api_requests:
            df = pd.DataFrame(self._api_requests)
            self.db.execute("DELETE FROM api_requests")
            results["api_requests"] = self.db.insert_df("api_requests", df)
            logger.info(f"Loaded {results['api_requests']} API requests")

        # Tool Decisions
        if self._tool_decisions:
            df = pd.DataFrame(self._tool_decisions)
            self.db.execute("DELETE FROM tool_decisions")
            results["tool_decisions"] = self.db.insert_df("tool_decisions", df)
            logger.info(f"Loaded {results['tool_decisions']} tool decisions")

        # Tool Results
        if self._tool_results:
            df = pd.DataFrame(self._tool_results)
            self.db.execute("DELETE FROM tool_results")
            results["tool_results"] = self.db.insert_df("tool_results", df)
            logger.info(f"Loaded {results['tool_results']} tool results")

        # User Prompts
        if self._user_prompts:
            df = pd.DataFrame(self._user_prompts)
            self.db.execute("DELETE FROM user_prompts")
            results["user_prompts"] = self.db.insert_df("user_prompts", df)
            logger.info(f"Loaded {results['user_prompts']} user prompts")

        # API Errors
        if self._api_errors:
            df = pd.DataFrame(self._api_errors)
            self.db.execute("DELETE FROM api_errors")
            results["api_errors"] = self.db.insert_df("api_errors", df)
            logger.info(f"Loaded {results['api_errors']} API errors")

        return results


def run_ingestion(
    telemetry_path: Optional[Path] = None,
    employees_path: Optional[Path] = None,
    reset_db: bool = False
) -> Dict[str, int]:
    """
    Convenience function to run ingestion pipeline.

    Args:
        telemetry_path: Path to telemetry_logs.jsonl
        employees_path: Path to employees.csv
        reset_db: If True, clear existing data

    Returns:
        Dictionary with record counts per table
    """
    pipeline = IngestionPipeline()
    return pipeline.run(telemetry_path, employees_path, reset_db)


if __name__ == "__main__":
    # Run ingestion when executed directly
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    reset = "--reset" in sys.argv
    results = run_ingestion(reset_db=reset)

    print("\nIngestion Results:")
    for table, count in results.items():
        print(f"  {table}: {count:,} rows")
