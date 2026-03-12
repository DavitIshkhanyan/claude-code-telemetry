"""
Telemetry event parser module.

Handles parsing of JSONL telemetry logs into structured data.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional, Generator
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ParsedEvent:
    """Structured representation of a telemetry event."""
    event_type: str
    session_id: str
    user_id: str
    email: Optional[str]
    timestamp: datetime
    organization_id: Optional[str]
    terminal_type: Optional[str]
    attributes: Dict[str, Any]
    resource: Dict[str, Any]
    scope: Dict[str, Any]


class TelemetryParser:
    """
    Parser for Claude Code telemetry JSONL files.

    Handles the CloudWatch-style log batch format with nested events.
    """

    def __init__(self, validate: bool = True):
        """
        Initialize parser.

        Args:
            validate: Whether to perform basic validation during parsing
        """
        self.validate = validate
        self._parse_errors: List[str] = []
        self._events_parsed = 0
        self._batches_parsed = 0

    def parse_file(self, file_path: Path) -> Generator[Dict[str, Any], None, None]:
        """
        Parse a JSONL telemetry file.

        Args:
            file_path: Path to the telemetry_logs.jsonl file

        Yields:
            Parsed event dictionaries
        """
        logger.info(f"Parsing telemetry file: {file_path}")

        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    batch = json.loads(line)
                    self._batches_parsed += 1

                    for event in self._parse_batch(batch):
                        self._events_parsed += 1
                        yield event

                except json.JSONDecodeError as e:
                    error_msg = f"JSON decode error at line {line_num}: {e}"
                    self._parse_errors.append(error_msg)
                    logger.warning(error_msg)
                except Exception as e:
                    error_msg = f"Error parsing line {line_num}: {e}"
                    self._parse_errors.append(error_msg)
                    logger.warning(error_msg)

        logger.info(
            f"Parsing complete: {self._batches_parsed} batches, "
            f"{self._events_parsed} events, {len(self._parse_errors)} errors"
        )

    def _parse_batch(self, batch: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Parse a log batch containing multiple events."""
        log_events = batch.get("logEvents", [])

        for log_event in log_events:
            message = log_event.get("message")
            if not message:
                continue

            try:
                if isinstance(message, str):
                    event = json.loads(message)
                else:
                    event = message

                yield event

            except json.JSONDecodeError:
                self._parse_errors.append(f"Failed to parse event message")
                continue

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp string to datetime."""
        # Format: 2025-01-01T12:34:56.123Z
        try:
            # Handle milliseconds
            dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Fallback to pandas parser for other formats
            return pd.to_datetime(timestamp_str, utc=True).to_pydatetime()

    def extract_api_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract api_request data from event."""
        attrs = event.get("attributes", {})
        resource = event.get("resource", {})

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "timestamp": self.parse_timestamp(attrs.get("event.timestamp")),
            "model": attrs.get("model"),
            "input_tokens": int(attrs.get("input_tokens", 0)),
            "output_tokens": int(attrs.get("output_tokens", 0)),
            "cache_creation_tokens": int(attrs.get("cache_creation_tokens", 0)),
            "cache_read_tokens": int(attrs.get("cache_read_tokens", 0)),
            "cost_usd": float(attrs.get("cost_usd", 0)),
            "duration_ms": int(attrs.get("duration_ms", 0)),
        }

    def extract_tool_decision(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tool_decision data from event."""
        attrs = event.get("attributes", {})

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "timestamp": self.parse_timestamp(attrs.get("event.timestamp")),
            "tool_name": attrs.get("tool_name"),
            "decision": attrs.get("decision"),
            "source": attrs.get("source"),
        }

    def extract_tool_result(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tool_result data from event."""
        attrs = event.get("attributes", {})

        success_val = attrs.get("success", "false")
        if isinstance(success_val, str):
            success = success_val.lower() == "true"
        else:
            success = bool(success_val)

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "timestamp": self.parse_timestamp(attrs.get("event.timestamp")),
            "tool_name": attrs.get("tool_name"),
            "success": success,
            "duration_ms": int(attrs.get("duration_ms", 0)),
            "decision_source": attrs.get("decision_source"),
            "decision_type": attrs.get("decision_type"),
            "result_size_bytes": int(attrs.get("tool_result_size_bytes", 0))
                if attrs.get("tool_result_size_bytes") else None,
        }

    def extract_user_prompt(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user_prompt data from event."""
        attrs = event.get("attributes", {})

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "timestamp": self.parse_timestamp(attrs.get("event.timestamp")),
            "prompt_length": int(attrs.get("prompt_length", 0)),
        }

    def extract_api_error(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract api_error data from event."""
        attrs = event.get("attributes", {})

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "timestamp": self.parse_timestamp(attrs.get("event.timestamp")),
            "model": attrs.get("model"),
            "error_message": attrs.get("error"),
            "status_code": attrs.get("status_code"),
            "attempt": int(attrs.get("attempt", 1)),
            "duration_ms": int(attrs.get("duration_ms", 0)),
        }

    def extract_session_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract session metadata from an event."""
        attrs = event.get("attributes", {})
        resource = event.get("resource", {})

        return {
            "session_id": attrs.get("session.id"),
            "user_id": attrs.get("user.id"),
            "email": attrs.get("user.email"),
            "organization_id": attrs.get("organization.id"),
            "terminal_type": attrs.get("terminal.type"),
            "os_type": resource.get("os.type"),
            "os_version": resource.get("os.version"),
            "host_arch": resource.get("host.arch"),
            "host_name": resource.get("host.name"),
            "service_version": resource.get("service.version"),
        }

    def get_parse_errors(self) -> List[str]:
        """Get list of parse errors encountered."""
        return self._parse_errors.copy()

    def get_stats(self) -> Dict[str, int]:
        """Get parsing statistics."""
        return {
            "batches_parsed": self._batches_parsed,
            "events_parsed": self._events_parsed,
            "parse_errors": len(self._parse_errors),
        }
