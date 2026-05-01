# Free AI Provider Setup Guide

## Overview

JobSentinel now supports **FREE** AI providers for running agents without cost:

1. **OpenRouter** - Free tier with multiple models
2. **Groq** - Fast inference, 14,400 requests/day free
3. **Together.ai** - $25 free credits
4. **Google Gemini** - 1,500 requests/day free

## Quick Comparison

| Provider | Free Tier | Speed | Quality | Best For |
|----------|-----------|-------|---------|----------|
| **Groq** | 14,400 req/day | Very Fast | Good | High volume |
| **OpenRouter** | Unlimited* | Medium | Good | Testing |
| **Gemini** | 1,500 req/day | Fast | Very Good | Quality |
| **Together.ai** | $25 credits | Fast | Good | Starting out |

*Some models are free, others pay-per-use

---

## Option 1: Groq (Recommended for Free)

**Best for:** High volume, fast responses

### Setup

1. **Get API Key**
   - Go to https://console.groq.com/keys
   - Sign up (free)
   - Create API key

2. **Install Package**
   ```bash
   pip install openai
   ```

3. **Set Environment Variable**
   ```bash
   # Windows PowerShell
   $env:GROQ_API_KEY = "gsk_..."
   
   # Linux/Mac
   export GROQ_API_KEY="gsk_..."
   ```

4. **Update Config** (`configs/settings.yaml`)
   ```yaml
   ai:
     use_agents: true
     use_cloud: true
     provider: groq
     model: llama-3.1-70b-versatile
     min_score: 70
   ```

### Free Tier Limits
- **14,400 requests per day**
- **30 requests per minute**
- Models: Llama 3.1 70B, Mixtral 8x7B, Gemma 7B

### Token Calculation (24 hours)
- Conservative mode (5 min interval): ~28,800 jobs
- Groq limit: 14,400 requests/day
- **Result: Can handle ~14,400 jobs/day for FREE**

---

## Option 2: OpenRouter

**Best for:** Testing, multiple model access

### Setup

1. **Get API Key**
   - Go to https://openrouter.ai/keys
   - Sign up (free)
   - Create API key

2. **Install Package**
   ```bash
   pip install openai
   ```

3. **Set Environment Variable**
   ```bash
   # Windows PowerShell
   $env:OPENROUTER_API_KEY = "sk-or-..."
   
   # Linux/Mac
   export OPENROUTER_API_KEY="sk-or-..."
   ```

4. **Update Config** (`configs/settings.yaml`)
   ```yaml
   ai:
     use_agents: true
     use_cloud: true
     provider: openrouter
     model: google/gemini-flash-1.5  # FREE
     min_score: 70
   ```

### Free Models
- `google/gemini-flash-1.5` - Free, fast
- `meta-llama/llama-3.2-3b-instruct` - Free
- `mistralai/mistral-7b-instruct` - Free

### Paid Models (Cheap)
- `anthropic/claude-3.5-sonnet` - $3 per 1M tokens
- `openai/gpt-4-turbo` - $10 per 1M tokens

---

## Option 3: Google Gemini

**Best for:** Quality on free tier

### Setup

1. **Get API Key**
   - Go to https://makersuite.google.com/app/apikey
   - Sign up (free)
   - Create API key

2. **Install Package**
   ```bash
   pip install google-generativeai
   ```

3. **Set Environment Variable**
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY = "..."
   
   # Linux/Mac
   export GEMINI_API_KEY="..."
   ```

4. **Update Config** (`configs/settings.yaml`)
   ```yaml
   ai:
     use_agents: true
     use_cloud: true
     provider: gemini
     model: gemini-1.5-flash
     min_score: 70
   ```

### Free Tier Limits
- **1,500 requests per day**
- **15 requests per minute**
- Model: Gemini 1.5 Flash

### Token Calculation (24 hours)
- Conservative mode: ~28,800 jobs
- Gemini limit: 1,500 requests/day
- **Result: Can handle ~1,500 jobs/day for FREE**

---

## Option 4: Together.ai

**Best for:** Getting started with credits

### Setup

1. **Get API Key**
   - Go to https://api.together.xyz/settings/api-keys
   - Sign up (get $25 free credits)
   - Create API key

2. **Install Package**
   ```bash
   pip install openai
   ```

3. **Set Environment Variable**
   ```bash
   # Windows PowerShell
   $env:TOGETHER_API_KEY = "..."
   
   # Linux/Mac
   export TOGETHER_API_KEY="..."
   ```

4. **Update Config** (`configs/settings.yaml`)
   ```yaml
   ai:
     use_agents: true
     use_cloud: true
     provider: together
     model: meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
     min_score: 70
   ```

### Pricing (After Free Credits)
- Llama 3.1 70B: $0.88 per 1M tokens
- Mixtral 8x22B: $1.20 per 1M tokens
- **$25 credits = ~28M tokens = ~24,000 jobs**

---

## Recommended Configuration for FREE Usage

### High Volume (Groq)
```yaml
app:
  run_interval_seconds: 300  # 5 minutes
  daily_applications: 10

