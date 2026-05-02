# Cloud AI Configuration Guide

## Overview

JobSentinel uses cloud AI providers for agent evaluation and orchestration.

Supported providers:
- **OpenAI**
- **Anthropic Claude**
- **Google Gemini**
- **OpenRouter**
- **Groq**
- **Together.ai**

## Quick Setup

Edit [configs/settings.yaml](../../configs/settings.yaml):

### OpenAI
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview
```

### Anthropic
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: anthropic
  model: claude-3-5-sonnet-20241022
```

### Gemini
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: gemini
  model: gemini-1.5-pro
```

### Groq
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: groq
  model: llama-3.1-8b-instant
```

## API Keys

Use environment variables or `.env`:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
TOGETHER_API_KEY=...
```

## Notes

- The active runtime uses cloud providers for agent reasoning.
- Resume parsing still uses the cloud client when keys are available and falls back to regex extraction otherwise.
- If cloud AI is disabled, non-agent evaluation falls back to the heuristic scorer.
