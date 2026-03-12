"""
Metrics computation module.

Provides helper functions for computing derived metrics and aggregations.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import date

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def compute_token_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute token-related metrics from API requests DataFrame.

    Args:
        df: DataFrame with input_tokens, output_tokens, cost_usd columns

    Returns:
        Dictionary with computed metrics
    """
    if df.empty:
        return {
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "avg_tokens_per_request": 0,
            "total_cost": 0,
            "avg_cost_per_request": 0,
        }

    total_input = df["input_tokens"].sum()
    total_output = df["output_tokens"].sum()
    total_tokens = total_input + total_output
    total_cost = df["cost_usd"].sum()
    num_requests = len(df)

    return {
        "total_tokens": int(total_tokens),
        "total_input_tokens": int(total_input),
        "total_output_tokens": int(total_output),
        "avg_tokens_per_request": total_tokens / num_requests if num_requests > 0 else 0,
        "total_cost": float(total_cost),
        "avg_cost_per_request": total_cost / num_requests if num_requests > 0 else 0,
        "input_output_ratio": total_input / total_output if total_output > 0 else 0,
    }


def compute_session_metrics(sessions_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute session-related metrics.

    Args:
        sessions_df: DataFrame with started_at, ended_at, event_count columns

    Returns:
        Dictionary with session metrics
    """
    if sessions_df.empty:
        return {
            "total_sessions": 0,
            "avg_events_per_session": 0,
            "avg_duration_minutes": 0,
            "median_duration_minutes": 0,
        }

    df = sessions_df.copy()

    # Calculate duration
    if "started_at" in df.columns and "ended_at" in df.columns:
        df["started_at"] = pd.to_datetime(df["started_at"])
        df["ended_at"] = pd.to_datetime(df["ended_at"])
        df["duration_seconds"] = (df["ended_at"] - df["started_at"]).dt.total_seconds()
        df = df[df["duration_seconds"] > 0]  # Filter invalid durations

        avg_duration = df["duration_seconds"].mean() / 60 if not df.empty else 0
        median_duration = df["duration_seconds"].median() / 60 if not df.empty else 0
    else:
        avg_duration = 0
        median_duration = 0

    return {
        "total_sessions": len(sessions_df),
        "avg_events_per_session": df["event_count"].mean() if "event_count" in df.columns else 0,
        "avg_duration_minutes": avg_duration,
        "median_duration_minutes": median_duration,
    }


def compute_tool_metrics(
    decisions_df: pd.DataFrame,
    results_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compute tool-related metrics.

    Args:
        decisions_df: DataFrame with tool_name, decision columns
        results_df: DataFrame with tool_name, success, duration_ms columns

    Returns:
        Dictionary with tool metrics
    """
    metrics = {
        "total_tool_decisions": len(decisions_df),
        "total_tool_executions": len(results_df),
        "overall_accept_rate": 0,
        "overall_success_rate": 0,
        "avg_tool_duration_ms": 0,
    }

    if not decisions_df.empty and "decision" in decisions_df.columns:
        accept_count = (decisions_df["decision"] == "accept").sum()
        metrics["overall_accept_rate"] = accept_count / len(decisions_df)

    if not results_df.empty:
        if "success" in results_df.columns:
            success_count = results_df["success"].sum()
            metrics["overall_success_rate"] = success_count / len(results_df)

        if "duration_ms" in results_df.columns:
            metrics["avg_tool_duration_ms"] = results_df["duration_ms"].mean()

    return metrics


def compute_percentiles(
    series: pd.Series,
    percentiles: list = [50, 75, 90, 95, 99]
) -> Dict[str, float]:
    """
    Compute percentile values for a series.

    Args:
        series: Pandas Series of numeric values
        percentiles: List of percentile values to compute

    Returns:
        Dictionary mapping percentile names to values
    """
    if series.empty:
        return {f"p{p}": 0 for p in percentiles}

    values = np.percentile(series.dropna(), percentiles)
    return {f"p{p}": v for p, v in zip(percentiles, values)}


def compute_growth_rate(
    current_value: float,
    previous_value: float
) -> Optional[float]:
    """
    Compute growth rate between two values.

    Returns:
        Growth rate as decimal (0.1 = 10% growth), or None if previous is 0
    """
    if previous_value == 0:
        return None
    return (current_value - previous_value) / previous_value


def compute_moving_average(
    series: pd.Series,
    window: int = 7
) -> pd.Series:
    """
    Compute moving average of a series.

    Args:
        series: Input series
        window: Window size for moving average

    Returns:
        Series with moving average values
    """
    return series.rolling(window=window, min_periods=1).mean()


def detect_anomalies(
    series: pd.Series,
    threshold_std: float = 2.5
) -> pd.Series:
    """
    Detect anomalies using standard deviation method.

    Args:
        series: Input series
        threshold_std: Number of standard deviations for anomaly threshold

    Returns:
        Boolean series indicating anomalies
    """
    if series.empty:
        return pd.Series(dtype=bool)

    mean = series.mean()
    std = series.std()

    if std == 0:
        return pd.Series(False, index=series.index)

    z_scores = np.abs((series - mean) / std)
    return z_scores > threshold_std
