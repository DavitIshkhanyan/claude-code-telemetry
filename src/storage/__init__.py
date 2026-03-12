"""
Storage module for the analytics platform.
"""

from .schema import create_all_tables, drop_all_tables, ALL_SCHEMAS
from .database import Database, get_database

__all__ = [
    "create_all_tables",
    "drop_all_tables",
    "ALL_SCHEMAS",
    "Database",
    "get_database",
]
