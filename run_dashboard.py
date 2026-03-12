#!/usr/bin/env python3
"""
Main entry point for running the Streamlit dashboard.

Usage:
    python run_dashboard.py

Or directly:
    streamlit run src/dashboard/app.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit dashboard."""
    app_path = Path(__file__).parent / "src" / "dashboard" / "app.py"

    print("=" * 60)
    print("Claude Code Telemetry - Analytics Dashboard")
    print("=" * 60)
    print(f"\nLaunching dashboard from: {app_path}")
    print("Press Ctrl+C to stop the server\n")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless=true"
    ])


if __name__ == "__main__":
    main()
