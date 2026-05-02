# START HERE - JobSentinel Multi-Agent System

## What You Have

JobSentinel with cloud-backed AI agents that evaluate jobs, plan strategies, and drive application workflows.

## Quick Start

### Step 1: Configure AI
```yaml
ai:
  use_agents: true
  use_multi_agent: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

### Step 2: Start Services
```bash
docker compose up -d
```

### Step 3: Use It
Open http://localhost:5000

## Notes

- The active runtime is cloud-only for LLM calls.
- Resume parsing still falls back cleanly if cloud extraction is unavailable.
