# JobSentinel - Quick Start Guide

## What You Have Now

JobSentinel with intelligent multi-agent AI system for automated job applications.

## Quick Start

### 1. Enable Multi-Agent System

Edit `configs/settings.yaml`:
```yaml
ai:
  use_ai: true
  use_llm: true
  use_agents: true
  llm_model: llama3.2:latest
```

### 2. Start Services

```bash
# Start Ollama (for LLM)
docker-compose up -d ollama

# Pull model
docker exec jobsentinel-ollama ollama pull llama3.2:latest

# Start dashboard
docker-compose up -d dashboard

# Start job collector (LinkedIn)
docker-compose up -d jobsentinel-linkedin
```

### 3. Access Dashboard

Open browser: http://localhost:5000

## Features

### ✅ Implemented

1. **Multi-Agent AI System**
   - JobEvaluatorAgent - Analyzes job match
   - ApplicationAgent - Plans strategy
   - ReviewAgent - Helps with decisions
   - StrategyAgent - Prioritizes jobs

2. **Platform Support**
   - LinkedIn (with Easy Apply)
   - Indeed
   - Naukri

3. **Smart Evaluation**
   - Detailed reasoning
   - Confidence scores
   - Match factors
   - Red flags detection

4. **Dashboard**
   - Job tracking
   - Status management
   - CSV export
   - Profile management

### 🔄 Coming Soon

1. **Portal Scanner** - Direct API scanning (Greenhouse, Ashby, Lever)
2. **Interview Prep** - STAR stories generation
3. **Pattern Analysis** - Success/rejection patterns
4. **Follow-up Manager** - Automated reminders
5. **CV Generator** - Tailored CVs per job
6. **Batch Processing** - Parallel evaluation

## Agent Modes

### Simple (Fast)
```yaml
use_ai: true
use_llm: false
use_agents: false
```
- 0 tokens, <1ms per job
- Keyword matching

### LLM (Balanced)
```yaml
use_ai: true
use_llm: true
use_agents: false
```
- ~500 tokens, 2-5s per job
- Basic LLM evaluation

### Multi-Agent (Intelligent)
```yaml
use_ai: true
use_llm: true
use_agents: true
```
- ~1500 tokens, 5-10s per job
- Deep reasoning, strategy, review

## Example Agent Output

```json
{
  "decision": "APPLY",
  "score": 85,
  "confidence": 90,
  "reasoning": "Strong match with required security skills. Experience level aligns well.",
  "match_factors": ["Python", "Security", "Cloud", "Remote"],
  "concerns": ["Salary not specified"],
  "application_strategy": "easy_apply",
  "priority": "high"
}
```

## Testing

```bash
# Test agents
python -c "from src.ai.agents import AgentOrchestrator; print('✅ Ready')"

# Test evaluation
python -c "
from src.ai.agents_wrapper import evaluate_job_with_agents
from src.core.config import load_settings, load_profile

settings = load_settings('.')
settings['ai']['use_agents'] = True
settings['ai']['use_llm'] = True
profile = load_profile('.')

job = {
    'title': 'Security Engineer',
    'company': 'Test',
    'description': 'Python security engineer',
    'easy_apply': True
}

result = evaluate_job_with_agents(job, profile, settings)
print(f'Decision: {result[\"decision\"]}')
print(f'Score: {result[\"score\"]}')
"
```

## Configuration

### Profile (`configs/profile.yaml`)
```yaml
name: Your Name
role: Security Engineer
experience: 5 years
skills:
  - Python
  - Security
  - Cloud
keywords:
  - cybersecurity
  - penetration testing
location: Remote
```

### Settings (`configs/settings.yaml`)
```yaml
app:
  apply_all: true
  use_ai: true
  pipeline_mode: direct_latest

ai:
  use_llm: true
  use_agents: true
  llm_model: llama3.2:latest
  min_score: 70

platforms:
  enabled:
    - linkedin
```

## Troubleshooting

### Agents not working?
1. Check Ollama: `docker ps | grep ollama`
2. Check model: `docker exec jobsentinel-ollama ollama list`
3. Check logs: `tail -f data/jobsentinel.log`

### Dashboard not loading?
1. Check port: `netstat -an | grep 5000`
2. Check logs: `docker logs dashboard`

### No jobs found?
1. Check sessions: Dashboard → Sessions tab
2. Login to platforms
3. Check settings: `platforms.enabled`

## Support

- Logs: `data/jobsentinel.log`
- Database: `data/jobsentinel.db`
- Sessions: `sessions/*.json`

## Next Steps

1. Configure your profile
2. Enable agents
3. Login to platforms
4. Start collecting jobs
5. Review agent decisions
6. Apply to best matches

---

**Ready to use!** Start with `docker-compose up -d` and open http://localhost:5000
