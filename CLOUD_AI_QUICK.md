# Cloud AI Quick Reference

## Setup (Choose One Provider)

### OpenAI (Recommended)
```bash
# 1. Get API key: https://platform.openai.com/api-keys
# 2. Install package
pip install openai

# 3. Set environment variable
export OPENAI_API_KEY="sk-..."  # Linux/Mac
$env:OPENAI_API_KEY = "sk-..."  # PowerShell

# 4. Update configs/settings.yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview
```

### Anthropic Claude
```bash
# 1. Get API key: https://console.anthropic.com/settings/keys
# 2. Install package
pip install anthropic

# 3. Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."  # Linux/Mac
$env:ANTHROPIC_API_KEY = "sk-ant-..."  # PowerShell

# 4. Update configs/settings.yaml
ai:
  use_agents: true
  use_cloud: true
  provider: anthropic
  model: claude-3-5-sonnet-20241022
```

### Google Gemini
```bash
# 1. Get API key: https://makersuite.google.com/app/apikey
# 2. Install package
pip install google-generativeai

# 3. Set environment variable
export GEMINI_API_KEY="..."  # Linux/Mac
$env:GEMINI_API_KEY = "..."  # PowerShell

# 4. Update configs/settings.yaml
ai:
  use_agents: true
  use_cloud: true
  provider: gemini
  model: gemini-1.5-pro
```

## Test Setup

```bash
python -c "
from src.ai.cloud_llm import create_llm_client
from src.core.config import load_settings

settings = load_settings('.')
client = create_llm_client(settings)

response = client.chat([
    {'role': 'system', 'content': 'You are helpful.'},
    {'role': 'user', 'content': 'Say hello'}
])
print('Success:', response)
"
```

## Model Options

### OpenAI
- `gpt-4-turbo-preview` - Best quality, slower, $$$
- `gpt-4` - High quality, slower, $$$
- `gpt-3.5-turbo` - Fast, cheap, good quality

### Anthropic
- `claude-3-5-sonnet-20241022` - Best balanced
- `claude-3-opus-20240229` - Highest quality, $$$
- `claude-3-sonnet-20240229` - Fast, balanced

### Google
- `gemini-1.5-pro` - Best quality
- `gemini-1.5-flash` - Faster, cheaper

## Cost per 1000 Jobs

| Provider | Model | Cost |
|----------|-------|------|
| OpenAI | GPT-4 Turbo | $15-30 |
| OpenAI | GPT-3.5 Turbo | $1-2 |
| Anthropic | Claude 3.5 Sonnet | $7-15 |
| Anthropic | Claude 3 Opus | $30-60 |
| Google | Gemini 1.5 Pro | $3-7 |

## Troubleshooting

### API Key Not Found
```bash
# Check if set
echo $OPENAI_API_KEY

# Set it
export OPENAI_API_KEY="sk-..."
```

### Package Not Installed
```bash
pip install openai  # or anthropic, google-generativeai
```

### Test API Key
```bash
# OpenAI
python -c "import openai; print(openai.OpenAI(api_key='sk-...').models.list())"

# Anthropic
python -c "import anthropic; print(anthropic.Anthropic(api_key='sk-ant-...').models.list())"
```

## Complete Example

```yaml
# configs/settings.yaml
app:
  apply_all: true
  use_ai: true

ai:
  use_agents: true
  use_cloud: true
  provider: openai
  model: gpt-4-turbo-preview
  min_score: 70

platforms:
  enabled:
    - linkedin
```

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Install package
pip install openai

# Start services
docker-compose up -d

# Access dashboard
open http://localhost:5000
```

## Switching Providers

Just change the config:

```yaml
# From OpenAI
ai:
  provider: openai
  model: gpt-4-turbo-preview

# To Claude
ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022

# To Gemini
ai:
  provider: gemini
  model: gemini-1.5-pro
```

And set the corresponding API key.

---

**Full Guide:** See `CLOUD_AI_SETUP.md`
