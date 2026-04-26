
# JobSentinel Feature Enhancements

## Multi-Agent AI System ✅

JobSentinel now uses specialized AI agents for intelligent job evaluation and application decisions.

### Agents

1. **JobEvaluatorAgent** - Evaluates job-candidate match with detailed reasoning
2. **ApplicationAgent** - Plans optimal application strategy
3. **ReviewAgent** - Analyzes borderline cases for human review
4. **StrategyAgent** - Prioritizes batches of jobs

### Configuration

Enable the multi-agent system in `configs/settings.yaml`:

```yaml
ai:
  use_llm: true
  use_agents: true
  llm_model: llama3.2:latest
```

### Usage

The agents work automatically when enabled. Each job gets:
- Detailed evaluation with reasoning
- Confidence score
- Application strategy recommendation
- Priority ranking

### Example Output

```python
{
    "decision": "APPLY",
    "score": 85,
    "confidence": 90,
    "reasoning": "Strong match with required security skills and experience level",
    "match_factors": ["Python", "Security", "Cloud"],
    "concerns": ["Salary range not specified"],
    "application_strategy": "easy_apply",
    "priority": "high"
}
```

## Upcoming Features

### Portal Scanner
Direct API integration with job boards (Greenhouse, Ashby, Lever) for zero-token job collection.

### Interview Preparation
Automated generation of STAR stories and company-specific interview prep.

### Pattern Analysis
Analyze application outcomes to identify success patterns and improve targeting.

### Follow-up Manager
Automated tracking and reminders for application follow-ups.

### Dynamic CV Generation
Generate tailored CVs optimized for each job posting.

### Batch Processing
Parallel job evaluation with concurrent workers for faster processing.
