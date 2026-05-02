# JobSentinel - Quick Start Guide

## What You Have Now

JobSentinel with cloud-backed AI agents for job evaluation and automated application workflows.

## Quick Start

### 1. Configure Cloud AI

Edit [configs/settings.yaml](../../configs/settings.yaml):

```yaml
app:
  use_ai: true

ai:
  use_agents: true
  use_multi_agent: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

### 2. Start Services

```bash
docker compose up -d dashboard jobsentinel-linkedin jobsentinel-indeed jobsentinel-naukri
```

### 3. Access Dashboard

Open browser: http://localhost:5000

## Features

### Implemented
- Multi-agent evaluation and apply workflow
- LinkedIn, Indeed, and Naukri collectors
- Dashboard for profile, automation, sessions, and review
- Truthful application outcome reporting and logs

## Notes

- The active runtime is cloud-backed for agent reasoning.
- If cloud keys are missing, resume parsing falls back to regex extraction and non-agent evaluation falls back to heuristic scoring.
