# Cloud AI Configuration Guide

## Overview

JobSentinel now supports multiple cloud AI providers instead of just local Ollama:
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic Claude** (Claude 3.5 Sonnet, Claude 3 Opus)
- **Google Gemini** (Gemini 1.5 Pro)
- **Ollama** (local fallback)

## Quick Setup

### 1. Choose Your Provider

Edit `configs/settings.yaml`:

#### Option A: OpenAI (Recommended)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview  # or gpt-3.5-turbo for faster/cheaper
  # api_key: sk-...  # Optional: set in environment instead
```

#### Option B: Anthropic Claude
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: anthropic
  model: claude-3-5-sonnet-20241022  # or claude-3-opus-20240229
  # api_key: sk-ant-...  # Optional: set in environment instead
```

#### Option C: Google Gemini
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: gemini
  model: gemini-1.5-pro
  # api_key: ...  # Optional: set in environment instead
```

#### Option D: Ollama (Local)
```yaml
ai:
  use_agents: true
  use_cloud: false  # or omit this line
  llm_model: llama3.2:latest
```

### 2. Set API Key

**Recommended: Environment Variable**

Windows PowerShell:
```powershell
# OpenAI
$env:OPENAI_API_KEY = "sk-..."

# Anthropic
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Gemini
$env:GEMINI_API_KEY = "..."
```

Linux/Mac:
```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Gemini
export GEMINI_API_KEY="..."
```

**Alternative: .env File**

Create/edit `.env` file:
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Gemini
GEMINI_API_KEY=...
```

### 3. Install Required Package

```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Gemini
pip install google-generativeai
```

### 4. Test Configuration

```bash
python -c "
from src.ai.cloud_llm import create_llm_client
from src.core.config import load_settings

settings = load_settings('.')
client = create_llm_client(settings)

response = client.chat([
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'Say hello'}
])
print('Response:', response)
"
```

## Provider Comparison

| Provider | Speed | Cost | Quality | Best For |
|----------|-------|------|---------|----------|
| **OpenAI GPT-4** | Medium | High | Excellent | Best reasoning |
| **OpenAI GPT-3.5** | Fast | Low | Good | High volume |
| **Claude 3.5 Sonnet** | Fast | Medium | Excellent | Balanced |
| **Claude 3 Opus** | Slow | High | Excellent | Complex analysis |
| **Gemini 1.5 Pro** | Fast | Medium | Very Good | Long context |
| **Ollama (local)** | Medium | Free | Good | Privacy/offline |

## Cost Estimates (per 1000 jobs)

### OpenAI
- **GPT-4 Turbo**: ~$15-30 (1500 tokens × 1000 jobs)
- **GPT-3.5 Turbo**: ~$1-2 (1500 tokens × 1000 jobs)

### Anthropic
- **Claude 3.5 Sonnet**: ~$7-15 (1500 tokens × 1000 jobs)
- **Claude 3 Opus**: ~$30-60 (1500 tokens × 1000 jobs)

### Google
- **Gemini 1.5 Pro**: ~$3-7 (1500 tokens × 1000 jobs)

### Ollama
- **Local LLM**: Free (requires GPU/CPU resources)

## Configuration Examples

### High Quality (Expensive)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview
  min_score: 75
```

### Balanced (Recommended)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  min_score: 70
```

### High Volume (Cheap)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-3.5-turbo
  min_score: 65
```

### Privacy/Offline (Free)
```yaml
ai:
  use_agents: true
  use_cloud: false
  llm_model: llama3.2:latest
  min_score: 70
```

## Complete Settings Example

```yaml
app:
  apply_all: true
  use_ai: true
  pipeline_mode: direct_latest

ai:
  # Cloud AI Configuration
  use_agents: true
  use_cloud: true
  provider: openai  # or anthropic, gemini, ollama
  model: gpt-4-turbo-preview
  # api_key: sk-...  # Optional, use environment variable instead
  
  # Scoring thresholds
  min_score: 70
  uncertainty_margin: 5

platforms:
  enabled:
    - linkedin
```

## Troubleshooting

### API Key Not Found
```bash
# Check environment variable
echo $OPENAI_API_KEY  # Linux/Mac
echo $env:OPENAI_API_KEY  # PowerShell

# Set it if missing
export OPENAI_API_KEY="sk-..."  # Linux/Mac
$env:OPENAI_API_KEY = "sk-..."  # PowerShell
```

### Package Not Installed
```bash
# Install required package
pip install openai  # for OpenAI
pip install anthropic  # for Anthropic
pip install google-generativeai  # for Gemini
```

### API Error
```bash
# Check logs
tail -f data/jobsentinel.log

# Test API directly
python -c "
import openai
client = openai.OpenAI(api_key='sk-...')
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'test'}]
)
print(response.choices[0].message.content)
"
```

## Migration from Ollama

If you were using Ollama, here's how to switch:

**Before (Ollama):**
```yaml
ai:
  use_llm: true
  use_agents: true
  llm_model: llama3.2:latest
```

**After (OpenAI):**
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview
```

Then:
1. Set `OPENAI_API_KEY` environment variable
2. Install: `pip install openai`
3. Restart services: `docker-compose restart`

## Docker Configuration

Update `docker-compose.yml` to pass API keys:

```yaml
services:
  jobsentinel-linkedin:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

Or use `.env` file (already configured).

## Best Practices

1. **Use Environment Variables** for API keys (not in config files)
2. **Start with GPT-3.5** to test, then upgrade to GPT-4
3. **Monitor Costs** - check your provider's dashboard
4. **Set Rate Limits** in settings to control spending
5. **Use Ollama** for development/testing (free)

## Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and save it (shown once)

### Anthropic
1. Go to https://console.anthropic.com/settings/keys
2. Create new API key
3. Copy and save it

### Google Gemini
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy and save it

## Summary

✅ **Cloud AI support added**
✅ **Multiple providers supported**
✅ **No Ollama required**
✅ **Easy configuration**

**Next Steps:**
1. Choose your provider
2. Get API key
3. Update `configs/settings.yaml`
4. Install required package
5. Test and start using!
