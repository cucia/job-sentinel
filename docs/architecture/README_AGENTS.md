# JobSentinel Multi-Agent AI System

## Overview

JobSentinel now includes an intelligent multi-agent AI system that replaces simple keyword-based scoring with deep reasoning and strategic decision-making.

## Architecture

```
Job Posting
    ↓
JobEvaluatorAgent
    ├─→ Analyzes match quality
    ├─→ Identifies strengths
    └─→ Detects concerns
    ↓
Decision: APPLY / REJECT / REVIEW
    ↓
ApplicationAgent
    ├─→ Plans strategy (easy_apply/manual)
    ├─→ Sets priority (high/medium/low)
    └─→ Estimates time
    ↓
ReviewAgent (if uncertain)
    ├─→ Explains why review needed
    ├─→ Suggests questions
    └─→ Provides recommendation
    ↓
StrategyAgent (for batches)
    ├─→ Prioritizes jobs
    ├─→ Optimizes order
    └─→ Maximizes success
    ↓
Final Decision + Application
```

## Agents

### 1. JobEvaluatorAgent
**Role:** Job-Candidate Match Analysis

**Evaluates:**
- Skills alignment
- Experience level fit
- Role compatibility
- Red flags

**Returns:**
```python
{
    "decision": "APPLY",
    "score": 85,
    "confidence": 90,
    "reasoning": "Strong match with required skills...",
    "match_factors": ["Python", "Security", "Remote"],
    "concerns": ["Salary not specified"]
}
```

### 2. ApplicationAgent
**Role:** Application Strategy Planning

**Determines:**
- Best application method
- Priority level
- Time investment
- Success probability

**Returns:**
```python
{
    "strategy": "easy_apply",
    "priority": "high",
    "reasoning": "Quick apply available, strong match",
    "estimated_time": "2 minutes"
}
```

### 3. ReviewAgent
**Role:** Uncertain Case Analysis

**Provides:**
- Review justification
- Decision questions
- Recommendations
- Key considerations

**Returns:**
```python
{
    "review_reason": "Partial match with unclear requirements",
    "questions": ["Is salary acceptable?", "Can you learn X?"],
    "recommendation": "Contact recruiter for clarification",
    "key_points": ["Salary unclear", "Tech stack partial match"]
}
```

### 4. StrategyAgent
**Role:** Batch Prioritization

**Optimizes:**
- Application order
- Resource allocation
- Success probability
- Time efficiency

**Returns:**
```python
[
    {"job": {...}, "priority_rank": 1, "reasoning": "..."},
    {"job": {...}, "priority_rank": 2, "reasoning": "..."},
    ...
]
```

### 5. AgentOrchestrator
**Role:** Coordination & Workflow

**Manages:**
- Agent execution order
- Data flow between agents
- Error handling
- Result aggregation

## Configuration

### Enable Agents

Edit `configs/settings.yaml`:

```yaml
ai:
  use_ai: true
  use_llm: true
  use_agents: true
  llm_model: llama3.2:latest
  min_score: 70
  uncertainty_margin: 5
```

### Operating Modes

**Simple Mode** (Fast, 0 tokens)
```yaml
use_agents: false
use_llm: false
```

**LLM Mode** (Balanced, ~500 tokens/job)
```yaml
use_agents: false
use_llm: true
```

**Multi-Agent Mode** (Intelligent, ~1500 tokens/job)
```yaml
use_agents: true
use_llm: true
```

## Usage

### Automatic (via Controller)

Agents run automatically when enabled:

```bash
python -m src.core.controller
```

Jobs are evaluated, strategies planned, and decisions made automatically.

### Manual (via Python)

```python
from src.ai.agents_wrapper import evaluate_job_with_agents
from src.core.config import load_settings, load_profile

settings = load_settings('.')
settings['ai']['use_agents'] = True
settings['ai']['use_llm'] = True
profile = load_profile('.')

job = {
    'title': 'Security Engineer',
    'company': 'TechCorp',
    'description': 'Security engineer with Python...',
    'location': 'Remote',
    'easy_apply': True
}

result = evaluate_job_with_agents(job, profile, settings)

print(f"Decision: {result['decision']}")
print(f"Score: {result['score']}/100")
print(f"Confidence: {result['confidence']}%")
print(f"Reasoning: {result['reasoning']}")
```

