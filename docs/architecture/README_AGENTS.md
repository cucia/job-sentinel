# Agent System Overview

## Configuration

Enable agents in [configs/settings.yaml](../../configs/settings.yaml):

```yaml
app:
  use_ai: true

ai:
  use_agents: true
  use_multi_agent: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
  min_score: 70
  uncertainty_margin: 5
```

## Operating Modes

### Heuristic Fallback
```yaml
use_agents: false
```

### Multi-Agent Mode
```yaml
use_agents: true
use_multi_agent: true
use_cloud: true
```

## Notes

- The active runtime uses configured cloud providers for agent reasoning.
- Non-agent fallback remains heuristic.
