"""
Analytics query engine.

Provides high-level analytics queries for the dashboard and API.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import numpy as np

from src.storage import Database, get_database
from src.config import get_config

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Analytics engine providing pre-built queries for common insights.
    """

    def __init__(self, database: Optional[Database] = None):
        """Initialize analytics engine."""
        self.db = database or get_database()

    # ========================================================================
    # Overview Metrics
    # ========================================================================

    def get_overview_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get high-level overview metrics.

        Returns:
            Dictionary with total_tokens, total_cost, total_requests,
            unique_users, unique_sessions, etc.
        """
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            COUNT(*) as total_requests,
            SUM(input_tokens + output_tokens) as total_tokens,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(duration_ms) as avg_latency_ms,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT session_id) as unique_sessions
        FROM api_requests
        {date_filter}
        """

        result = self.db.query_df(query)

        if result.empty:
            return {}

        row = result.iloc[0]
        return {
            "total_requests": int(row["total_requests"] or 0),
            "total_tokens": int(row["total_tokens"] or 0),
            "total_input_tokens": int(row["total_input_tokens"] or 0),
            "total_output_tokens": int(row["total_output_tokens"] or 0),
            "total_cost_usd": float(row["total_cost_usd"] or 0),
            "avg_latency_ms": float(row["avg_latency_ms"] or 0),
            "unique_users": int(row["unique_users"] or 0),
            "unique_sessions": int(row["unique_sessions"] or 0),
        }

    # ========================================================================
    # Token Consumption Analytics
    # ========================================================================

    def get_tokens_by_practice(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get token consumption grouped by engineering practice.

        Returns:
            DataFrame with columns: practice, total_tokens, total_cost,
            request_count, avg_tokens_per_request
        """
        date_filter = self._build_date_filter(start_date, end_date, "a.")

        query = f"""
        SELECT 
            e.practice,
            SUM(a.input_tokens + a.output_tokens) as total_tokens,
            SUM(a.cost_usd) as total_cost,
            COUNT(*) as request_count,
            AVG(a.input_tokens + a.output_tokens) as avg_tokens_per_request
        FROM api_requests a
        LEFT JOIN employees e ON a.email = e.email
        {date_filter}
        GROUP BY e.practice
        ORDER BY total_tokens DESC
        """

        return self.db.query_df(query)

    def get_tokens_by_level(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get token consumption grouped by seniority level."""
        date_filter = self._build_date_filter(start_date, end_date, "a.")

        query = f"""
        SELECT 
            e.level,
            SUM(a.input_tokens + a.output_tokens) as total_tokens,
            SUM(a.cost_usd) as total_cost,
            COUNT(*) as request_count,
            COUNT(DISTINCT a.email) as user_count
        FROM api_requests a
        LEFT JOIN employees e ON a.email = e.email
        {date_filter}
        GROUP BY e.level
        ORDER BY e.level
        """

        return self.db.query_df(query)

    def get_tokens_by_location(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get token consumption grouped by location."""
        date_filter = self._build_date_filter(start_date, end_date, "a.")

        query = f"""
        SELECT 
            e.location,
            SUM(a.input_tokens + a.output_tokens) as total_tokens,
            SUM(a.cost_usd) as total_cost,
            COUNT(*) as request_count,
            COUNT(DISTINCT a.email) as user_count
        FROM api_requests a
        LEFT JOIN employees e ON a.email = e.email
        {date_filter}
        GROUP BY e.location
        ORDER BY total_tokens DESC
        """

        return self.db.query_df(query)

    def get_tokens_by_model(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get token consumption grouped by model."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            model,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(input_tokens + output_tokens) as total_tokens,
            SUM(cost_usd) as total_cost,
            COUNT(*) as request_count,
            AVG(duration_ms) as avg_latency_ms
        FROM api_requests
        {date_filter}
        GROUP BY model
        ORDER BY total_tokens DESC
        """

        return self.db.query_df(query)

    def get_daily_token_usage(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get daily token usage time series."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            DATE(timestamp) as date,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(input_tokens + output_tokens) as total_tokens,
            SUM(cost_usd) as total_cost,
            COUNT(*) as request_count,
            COUNT(DISTINCT user_id) as active_users,
            AVG(duration_ms) as avg_latency_ms
        FROM api_requests
        {date_filter}
        GROUP BY DATE(timestamp)
        ORDER BY date
        """

        df = self.db.query_df(query)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def get_hourly_usage_pattern(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get usage pattern by hour of day."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            EXTRACT(HOUR FROM timestamp) as hour,
            COUNT(*) as request_count,
            SUM(input_tokens + output_tokens) as total_tokens,
            AVG(duration_ms) as avg_latency_ms
        FROM api_requests
        {date_filter}
        GROUP BY EXTRACT(HOUR FROM timestamp)
        ORDER BY hour
        """

        return self.db.query_df(query)

    def get_weekday_usage_pattern(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get usage pattern by day of week."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            EXTRACT(DOW FROM timestamp) as day_of_week,
            COUNT(*) as request_count,
            SUM(input_tokens + output_tokens) as total_tokens,
            SUM(cost_usd) as total_cost
        FROM api_requests
        {date_filter}
        GROUP BY EXTRACT(DOW FROM timestamp)
        ORDER BY day_of_week
        """

        df = self.db.query_df(query)

        # Map day numbers to names
        day_names = {
            0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
            4: "Thursday", 5: "Friday", 6: "Saturday"
        }
        if not df.empty:
            df["day_name"] = df["day_of_week"].map(day_names)

        return df

    def get_usage_heatmap(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get usage heatmap data (hour x day of week)."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            EXTRACT(DOW FROM timestamp) as day_of_week,
            EXTRACT(HOUR FROM timestamp) as hour,
            COUNT(*) as request_count,
            SUM(input_tokens + output_tokens) as total_tokens
        FROM api_requests
        {date_filter}
        GROUP BY EXTRACT(DOW FROM timestamp), EXTRACT(HOUR FROM timestamp)
        ORDER BY day_of_week, hour
        """

        return self.db.query_df(query)

    # ========================================================================
    # Session Analytics
    # ========================================================================

    def get_session_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get session duration and activity statistics."""
        date_filter = self._build_date_filter(start_date, end_date, prefix="",
                                              date_col="started_at")

        query = f"""
        SELECT 
            COUNT(*) as total_sessions,
            AVG(event_count) as avg_events_per_session,
            AVG(EXTRACT(EPOCH FROM (ended_at - started_at))) as avg_duration_seconds,
            MAX(EXTRACT(EPOCH FROM (ended_at - started_at))) as max_duration_seconds,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY event_count) as median_events
        FROM sessions
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL
        {date_filter.replace('WHERE', 'AND') if date_filter else ''}
        """

        result = self.db.query_df(query)

        if result.empty:
            return {}

        row = result.iloc[0]
        return {
            "total_sessions": int(row["total_sessions"] or 0),
            "avg_events_per_session": float(row["avg_events_per_session"] or 0),
            "avg_duration_minutes": float(row["avg_duration_seconds"] or 0) / 60,
            "max_duration_minutes": float(row["max_duration_seconds"] or 0) / 60,
            "median_events": float(row["median_events"] or 0),
        }

    def get_sessions_per_user(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 20
    ) -> pd.DataFrame:
        """Get session counts per user."""
        date_filter = self._build_date_filter(start_date, end_date, prefix="s.",
                                              date_col="started_at")

        query = f"""
        SELECT 
            e.email,
            e.full_name,
            e.practice,
            e.level,
            COUNT(s.session_id) as session_count,
            SUM(s.event_count) as total_events
        FROM sessions s
        LEFT JOIN employees e ON s.email = e.email
        {date_filter}
        GROUP BY e.email, e.full_name, e.practice, e.level
        ORDER BY session_count DESC
        LIMIT {top_n}
        """

        return self.db.query_df(query)

    # ========================================================================
    # Tool Analytics
    # ========================================================================

    def get_tool_usage_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get comprehensive tool usage statistics."""
        date_filter_d = self._build_date_filter(start_date, end_date, "d.")
        date_filter_r = self._build_date_filter(start_date, end_date, "r.")

        # Tool decisions
        decisions_query = f"""
        SELECT 
            tool_name,
            COUNT(*) as total_decisions,
            SUM(CASE WHEN decision = 'accept' THEN 1 ELSE 0 END) as accepts,
            SUM(CASE WHEN decision = 'reject' THEN 1 ELSE 0 END) as rejects
        FROM tool_decisions d
        {date_filter_d}
        GROUP BY tool_name
        """

        # Tool results
        results_query = f"""
        SELECT 
            tool_name,
            COUNT(*) as total_executions,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
            AVG(duration_ms) as avg_duration_ms,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms
        FROM tool_results r
        {date_filter_r}
        GROUP BY tool_name
        """

        decisions_df = self.db.query_df(decisions_query)
        results_df = self.db.query_df(results_query)

        # Merge
        if decisions_df.empty and results_df.empty:
            return pd.DataFrame()

        if decisions_df.empty:
            merged = results_df
        elif results_df.empty:
            merged = decisions_df
        else:
            merged = pd.merge(
                decisions_df, results_df,
                on="tool_name", how="outer"
            )

        # Calculate rates
        if "total_decisions" in merged.columns and "accepts" in merged.columns:
            merged["accept_rate"] = merged["accepts"] / merged["total_decisions"]

        if "total_executions" in merged.columns and "successes" in merged.columns:
            merged["success_rate"] = merged["successes"] / merged["total_executions"]

        return merged.sort_values("total_executions", ascending=False, na_position="last")

    def get_tool_usage_by_practice(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get tool usage breakdown by practice."""
        date_filter = self._build_date_filter(start_date, end_date, "r.")

        query = f"""
        SELECT 
            e.practice,
            r.tool_name,
            COUNT(*) as usage_count,
            AVG(r.duration_ms) as avg_duration_ms
        FROM tool_results r
        LEFT JOIN employees e ON r.email = e.email
        {date_filter}
        GROUP BY e.practice, r.tool_name
        ORDER BY e.practice, usage_count DESC
        """

        return self.db.query_df(query)

    # ========================================================================
    # Top Users / Leaderboards
    # ========================================================================

    def get_top_users_by_tokens(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 10
    ) -> pd.DataFrame:
        """Get top users by token consumption."""
        date_filter = self._build_date_filter(start_date, end_date, "a.")

        query = f"""
        SELECT 
            e.email,
            e.full_name,
            e.practice,
            e.level,
            e.location,
            SUM(a.input_tokens + a.output_tokens) as total_tokens,
            SUM(a.cost_usd) as total_cost,
            COUNT(*) as request_count,
            COUNT(DISTINCT a.session_id) as session_count
        FROM api_requests a
        LEFT JOIN employees e ON a.email = e.email
        {date_filter}
        GROUP BY e.email, e.full_name, e.practice, e.level, e.location
        ORDER BY total_tokens DESC
        LIMIT {top_n}
        """

        return self.db.query_df(query)

    def get_top_users_by_cost(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 10
    ) -> pd.DataFrame:
        """Get top users by cost."""
        date_filter = self._build_date_filter(start_date, end_date, "a.")

        query = f"""
        SELECT 
            e.email,
            e.full_name,
            e.practice,
            e.level,
            SUM(a.cost_usd) as total_cost,
            SUM(a.input_tokens + a.output_tokens) as total_tokens,
            COUNT(*) as request_count
        FROM api_requests a
        LEFT JOIN employees e ON a.email = e.email
        {date_filter}
        GROUP BY e.email, e.full_name, e.practice, e.level
        ORDER BY total_cost DESC
        LIMIT {top_n}
        """

        return self.db.query_df(query)

    # ========================================================================
    # Efficiency Metrics
    # ========================================================================

    def get_token_efficiency_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get token efficiency metrics (tokens per request, cost per token)."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            model,
            COUNT(*) as request_count,
            AVG(input_tokens + output_tokens) as avg_tokens_per_request,
            AVG(cost_usd) as avg_cost_per_request,
            SUM(cost_usd) / NULLIF(SUM(input_tokens + output_tokens), 0) * 1000 as cost_per_1k_tokens,
            AVG(output_tokens::FLOAT / NULLIF(input_tokens, 0)) as output_input_ratio,
            AVG(duration_ms::FLOAT / NULLIF(output_tokens, 0)) as ms_per_output_token
        FROM api_requests
        {date_filter}
        GROUP BY model
        ORDER BY request_count DESC
        """

        return self.db.query_df(query)

    # ========================================================================
    # Error Analytics
    # ========================================================================

    def get_error_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get API error summary."""
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT 
            status_code,
            error_message,
            COUNT(*) as error_count,
            COUNT(DISTINCT session_id) as affected_sessions
        FROM api_errors
        {date_filter}
        GROUP BY status_code, error_message
        ORDER BY error_count DESC
        """

        return self.db.query_df(query)

    def get_error_rate_by_day(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get daily error rates."""
        date_filter_req = self._build_date_filter(start_date, end_date)
        date_filter_err = self._build_date_filter(start_date, end_date)

        query = f"""
        WITH daily_requests AS (
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as request_count
            FROM api_requests
            {date_filter_req}
            GROUP BY DATE(timestamp)
        ),
        daily_errors AS (
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as error_count
            FROM api_errors
            {date_filter_err}
            GROUP BY DATE(timestamp)
        )
        SELECT 
            r.date,
            r.request_count,
            COALESCE(e.error_count, 0) as error_count,
            COALESCE(e.error_count, 0)::FLOAT / r.request_count as error_rate
        FROM daily_requests r
        LEFT JOIN daily_errors e ON r.date = e.date
        ORDER BY r.date
        """

        df = self.db.query_df(query)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # ========================================================================
    # Date Range Info
    # ========================================================================

    def get_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """Get the date range of available data."""
        query = """
        SELECT 
            MIN(DATE(timestamp)) as min_date,
            MAX(DATE(timestamp)) as max_date
        FROM api_requests
        """

        result = self.db.query_df(query)

        if result.empty:
            return None, None

        row = result.iloc[0]
        min_date = row["min_date"]
        max_date = row["max_date"]

        if pd.isna(min_date) or pd.isna(max_date):
            return None, None

        return (
            pd.to_datetime(min_date).date(),
            pd.to_datetime(max_date).date()
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _build_date_filter(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        prefix: str = "",
        date_col: str = "timestamp"
    ) -> str:
        """Build SQL WHERE clause for date filtering."""
        conditions = []

        col = f"{prefix}{date_col}" if prefix else date_col

        if start_date:
            conditions.append(f"DATE({col}) >= '{start_date}'")
        if end_date:
            conditions.append(f"DATE({col}) <= '{end_date}'")

        if conditions:
            return "WHERE " + " AND ".join(conditions)
        return ""