ai:
  use_agents: true
  use_cloud: true
  provider: groq
  model: llama-3.1-70b-versatile
  min_score: 70

platforms:
  linkedin:
    search:
      max_results: 50
      easy_apply_only: true
```

**Capacity:** 14,400 jobs/day FREE

### Quality Focus (Gemini)
```yaml
app:
  run_interval_seconds: 600  # 10 minutes
  daily_applications: 10

ai:
  use_agents: true
  use_cloud: true
  provider: gemini
  model: gemini-1.5-flash
  min_score: 70

platforms:
  linkedin:
    search:
      max_results: 20
      easy_apply_only: true
```

**Capacity:** 1,500 jobs/day FREE

---

## Testing Your Setup

### Test Groq
```bash
python -c "
from src.ai.cloud_llm import CloudLLMClient

client = CloudLLMClient(provider='groq', model='llama-3.1-70b-versatile')
response = client.chat([
    {'role': 'system', 'content': 'You are helpful.'},
    {'role': 'user', 'content': 'Say hello'}
])
print('Response:', response)
"
```

### Test OpenRouter
```bash
python -c "
from src.ai.cloud_llm import CloudLLMClient

client = CloudLLMClient(provider='openrouter', model='google/gemini-flash-1.5')
response = client.chat([
    {'role': 'system', 'content': 'You are helpful.'},
    {'role': 'user', 'content': 'Say hello'}
])
print('Response:', response)
"
```

### Test Gemini
```bash
python -c "
from src.ai.cloud_llm import CloudLLMClient

client = CloudLLMClient(provider='gemini', model='gemini-1.5-flash')
response = client.chat([
    {'role': 'system', 'content': 'You are helpful.'},
    {'role': 'user', 'content': 'Say hello'}
])
print('Response:', response)
"
```

---

## Cost Comparison (24 hours, Conservative Mode)

| Provider | Model | Cost | Jobs/Day |
|----------|-------|------|----------|
| **Groq** | Llama 3.1 70B | **FREE** | 14,400 |
| **OpenRouter** | Gemini Flash | **FREE** | Unlimited* |
| **Gemini** | Gemini 1.5 Flash | **FREE** | 1,500 |
| **Together.ai** | Llama 3.1 70B | $1-2 | 28,800 |
| OpenAI | GPT-3.5 | $23-46 | 28,800 |
| OpenAI | GPT-4 | $460-1,380 | 28,800 |

*Rate limited but no hard cap

---

## Troubleshooting

### API Key Not Found
```bash
# Check if set
echo $GROQ_API_KEY

# Set it
export GROQ_API_KEY="gsk-..."
```

### Rate Limit Exceeded
**Solution:** Increase `run_interval_seconds` in config

```yaml
app:
  run_interval_seconds: 600  # 10 minutes instead of 5
```

### Package Not Installed
```bash
pip install openai  # For Groq, OpenRouter, Together.ai
pip install google-generativeai  # For Gemini
```

---

## Summary

**Best Free Options:**

1. **Groq** - 14,400 jobs/day, very fast, FREE
2. **Gemini** - 1,500 jobs/day, high quality, FREE
3. **OpenRouter** - Unlimited with free models, FREE
4. **Together.ai** - $25 credits (~24,000 jobs)

**Recommendation:**
- Start with **Groq** for high volume
- Use **Gemini** if you need better quality
- Try **OpenRouter** for testing different models

All options are significantly cheaper than OpenAI GPT-4 and work great with the multi-agent system!
