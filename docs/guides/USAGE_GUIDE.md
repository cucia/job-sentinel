# Using the Multi-Agent System - Step by Step

## Current Status

Your JobSentinel is fully functional with multi-agent AI. Here's how to use it.

## Step 1: Enable Agents

Open `configs/settings.yaml` and change:

```yaml
ai:
  min_score: 70
  uncertainty_margin: 5
  use_llm: true          # Change to true
  llm_model: llama3.2:latest
  use_agents: true       # Change to true
```

## Step 2: Start Ollama

```bash
# Start Ollama container
docker-compose up -d ollama

# Wait 10 seconds for it to start
sleep 10

# Pull the model (first time only)
docker exec jobsentinel-ollama ollama pull llama3.2:latest
```

## Step 3: Test the Agents

Create a test file `test_agents.py`:

```python
from src.core.config import load_settings, load_profile
from src.ai.agents_wrapper import evaluate_job_with_agents

# Load configuration
settings = load_settings('.')
settings['ai']['use_agents'] = True
settings['ai']['use_llm'] = True
profile = load_profile('.')

# Test job
job = {
    'title': 'Security Engineer',
    'company': 'TechCorp',
    'description': '''
    We are looking for a Security Engineer with:
    - 3-5 years experience in cybersecurity
    - Strong Python programming skills
    - Experience with cloud security (AWS/Azure)
    - Knowledge of security tools and frameworks
    - Excellent communication skills
    
    Responsibilities:
    - Implement security controls
    - Conduct security assessments
    - Respond to security incidents
    - Develop security automation
    ''',
    'location': 'Remote',
    'easy_apply': True,
    'posted_text': '2 days ago'
}

# Evaluate with agents
print("Evaluating job with multi-agent system...\n")
result = evaluate_job_with_agents(job, profile, settings)

# Display results
print("=" * 60)
print(f"DECISION: {result['decision']}")
print(f"SCORE: {result['score']}/100")
print(f"CONFIDENCE: {result['confidence']}%")
print(f"PRIORITY: {result['priority_score']}")
print("=" * 60)
print(f"\nREASONING:\n{result['reasoning']}")
print(f"\nMATCH FACTORS:\n- " + "\n- ".join(result['match_factors']))
if result['concerns']:
    print(f"\nCONCERNS:\n- " + "\n- ".join(result['concerns']))
if result.get('application_strategy'):
    print(f"\nAPPLICATION STRATEGY: {result['application_strategy']}")
    print(f"PRIORITY: {result.get('application_priority', 'N/A')}")
print("=" * 60)
```

Run it:
```bash
python test_agents.py
```

## Step 4: Start the Full System

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## Step 5: Access Dashboard

Open browser: http://localhost:5000

Navigate to:
- **Overview** - See stats and system status
- **Automation** - Enable/disable platforms and AI
- **Sessions** - Login to LinkedIn/Indeed/Naukri
- **Jobs** - View collected jobs
- **Profile** - Configure your profile

## Step 6: Configure Your Profile

1. Go to http://localhost:5000/profile
2. Fill in your details:
   - Name, email, phone
   - Role and experience
   - Skills (comma-separated)
   - Keywords (comma-separated)
   - Location preferences

## Step 7: Login to Platforms

1. Go to http://localhost:5000/sessions
2. For each platform:
   - Click "Start Login"
   - Login in the browser window
   - Click "Save Session"
   - Verify with "Check Session"

## Step 8: Start Collecting Jobs

The controller will automatically:
1. Collect jobs from enabled platforms
2. Evaluate each job with agents
3. Apply to jobs that score high
4. Move uncertain jobs to review

Monitor in dashboard:
- **Jobs → Review** - Jobs needing your decision
- **Jobs → Applied** - Successfully applied
- **Jobs → Queued** - Waiting to apply
- **Jobs → Rejected** - Not a good match

## Understanding Agent Decisions