## Decision Examples

### APPLY Decision
```
Decision: APPLY
Score: 85/100
Confidence: 90%

Reasoning: Strong match with required security skills and Python 
experience. Remote work aligns with preferences. Company culture 
appears collaborative based on job description.

Match Factors:
- Python programming (5+ years)
- Security certifications
- Cloud experience (AWS)
- Remote work

Concerns:
- Salary range not specified

Strategy: easy_apply
Priority: high
Estimated Time: 2 minutes
```

### REJECT Decision
```
Decision: REJECT
Score: 35/100
Confidence: 95%

Reasoning: Job requires 10+ years senior-level experience which 
significantly exceeds candidate profile. Technology stack focuses 
on Java/C++ while candidate specializes in Python. On-site only 
conflicts with remote preference.

Concerns:
- Experience gap (requires 10+ years, candidate has 5)
- Technology mismatch (Java/C++ vs Python)
- Location conflict (on-site vs remote)

Strategy: skip
Priority: low
```

### REVIEW Decision
```
Decision: REVIEW
Score: 65/100
Confidence: 55%

Reasoning: Partial match with some concerns. Role responsibilities 
are somewhat ambiguous. Salary range unclear. Required framework 
experience is adjacent but not exact match.

Questions to Consider:
- Is the salary range acceptable?
- Can you learn the required framework in reasonable time?
- Is occasional travel (20%) feasible?

Recommendation: Contact recruiter to clarify requirements and 
discuss framework learning curve.

Key Points:
- Salary unclear
- Framework adjacent match
- Travel requirements
```

## Performance

### Speed
- Simple: <1ms per job
- LLM: 2-5 seconds per job
- Multi-Agent: 5-10 seconds per job

### Token Usage
- Simple: 0 tokens
- LLM: ~500 tokens per job
- Multi-Agent: ~1500 tokens per job

### Accuracy
- Simple: Keyword matching
- LLM: Context-aware evaluation
- Multi-Agent: Deep reasoning + strategy

## Best Practices

1. **Start with Review Mode**
   - Set `apply_all: false`
   - Review agent decisions manually
   - Build confidence in the system

2. **Tune Your Profile**
   - Add specific skills
   - Include relevant keywords
   - Set realistic expectations

3. **Monitor and Adjust**
   - Check agent reasoning in logs
   - Adjust min_score threshold
   - Tune uncertainty_margin

4. **Use Selectively**
   - Enable for high-value jobs
   - Disable for bulk screening
   - Balance quality vs quantity

## Troubleshooting

### Agents Not Working

```bash
# Check Ollama is running
docker ps | grep ollama

# Check model is loaded
docker exec jobsentinel-ollama ollama list

# Test LLM directly
docker exec jobsentinel-ollama ollama run llama3.2:latest "test"
```

### Slow Evaluation

- Normal: 5-10 seconds with agents
- Speed up: Use smaller model (phi4)
- Or: Disable agents for bulk screening

### Wrong Decisions

- Review agent reasoning in logs
- Adjust profile (skills, keywords)
- Tune min_score threshold
- Provide feedback via dashboard

## Files

- `src/ai/agents.py` - Multi-agent system (450 lines)
- `src/ai/agents_wrapper.py` - Integration wrapper (80 lines)
- `src/core/controller.py` - Controller integration
- `configs/settings.yaml` - Configuration

## Documentation

- `README_AGENTS.md` - This file
- `USAGE_GUIDE.md` - Step-by-step usage
- `QUICKSTART.md` - Quick start
- `REPORT.md` - Complete report
- `CHECKLIST.md` - Action items

## Support

**Logs:** `data/jobsentinel.log`
**Database:** `data/jobsentinel.db`
**Dashboard:** http://localhost:5000

---

**Version:** Multi-Agent v1.0
**Status:** Production Ready
**Date:** April 25, 2026
