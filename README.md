# Claude Code Telemetry Analytics Platform

An end-to-end analytics platform for processing, storing, and visualizing Claude Code telemetry data. This platform transforms raw event streams into actionable insights regarding developer patterns and user behavior through an interactive dashboard.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Claude Code Telemetry Platform                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Raw Data   │───▶│  Ingestion   │───▶│   Storage    │               │
│  │   (JSONL)    │    │   Pipeline   │    │   (DuckDB)   │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                             │                    │                      │
│                             ▼                    ▼                      │
│                      ┌──────────────┐    ┌──────────────┐               │
│                      │  Validation  │    │  Analytics   │               │
│                      │   & Parsing  │    │    Engine    │               │
│                      └──────────────┘    └──────────────┘               │
│                                                 │                       │
│                                                 ▼                       │
│                                          ┌──────────────┐               │
│                                          │  Streamlit   │               │
│                                          │  Dashboard   │               │
│                                          └──────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
claude_code_telemetry/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── ingestion/             # Data ingestion module
│   │   ├── __init__.py
│   │   ├── pipeline.py        # Main ingestion orchestration
│   │   ├── parser.py          # JSONL parsing
│   │   └── validators.py      # Data validation
│   ├── storage/               # Database layer
│   │   ├── __init__.py
│   │   ├── database.py        # Database connection & queries
│   │   └── schema.py          # Table definitions
│   ├── analytics/             # Analytics engine
│   │   ├── __init__.py
│   │   ├── queries.py         # Analytics queries
│   │   └── metrics.py         # Metric computations
│   └── dashboard/             # Streamlit app
│       ├── __init__.py
│       └── app.py             # Dashboard application
├── output/                    # Generated data (from generate_fake_data.py)
│   ├── telemetry_logs.jsonl
│   └── employees.csv
├── data/                      # Database files
│   └── telemetry.duckdb
├── generate_fake_data.py      # Synthetic data generator
├── run_ingestion.py           # Ingestion entry point
├── run_dashboard.py           # Dashboard entry point
├── requirements.txt           # Python dependencies
└── README.md
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Synthetic Data (if not already done)

```bash
python3 generate_fake_data.py --num-users 100 --num-sessions 5000 --days 60
```

### 3. Run Data Ingestion

```bash
python run_ingestion.py
```

This will:
- Parse the telemetry JSONL file
- Validate and clean the data
- Load into DuckDB database

### 4. Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

Or use the helper script:
```bash
python run_dashboard.py
```

Open your browser at `http://localhost:8501`

## 📊 Analytics Features

### Overview Tab
- **Key Metrics**: Total tokens, cost, requests, active users
- **Daily Trends**: Token usage and cost over time
- **Breakdowns**: By engineering practice and model

### Usage Patterns Tab
- **Peak Hours**: Request distribution by hour
- **Weekly Patterns**: Usage by day of week
- **Heatmap**: Hour × Day of week visualization
- **Daily Active Users**: User engagement over time

### User Analytics Tab
- **By Seniority Level**: Token consumption L1-L10
- **By Location**: Geographic distribution
- **Top Users**: Leaderboard by tokens/cost
- **Detailed Table**: User-level statistics

### Tool Analytics Tab
- **Tool Usage Summary**: Executions, success rates
- **Duration Analysis**: Average tool execution time
- **By Practice**: Tool preferences per team
- **Sunburst Chart**: Hierarchical view

### Performance Tab
- **Latency Trends**: API response times
- **Model Efficiency**: Cost per token, latency per token
- **Error Analysis**: Error types and rates

## 🗄️ Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `employees` | User metadata (email, practice, level, location) |
| `sessions` | Session metadata (duration, event count) |
| `api_requests` | API call details (tokens, cost, latency) |
| `tool_decisions` | Tool accept/reject decisions |
| `tool_results` | Tool execution results |
| `user_prompts` | User prompt metadata |
| `api_errors` | API error events |

### Example SQL Queries