### APPLY Decision
```
Decision: APPLY
Score: 85/100
Confidence: 90%

Reasoning: Strong match with required security skills. 
Experience level aligns well. Remote work matches preferences.

Match Factors:
- Python programming
- Security experience
- Cloud knowledge
- Remote work

Strategy: easy_apply
Priority: high
```

### REJECT Decision
```
Decision: REJECT
Score: 35/100
Confidence: 95%

Reasoning: Job requires senior-level experience (10+ years) 
which exceeds candidate profile. Technology stack mismatch.

Concerns:
- Experience gap (requires 10+ years)
- Different tech stack (Java vs Python)
- On-site only (conflicts with remote preference)
```

### REVIEW Decision
```
Decision: REVIEW
Score: 65/100
Confidence: 55%

Reasoning: Partial match with some concerns. Salary range 
unclear. Role responsibilities somewhat ambiguous.

Questions to Consider:
- Is the salary range acceptable?
- Can you learn the required framework?
- Is occasional travel feasible?

Recommendation: Contact recruiter for clarification
```

## Monitoring Agent Performance

Check logs:
```bash
tail -f data/jobsentinel.log
```

Look for:
```
AI accepted: title=Security Engineer score=85 confidence=90 ...
AI rejected: title=Senior Architect score=35 confidence=95 ...
AI review: title=DevOps Engineer score=65 confidence=55 ...
```

## Adjusting Agent Behavior

### Make Agents More Selective
```yaml
ai:
  min_score: 80  # Increase from 70
  uncertainty_margin: 3  # Decrease from 5
```

### Make Agents Less Selective
```yaml
ai:
  min_score: 60  # Decrease from 70
  uncertainty_margin: 10  # Increase from 5
```

### Change LLM Model
```yaml
ai:
  llm_model: mistral:latest  # or phi4, llama3.2, etc.
```

## Troubleshooting

### Agents not evaluating?
```bash
# Check Ollama is running
docker ps | grep ollama

# Check model is loaded
docker exec jobsentinel-ollama ollama list

# Test LLM directly
docker exec jobsentinel-ollama ollama run llama3.2:latest "Hello"
```

### Slow evaluation?
- Normal: 5-10 seconds per job with agents
- Speed up: Use smaller model (phi4)
- Or disable agents for bulk screening

### Wrong decisions?
- Review agent reasoning in logs
- Adjust your profile (skills, keywords)
- Tune min_score threshold
- Provide feedback via dashboard

## Best Practices

1. **Start with Review Mode**
   - Set `apply_all: false` initially
   - Review agent decisions manually
   - Build confidence in the system

2. **Tune Your Profile**
   - Add specific skills
   - Include relevant keywords
   - Set realistic expectations

3. **Monitor Daily**
   - Check review queue
   - Approve/reject borderline cases
   - System learns from your feedback

4. **Use Agents Selectively**
   - Enable for high-value jobs
   - Disable for bulk screening
   - Balance quality vs quantity

## Example Workflow

### Morning Routine
```bash
# Check what was collected overnight
curl http://localhost:5000/jobs/review

# Review agent decisions
# Approve good matches
# Reject poor matches

# Check applications
curl http://localhost:5000/jobs/applied
```

### Weekly Review
```bash
# Export all jobs
curl http://localhost:5000/export.csv > jobs.csv

# Analyze patterns
# Adjust profile based on results
# Tune agent thresholds
```

## Getting Help

- **Logs**: `data/jobsentinel.log`
- **Database**: `data/jobsentinel.db` (SQLite)
- **Sessions**: `sessions/*.json`
- **Config**: `configs/settings.yaml`

## Summary

You now have:
- ✓ Multi-agent AI system
- ✓ Intelligent job evaluation
- ✓ Application strategy planning
- ✓ Human-in-the-loop review
- ✓ Batch prioritization

**Next**: Enable agents, start collecting, and let the AI help you find the best jobs!
