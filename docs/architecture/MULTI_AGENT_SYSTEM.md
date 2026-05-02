# Multi-Agent System

## Configuration

Enable coordinated agents in [configs/settings.yaml](../../configs/settings.yaml):

```yaml
ai:
  use_multi_agent: true
  use_agents: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

## Features

- Dynamic navigation
- Intelligent form detection
- Integrated form filling
- Recovery and truthful outcome reporting

## Notes

The runtime uses configured cloud AI providers for agent reasoning.
