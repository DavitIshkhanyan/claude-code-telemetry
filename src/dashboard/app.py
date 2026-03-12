"""
Streamlit dashboard for Claude Code Telemetry Analytics.

Interactive dashboard providing insights into token usage, user behavior,
tool usage patterns, and system performance.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage import get_database
from src.analytics import AnalyticsEngine


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Claude Code Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stMetric {
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Initialize Analytics Engine
# ============================================================================

@st.cache_resource
def get_analytics_engine():
    """Get cached analytics engine instance."""
    db = get_database()
    return AnalyticsEngine(db)


def create_app():
    """Main dashboard application."""

    # Initialize
    engine = get_analytics_engine()

    # Get date range
    min_date, max_date = engine.get_date_range()

    if min_date is None or max_date is None:
        st.error("⚠️ No data found in database. Please run the ingestion pipeline first.")
        st.code("python -m src.ingestion.pipeline", language="bash")
        st.stop()

    # ========================================================================
    # Sidebar - Filters
    # ========================================================================

    with st.sidebar:
        st.image("https://www.anthropic.com/images/icons/apple-touch-icon.png", width=50)
        st.title("🔍 Filters")

        # Date range filter
        st.subheader("Date Range")
        date_range = st.date_input(
            "Select dates",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date

        st.divider()

        # Quick date ranges
        st.subheader("Quick Select")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Last 7 days"):
                start_date = max_date - timedelta(days=7)
                end_date = max_date
        with col2:
            if st.button("Last 30 days"):
                start_date = max_date - timedelta(days=30)
                end_date = max_date

        st.divider()

        # Data info
        st.subheader("📊 Data Info")
        st.caption(f"Data range: {min_date} to {max_date}")

        db_stats = get_database().get_table_stats()
        st.caption(f"API Requests: {db_stats.get('api_requests', 0):,}")
        st.caption(f"Sessions: {db_stats.get('sessions', 0):,}")
        st.caption(f"Employees: {db_stats.get('employees', 0):,}")

    # ========================================================================
    # Main Content
    # ========================================================================

    # Header
    st.markdown('<p class="main-header">📊 Claude Code Usage Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time insights into Claude Code telemetry data</p>', unsafe_allow_html=True)

    # Tabs
    tab_overview, tab_usage, tab_users, tab_tools, tab_performance = st.tabs([
        "📈 Overview",
        "⏰ Usage Patterns",
        "👥 User Analytics",
        "🔧 Tool Analytics",
        "⚡ Performance"
    ])

    # ========================================================================
    # Tab 1: Overview
    # ========================================================================

    with tab_overview:
        render_overview_tab(engine, start_date, end_date)

    # ========================================================================
    # Tab 2: Usage Patterns
    # ========================================================================

    with tab_usage:
        render_usage_patterns_tab(engine, start_date, end_date)

    # ========================================================================
    # Tab 3: User Analytics
    # ========================================================================

    with tab_users:
        render_user_analytics_tab(engine, start_date, end_date)

    # ========================================================================
    # Tab 4: Tool Analytics
    # ========================================================================

    with tab_tools:
        render_tool_analytics_tab(engine, start_date, end_date)

    # ========================================================================
    # Tab 5: Performance
    # ========================================================================

    with tab_performance:
        render_performance_tab(engine, start_date, end_date)


# ============================================================================
# Tab Renderers
# ============================================================================

def render_overview_tab(engine: AnalyticsEngine, start_date: date, end_date: date):
    """Render the overview tab."""

    # Key Metrics
    metrics = engine.get_overview_metrics(start_date, end_date)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Tokens",
            f"{metrics.get('total_tokens', 0):,.0f}",
            help="Total input + output tokens",
            border=True
        )

    with col2:
        st.metric(
            "Total Cost",
            f"${metrics.get('total_cost_usd', 0):,.2f}",
            help="Total API cost in USD",
            border=True
        )

    with col3:
        st.metric(
            "API Requests",
            f"{metrics.get('total_requests', 0):,}",
            help="Total API requests",
            border=True
        )

    with col4:
        st.metric(
            "Active Users",
            f"{metrics.get('unique_users', 0):,}",
            help="Unique users",
            border=True
        )

    st.divider()

    # Daily trends
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Daily Token Usage")
        daily_df = engine.get_daily_token_usage(start_date, end_date)

        if not daily_df.empty:
            fig = px.area(
                daily_df,
                x="date",
                y=["input_tokens", "output_tokens"],
                title="",
                labels={"value": "Tokens", "date": "Date", "variable": "Type"},
                color_discrete_map={
                    "input_tokens": "#667eea",
                    "output_tokens": "#764ba2"
                }
            )
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("💰 Daily Cost")
        if not daily_df.empty:
            fig = px.line(
                daily_df,
                x="date",
                y="total_cost",
                title="",
                labels={"total_cost": "Cost (USD)", "date": "Date"}
            )
            fig.update_traces(
                line_color="#10b981",
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.1)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    # Breakdown charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Tokens by Practice")
        practice_df = engine.get_tokens_by_practice(start_date, end_date)

        if not practice_df.empty:
            fig = px.pie(
                practice_df,
                values="total_tokens",
                names="practice",
                title="",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("🤖 Tokens by Model")
        model_df = engine.get_tokens_by_model(start_date, end_date)

        if not model_df.empty:
            fig = px.bar(
                model_df,
                x="model",
                y="total_tokens",
                title="",
                color="total_cost",
                color_continuous_scale="Viridis",
                labels={"total_tokens": "Total Tokens", "model": "Model"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")


def render_usage_patterns_tab(engine: AnalyticsEngine, start_date: date, end_date: date):
    """Render the usage patterns tab."""

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⏰ Peak Usage Hours")
        hourly_df = engine.get_hourly_usage_pattern(start_date, end_date)

        if not hourly_df.empty:
            fig = px.bar(
                hourly_df,
                x="hour",
                y="request_count",
                title="",
                labels={"request_count": "Requests", "hour": "Hour of Day"},
                color="total_tokens",
                color_continuous_scale="Blues"
            )
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("📅 Usage by Day of Week")
        weekday_df = engine.get_weekday_usage_pattern(start_date, end_date)

        if not weekday_df.empty and "day_name" in weekday_df.columns:
            # Reorder days
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_df["day_name"] = pd.Categorical(
                weekday_df["day_name"],
                categories=day_order,
                ordered=True
            )
            weekday_df = weekday_df.sort_values("day_name")

            fig = px.bar(
                weekday_df,
                x="day_name",
                y="request_count",
                title="",
                labels={"request_count": "Requests", "day_name": "Day"},
                color="total_tokens",
                color_continuous_scale="Greens"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    # Heatmap
    st.subheader("🗓️ Usage Heatmap (Hour × Day of Week)")
    heatmap_df = engine.get_usage_heatmap(start_date, end_date)

    if not heatmap_df.empty:
        # Pivot for heatmap
        pivot_df = heatmap_df.pivot(
            index="day_of_week",
            columns="hour",
            values="request_count"
        ).fillna(0)

        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=[f"{h:02d}:00" for h in range(24)],
            y=[day_names[int(i)] for i in pivot_df.index],
            colorscale="YlOrRd",
            hoverongaps=False
        ))
        fig.update_layout(
            xaxis_title="Hour",
            yaxis_title="Day of Week",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for heatmap")

    # Daily active users
    st.subheader("👥 Daily Active Users")
    daily_df = engine.get_daily_token_usage(start_date, end_date)

    if not daily_df.empty and "active_users" in daily_df.columns:
        fig = px.line(
            daily_df,
            x="date",
            y="active_users",
            title="",
            labels={"active_users": "Active Users", "date": "Date"}
        )
        fig.update_traces(
            line_color="#f59e0b",
            mode="lines+markers"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_user_analytics_tab(engine: AnalyticsEngine, start_date: date, end_date: date):
    """Render the user analytics tab."""

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Tokens by Seniority Level")
        level_df = engine.get_tokens_by_level(start_date, end_date)

        if not level_df.empty:
            # Sort levels properly
            level_order = [f"L{i}" for i in range(1, 11)]
            level_df["level"] = pd.Categorical(
                level_df["level"],
                categories=level_order,
                ordered=True
            )
            level_df = level_df.sort_values("level")

            fig = px.bar(
                level_df,
                x="level",
                y="total_tokens",
                title="",
                labels={"total_tokens": "Total Tokens", "level": "Level"},
                color="user_count",
                color_continuous_scale="Purples",
                text="user_count"
            )
            fig.update_traces(texttemplate="%{text} users", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("🌍 Tokens by Location")
        location_df = engine.get_tokens_by_location(start_date, end_date)

        if not location_df.empty:
            fig = px.bar(
                location_df,
                x="location",
                y="total_tokens",
                title="",
                labels={"total_tokens": "Total Tokens", "location": "Location"},
                color="total_cost",
                color_continuous_scale="Teal"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    # Top users
    st.subheader("🏆 Top Users by Token Consumption")
    top_users_df = engine.get_top_users_by_tokens(start_date, end_date, top_n=15)

    if not top_users_df.empty:
        fig = px.bar(
            top_users_df,
            x="total_tokens",
            y="full_name",
            orientation="h",
            title="",
            color="practice",
            labels={"total_tokens": "Total Tokens", "full_name": "User"},
            text="total_tokens"
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

    # User table
    st.subheader("📋 User Details")
    if not top_users_df.empty:
        display_df = top_users_df[[
            "full_name", "practice", "level", "location",
            "total_tokens", "total_cost", "request_count", "session_count"
        ]].copy()
        display_df.columns = [
            "Name", "Practice", "Level", "Location",
            "Tokens", "Cost ($)", "Requests", "Sessions"
        ]
        display_df["Cost ($)"] = display_df["Cost ($)"].apply(lambda x: f"${x:,.2f}")
        display_df["Tokens"] = display_df["Tokens"].apply(lambda x: f"{x:,.0f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_tool_analytics_tab(engine: AnalyticsEngine, start_date: date, end_date: date):
    """Render the tool analytics tab."""

    # Tool usage summary
    st.subheader("🔧 Tool Usage Summary")
    tools_df = engine.get_tool_usage_summary(start_date, end_date)

    if not tools_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Tool usage chart
            if "total_executions" in tools_df.columns:
                fig = px.bar(
                    tools_df.head(15),
                    x="tool_name",
                    y="total_executions",
                    title="Tool Executions",
                    color="success_rate" if "success_rate" in tools_df.columns else None,
                    color_continuous_scale="RdYlGn",
                    labels={"total_executions": "Executions", "tool_name": "Tool"}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Success rate chart
            if "success_rate" in tools_df.columns:
                fig = px.bar(
                    tools_df.head(15),
                    x="tool_name",
                    y="success_rate",
                    title="Tool Success Rate",
                    color="success_rate",
                    color_continuous_scale="RdYlGn",
                    labels={"success_rate": "Success Rate", "tool_name": "Tool"}
                )
                fig.update_xaxes(tickangle=45)
                fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)

        # Tool duration
        st.subheader("⏱️ Tool Duration Distribution")
        if "avg_duration_ms" in tools_df.columns:
            fig = px.bar(
                tools_df.sort_values("avg_duration_ms", ascending=False).head(15),
                x="tool_name",
                y="avg_duration_ms",
                title="",
                labels={"avg_duration_ms": "Avg Duration (ms)", "tool_name": "Tool"},
                color="avg_duration_ms",
                color_continuous_scale="Oranges"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Tool table
        st.subheader("📋 Tool Statistics")
        display_cols = ["tool_name"]
        if "total_executions" in tools_df.columns:
            display_cols.append("total_executions")
        if "success_rate" in tools_df.columns:
            display_cols.append("success_rate")
        if "accept_rate" in tools_df.columns:
            display_cols.append("accept_rate")
        if "avg_duration_ms" in tools_df.columns:
            display_cols.append("avg_duration_ms")

        display_df = tools_df[display_cols].copy()

        # Format percentages
        for col in ["success_rate", "accept_rate"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
                )

        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No tool data available")

    # Tool usage by practice
    st.subheader("🏢 Tool Usage by Practice")
    practice_tools = engine.get_tool_usage_by_practice(start_date, end_date)

    if not practice_tools.empty:
        fig = px.sunburst(
            practice_tools,
            path=["practice", "tool_name"],
            values="usage_count",
            title="",
            color="avg_duration_ms",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_performance_tab(engine: AnalyticsEngine, start_date: date, end_date: date):
    """Render the performance tab."""

    # Latency trends
    st.subheader("⚡ API Latency Trends")
    daily_df = engine.get_daily_token_usage(start_date, end_date)

    if not daily_df.empty and "avg_latency_ms" in daily_df.columns:
        fig = px.line(
            daily_df,
            x="date",
            y="avg_latency_ms",
            title="",
            labels={"avg_latency_ms": "Avg Latency (ms)", "date": "Date"}
        )
        fig.update_traces(line_color="#ef4444")
        st.plotly_chart(fig, use_container_width=True)

    # Model efficiency
    st.subheader("📊 Model Efficiency Metrics")
    efficiency_df = engine.get_token_efficiency_metrics(start_date, end_date)

    if not efficiency_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            if "cost_per_1k_tokens" in efficiency_df.columns:
                fig = px.bar(
                    efficiency_df,
                    x="model",
                    y="cost_per_1k_tokens",
                    title="Cost per 1K Tokens",
                    color="cost_per_1k_tokens",
                    color_continuous_scale="Reds",
                    labels={"cost_per_1k_tokens": "Cost ($)", "model": "Model"}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "ms_per_output_token" in efficiency_df.columns:
                fig = px.bar(
                    efficiency_df,
                    x="model",
                    y="ms_per_output_token",
                    title="Latency per Output Token",
                    color="ms_per_output_token",
                    color_continuous_scale="Blues",
                    labels={"ms_per_output_token": "ms/token", "model": "Model"}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        # Efficiency table
        st.dataframe(efficiency_df, use_container_width=True, hide_index=True)

    # Error analysis
    st.subheader("❌ Error Analysis")

    col1, col2 = st.columns(2)

    with col1:
        error_df = engine.get_error_summary(start_date, end_date)
        if not error_df.empty:
            st.dataframe(error_df, use_container_width=True, hide_index=True)
        else:
            st.success("No errors recorded! 🎉")

    with col2:
        error_rate_df = engine.get_error_rate_by_day(start_date, end_date)
        if not error_rate_df.empty and "error_rate" in error_rate_df.columns:
            fig = px.line(
                error_rate_df,
                x="date",
                y="error_rate",
                title="Daily Error Rate",
                labels={"error_rate": "Error Rate", "date": "Date"}
            )
            fig.update_traces(line_color="#ef4444")
            fig.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    create_app()
