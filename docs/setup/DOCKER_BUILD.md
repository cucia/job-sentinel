# Docker Build & Deployment Guide

## Prerequisites

1. Docker Desktop installed and running
2. Git repository cloned
3. In project directory: `C:\Users\qucia\Music\job-sentinel`

## Build & Start Services

```powershell
docker compose build
docker compose up -d
docker compose ps
```

## Post-Build Setup

### 1. Access Dashboard

Open browser: http://localhost:5000

### 2. Configure Profile

Fill in profile details and search keywords from the dashboard.

### 3. Configure Cloud AI

Edit [configs/settings.yaml](../../configs/settings.yaml):

```yaml
ai:
  use_agents: true
  use_multi_agent: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

Provide the matching provider API key through environment variables or `.env`.

## Verify Build

```powershell
docker compose ps
docker compose logs --tail=50 dashboard jobsentinel-linkedin jobsentinel-indeed jobsentinel-naukri
```

## Notes

- The runtime uses configured cloud AI providers for agent reasoning.
- If cloud AI is unavailable, heuristic evaluation remains available for the non-agent fallback path.
