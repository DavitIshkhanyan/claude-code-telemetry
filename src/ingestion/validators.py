"""
Data validation module for telemetry events.

Provides schema validation and data quality checks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


@dataclass
class ValidationStats:
    """Statistics from validation run."""
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    warnings_count: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    @property
    def validity_rate(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.valid_records / self.total_records


class DataValidator:
    """
    Validates telemetry data against expected schemas and business rules.
    """

    # Required fields by event type
    REQUIRED_FIELDS = {
        "claude_code.api_request": [
            "session.id", "user.id", "event.timestamp", "model",
            "input_tokens", "output_tokens", "cost_usd", "duration_ms"
        ],
        "claude_code.tool_decision": [
            "session.id", "user.id", "event.timestamp",
            "tool_name", "decision"
        ],
        "claude_code.tool_result": [
            "session.id", "user.id", "event.timestamp",
            "tool_name", "success", "duration_ms"
        ],
        "claude_code.user_prompt": [
            "session.id", "user.id", "event.timestamp", "prompt_length"
        ],
        "claude_code.api_error": [
            "session.id", "user.id", "event.timestamp", "error"
        ],
    }

    # Valid values for categorical fields
    VALID_VALUES = {
        "decision": {"accept", "reject"},
        "success": {"true", "false", True, False},
    }

    def __init__(self, skip_invalid: bool = True):
        """
        Initialize validator.

        Args:
            skip_invalid: If True, skip invalid records; if False, raise errors
        """
        self.skip_invalid = skip_invalid
        self.stats = ValidationStats()

    def validate_event(self, event: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single telemetry event.

        Args:
            event: Event dictionary with body, attributes, resource, scope

        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        self.stats.total_records += 1

        # Check event structure
        if "body" not in event:
            result.add_error("Missing 'body' field")
            self._record_error("missing_body")
            return result

        body = event["body"]
        attrs = event.get("attributes", {})

        # Check required fields
        required = self.REQUIRED_FIELDS.get(body, [])
        for field_name in required:
            if field_name not in attrs:
                result.add_error(f"Missing required field: {field_name}")
                self._record_error(f"missing_{field_name}")

        # Validate specific fields
        self._validate_timestamp(attrs.get("event.timestamp"), result)
        self._validate_numeric_fields(attrs, body, result)
        self._validate_categorical_fields(attrs, result)

        # Update stats
        if result.is_valid:
            self.stats.valid_records += 1
        else:
            self.stats.invalid_records += 1

        if result.warnings:
            self.stats.warnings_count += len(result.warnings)

        return result

    def _validate_timestamp(
        self,
        timestamp: Optional[str],
        result: ValidationResult
    ) -> None:
        """Validate timestamp format."""
        if not timestamp:
            return

        try:
            # Expected format: 2025-01-01T12:34:56.123Z
            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            result.add_warning(f"Non-standard timestamp format: {timestamp}")

    def _validate_numeric_fields(
        self,
        attrs: Dict[str, Any],
        body: str,
        result: ValidationResult
    ) -> None:
        """Validate numeric fields are valid numbers."""
        numeric_fields = {
            "input_tokens", "output_tokens", "cache_creation_tokens",
            "cache_read_tokens", "duration_ms", "cost_usd", "prompt_length",
            "attempt", "tool_result_size_bytes"
        }

        for field_name in numeric_fields:
            if field_name in attrs:
                value = attrs[field_name]
                try:
                    num = float(value)
                    if num < 0 and field_name not in ("cost_usd",):
                        result.add_warning(f"Negative value for {field_name}: {value}")
                except (ValueError, TypeError):
                    result.add_error(f"Invalid numeric value for {field_name}: {value}")
                    self._record_error(f"invalid_{field_name}")

    def _validate_categorical_fields(
        self,
        attrs: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate categorical fields have valid values."""
        for field_name, valid_values in self.VALID_VALUES.items():
            if field_name in attrs:
                value = attrs[field_name]
                if value not in valid_values:
                    result.add_warning(
                        f"Unexpected value for {field_name}: {value}"
                    )

    def _record_error(self, error_type: str) -> None:
        """Record an error type for statistics."""
        self.stats.errors_by_type[error_type] = \
            self.stats.errors_by_type.get(error_type, 0) + 1

    def get_stats(self) -> ValidationStats:
        """Get validation statistics."""
        return self.stats

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.stats = ValidationStats()

    def log_summary(self) -> None:
        """Log validation summary."""
        logger.info(f"Validation Summary:")
        logger.info(f"  Total records: {self.stats.total_records:,}")
        logger.info(f"  Valid records: {self.stats.valid_records:,}")
        logger.info(f"  Invalid records: {self.stats.invalid_records:,}")
        logger.info(f"  Validity rate: {self.stats.validity_rate:.2%}")

        if self.stats.errors_by_type:
            logger.info("  Errors by type:")
            for error_type, count in sorted(
                self.stats.errors_by_type.items(),
                key=lambda x: -x[1]
            ):
                logger.info(f"    {error_type}: {count:,}")
