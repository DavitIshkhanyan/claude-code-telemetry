#!/usr/bin/env python3
"""Quick test script to verify the analytics platform works."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage import get_database
from src.analytics import AnalyticsEngine

def main():
    print("Testing Claude Code Analytics Platform...")
    print("=" * 50)

    # Get database
    db = get_database()
    print(f"✓ Database connected")

    # Get table stats
    stats = db.get_table_stats()
    print(f"\nTable Statistics:")
    for table, count in stats.items():
        print(f"  {table}: {count:,} rows")

    # Test analytics engine
    engine = AnalyticsEngine(db)

    # Get overview metrics
    metrics = engine.get_overview_metrics()
    print(f"\nOverview Metrics:")
    print(f"  Total tokens: {metrics.get('total_tokens', 0):,}")
    print(f"  Total cost: ${metrics.get('total_cost_usd', 0):,.2f}")
    print(f"  Total requests: {metrics.get('total_requests', 0):,}")
    print(f"  Unique users: {metrics.get('unique_users', 0):,}")

    # Get tokens by practice
    practice_df = engine.get_tokens_by_practice()
    print(f"\nTokens by Practice:")
    if not practice_df.empty:
        for _, row in practice_df.iterrows():
            print(f"  {row['practice']}: {row['total_tokens']:,.0f} tokens")

    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("\nTo launch the dashboard, run:")
    print("  ./venv/bin/streamlit run src/dashboard/app.py")

if __name__ == "__main__":
    main()
