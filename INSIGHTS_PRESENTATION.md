    # Claude Code Usage Analytics
## Insights Presentation

---

# Slide 1: Executive Summary

## Key Findings from 60 Days of Claude Code Telemetry

| Metric | Value |
|--------|-------|
| **Total Tokens Processed** | 103.3 Million |
| **Total API Cost** | $6,001.43 |
| **API Requests** | 118,014 |
| **Active Users** | 100 engineers |
| **Sessions** | 5,000 |

### The Story
Over 60 days, 100 engineers across 5 practices used Claude Code extensively, generating over 100M tokens. ML Engineering and Frontend Engineering teams are the heaviest users, accounting for nearly 50% of total consumption.

---

# Slide 2: Token Consumption by Practice

## Who Uses Claude Code the Most?

```
ML Engineering:       ████████████████████████  25.6M tokens (24.8%)
Frontend Engineering: ████████████████████████  25.2M tokens (24.4%)
Data Engineering:     ████████████████████      20.5M tokens (19.9%)
Backend Engineering:  ███████████████████       19.9M tokens (19.3%)
Platform Engineering: ████████████              12.1M tokens (11.7%)
```

### Insights:
- **ML & Frontend teams** consume nearly 50% of all tokens
- **Platform Engineering** uses the least - potential for increased adoption
- Token consumption correlates with team size and project complexity

### Recommendation:
Consider tiered cost allocation by practice for budget planning.

---

# Slide 3: Usage Patterns & Peak Hours

## When Do Engineers Use Claude Code?

### Peak Hours (UTC)
```
09:00 - 13:00  ████████████████████  Peak usage (70% of requests)
14:00 - 17:00  ████████████          Moderate usage
18:00 - 08:00  ████                  Low usage
```

### Weekday Distribution
- **Tuesday-Thursday**: Highest usage
- **Monday**: Ramp-up day
- **Friday**: Declining usage
- **Weekend**: Minimal activity (< 5%)

### Insights:
- Usage follows standard business hours
- 70% of requests occur during 9 AM - 1 PM window
- Engineers prefer Claude Code for focused morning work

---

# Slide 4: Tool Usage & Efficiency

## Most Used Tools

| Tool | Executions | Success Rate | Avg Duration |
|------|------------|--------------|--------------|
| **Read** | 48,234 | 98.6% | 34 ms |
| **Bash** | 44,821 | 93.3% | 5,169 ms |
| **Edit** | 20,113 | 99.0% | 1,817 ms |
| **Grep** | 11,962 | 99.0% | 474 ms |
| **Glob** | 7,384 | 99.0% | 750 ms |

### Key Observations:
- **Read & Bash** dominate tool usage (63% combined)
- **Bash** has lowest success rate - command errors
- **Edit** operations are most reliable
- **WebSearch** is rarely used but has longest duration

### Recommendation:
Provide training on Bash command best practices to improve success rate.

---

# Slide 5: Cost Analysis & Model Usage

## Model Distribution & Cost Efficiency

| Model | Requests | Cost | Cost/1K Tokens |
|-------|----------|------|----------------|
| claude-haiku-4-5 | 45,934 (39%) | $152.30 | $0.038 |
| claude-opus-4-6 | 25,780 (22%) | $1,830.42 | $0.25 |
| claude-opus-4-5 | 23,487 (20%) | $1,973.54 | $0.27 |
| claude-sonnet-4-5 | 19,673 (17%) | $1,219.95 | $0.18 |
| claude-sonnet-4-6 | 3,140 (3%) | $207.40 | $0.19 |

### Cost Optimization Insights:
- **Haiku** is most cost-efficient: 39% of requests, only 2.5% of cost
- **Opus models** drive 63% of total cost
- Users self-select appropriate models for task complexity

### Recommendation:
Encourage Haiku usage for simple tasks; reserve Opus for complex reasoning.

---

# Slide 6: Error Analysis

## API Reliability

| Error Type | Count | % of Errors |
|------------|-------|-------------|
| Request aborted | 605 | 44% |
| Rate limit (429) | 261 | 19% |
| Invalid input (400) | 137 | 10% |
| Server error (500) | 55 | 4% |
| Auth expired (401) | 27 | 2% |

### Overall Error Rate: 1.15%

### Insights:
- **98.85% success rate** - excellent reliability
- Rate limiting affects peak hours - consider request smoothing
- Auth errors indicate token refresh issues

---

# Slide 7: User Segments & Adoption

## Adoption by Seniority Level

```
L1-L3 (Junior):   ████████████████████  35% of users, 28% of tokens
L4-L6 (Mid):      ████████████████████████████  45% of users, 48% of tokens
L7-L10 (Senior):  ████████████          20% of users, 24% of tokens
```

### Power Users
Top 10% of users account for 40% of total token consumption.

### Geographic Distribution
| Location | Users | Token Share |
|----------|-------|-------------|
| Poland | 28 | 26% |
| Germany | 25 | 24% |
| United Kingdom | 22 | 23% |
| Canada | 15 | 16% |
| United States | 10 | 11% |

---

# Slide 8: Recommendations & Next Steps

## Optimization Opportunities

### 1. Cost Reduction
- Promote Haiku for simple tasks (potential 20% cost savings)
- Implement caching for repeated queries
- Set per-user daily token limits

### 2. Adoption Increase
- Target Platform Engineering team for onboarding
- Create Claude Code best practices documentation
- Share power user workflows

### 3. Performance Improvement
- Bash command validation before execution
- Token refresh automation to reduce auth errors
- Request queuing during peak hours

### 4. Monitoring
- Real-time cost alerts by practice
- Weekly usage reports to team leads
- Anomaly detection for unusual patterns

---

# Thank You

## Dashboard Access
**URL:** http://localhost:8501

## Questions?

*Built with Python, DuckDB, Streamlit, and Plotly*
*Data: 60 days, 100 users, 454K events*
