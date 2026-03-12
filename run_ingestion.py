#!/usr/bin/env python3
"""
Main entry point for running the ingestion pipeline.

Usage:
    python run_ingestion.py [--reset]
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion import run_ingestion


def main():
    """Run the ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    reset = "--reset" in sys.argv

    print("=" * 60)
    print("Claude Code Telemetry - Data Ingestion Pipeline")
    print("=" * 60)

    results = run_ingestion(reset_db=reset)

    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print("\nRecords loaded:")
    for table, count in results.items():
        print(f"  {table}: {count:,} rows")

    print("\nNext steps:")
    print("  Run the dashboard: streamlit run src/dashboard/app.py")


if __name__ == "__main__":
    main()