```sql
-- Token consumption by practice
SELECT 
    e.practice,
    SUM(a.input_tokens + a.output_tokens) as total_tokens,
    SUM(a.cost_usd) as total_cost
FROM api_requests a
LEFT JOIN employees e ON a.email = e.email
GROUP BY e.practice
ORDER BY total_tokens DESC;

-- Peak usage hours
SELECT 
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as requests,
    SUM(input_tokens + output_tokens) as tokens
FROM api_requests
GROUP BY EXTRACT(HOUR FROM timestamp)
ORDER BY hour;

-- Tool success rates
SELECT 
    tool_name,
    COUNT(*) as executions,
    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
    AVG(duration_ms) as avg_duration_ms
FROM tool_results
GROUP BY tool_name
ORDER BY executions DESC;

-- Daily active users and cost
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT user_id) as active_users,
    SUM(cost_usd) as daily_cost
FROM api_requests
GROUP BY DATE(timestamp)
ORDER BY date;
```

## 🔧 Configuration

Configuration is managed in `src/config.py`:

```python
from src.config import get_config

config = get_config()

# Database settings
config.database.db_path  # Path to DuckDB file

# Ingestion settings
config.ingestion.batch_size  # Batch size for inserts
config.ingestion.skip_invalid_records  # Skip or fail on errors

# Analytics settings
config.analytics.cache_ttl_seconds  # Query cache TTL
```

## 🎯 Key Insights Available

1. **Token Consumption Patterns**
   - Which practices consume the most tokens?
   - How does usage vary by seniority level?
   - What's the input/output token ratio by model?

2. **Usage Timing**
   - When are peak usage hours?
   - How does usage vary by day of week?
   - Are there seasonal patterns?

3. **Tool Behavior**
   - Which tools are most commonly used?
   - What are the tool success/failure rates?
   - Which tools have the longest execution times?

4. **Cost Analysis**
   - Who are the top spenders?
   - What's the cost per model?
   - How does cost trend over time?

5. **Performance Metrics**
   - API latency trends
   - Error rates by type
   - Model efficiency comparisons

## 🔮 Optional Enhancements

### Anomaly Detection
The platform includes basic anomaly detection in `src/analytics/metrics.py`:

```python
from src.analytics.metrics import detect_anomalies

# Detect days with unusual token usage
anomalies = detect_anomalies(daily_tokens_series, threshold_std=2.5)
```

### Forecasting (Future Enhancement)
```python
# Using statsmodels for time series forecasting
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(daily_tokens, trend='add', periods=7)
forecast = model.fit().forecast(7)  # 7-day forecast
```

### Real-time Ingestion Design
For production real-time processing:
- Use Apache Kafka for event streaming
- Implement a Kafka consumer in the ingestion module
- Use incremental updates instead of full refreshes
- Add a message queue for buffering

### API Access (Future Enhancement)
```python
# FastAPI endpoints for programmatic access
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/metrics/tokens")
def get_token_metrics(start_date: date, end_date: date):
    return engine.get_overview_metrics(start_date, end_date)
```

## 📝 Dependencies

- **pandas** - Data manipulation
- **polars** - High-performance data processing
- **duckdb** - Embedded analytics database
- **streamlit** - Interactive dashboard
- **plotly** - Visualizations
- **sqlalchemy** - Database abstraction

## 🧪 Data Generation Options

| Flag | Default | Description |
|------|---------|-------------|
| `--num-users` | 30 | Number of engineers |
| `--num-sessions` | 500 | Total coding sessions |
| `--days` | 30 | Time span in days |
| `--output-dir` | `output` | Output directory |
| `--seed` | 42 | Random seed for reproducibility |

## 📋 Telemetry Structure

Each log record contains a batch of `logEvents`. Each event has a JSON `message` with:

- `body` — event type (api_request, tool_decision, tool_result, etc.)
- `attributes` — event-specific fields
- `scope` — instrumentation metadata
- `resource` — host/user environment info

## 📜 Notes

- All user identifiers are synthetic
- Prompt contents are redacted
- Employee emails match the telemetry data

---

Built with ❤️ for Claude Code telemetry analysis

