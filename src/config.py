"""
Configuration module for the analytics platform.

Centralizes all configuration settings including paths, database connections,
and feature flags.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import logging


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    db_type: str = "duckdb"  # "duckdb" or "postgresql"
    db_path: str = "data/telemetry.duckdb"

    # PostgreSQL settings (if using PostgreSQL)
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "telemetry"
    pg_user: str = "postgres"
    pg_password: str = ""

    @property
    def connection_string(self) -> str:
        if self.db_type == "duckdb":
            return self.db_path
        else:
            return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"


@dataclass
class PathConfig:
    """File path configuration."""
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))

    def __post_init__(self):
        # Convert to absolute paths
        self.data_dir = self.base_dir / self.data_dir
        self.output_dir = self.base_dir / self.output_dir
        self.logs_dir = self.base_dir / self.logs_dir

        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def telemetry_file(self) -> Path:
        return self.output_dir / "telemetry_logs.jsonl"

    @property
    def employees_file(self) -> Path:
        return self.output_dir / "employees.csv"

    @property
    def database_file(self) -> Path:
        return self.data_dir / "telemetry.duckdb"


@dataclass
class IngestionConfig:
    """Ingestion pipeline configuration."""
    batch_size: int = 10000
    validate_schema: bool = True
    skip_invalid_records: bool = True
    max_workers: int = 4


@dataclass
class AnalyticsConfig:
    """Analytics computation configuration."""
    cache_ttl_seconds: int = 300
    enable_anomaly_detection: bool = True
    anomaly_threshold_std: float = 2.5
    forecast_horizon_days: int = 7


@dataclass
class Config:
    """Main configuration container."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    log_level: str = "INFO"

    def setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.setup_logging()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
    _config.setup_logging()
