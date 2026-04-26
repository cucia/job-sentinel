# AI Agents - Complete Status & Setup

**Last Updated:** April 25, 2026

---

## Current Status

### ✅ What's Installed

**Multi-Agent System:**
- JobEvaluatorAgent (job matching analysis)
- ApplicationAgent (strategy planning)
- ReviewAgent (decision assistance)
- StrategyAgent (batch prioritization)
- AgentOrchestrator (coordination)

**AI Provider Support:**
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Anthropic Claude (Claude 3.5 Sonnet, Opus)
- ✅ Google Gemini (Gemini 1.5 Pro, Flash)
- ✅ **Groq (FREE - 14,400 req/day)**
- ✅ **OpenRouter (FREE models available)**
- ✅ **Together.ai ($25 free credits)**
- ✅ Ollama (local LLM - optional)

**Files:**
- `src/ai/agents.py` - Multi-agent system
- `src/ai/agents_wrapper.py` - Integration
- `src/ai/cloud_llm.py` - Cloud provider client (updated with free options)

### ⚠️ Current Configuration

```yaml
ai:
  use_agents: false    # Agents disabled
  use_cloud: false     # Cloud AI disabled
  provider: openai
  model: gpt-4-turbo-preview
```

**Status:** Agents are installed but **NOT ENABLED**

---

## FREE AI Options (NEW!)

### Option 1: Groq (Recommended) ⭐ FREE

**Pros:**
- Completely FREE (14,400 requests/day)
- Very fast inference
- Good quality (Llama 3.1 70B)
- No credit card required

**Cons:**
- Rate limited (30 req/min)
- Limited to 14,400 jobs/day

**Setup:**

1. **Get API Key**
   - Go to https://console.groq.com/keys
   - Sign up (free, no credit card)
   - Create API key

2. **Install Package**
   ```bash
   pip install openai
   ```

3. **Set Environment Variable**
   ```bash
   # PowerShell
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
   ```

5. **Start Using**
   ```bash
   docker-compose up -d
   ```

**Capacity:** 14,400 jobs/day FREE

---

### Option 2: OpenRouter FREE

**Pros:**
- Multiple free models
- No daily limit on some models
- Easy to switch models

**Cons:**
- Free models are smaller
- Quality varies by model

**Setup:**

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
   # PowerShell
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
   ```

**Free Models:**
- `google/gemini-flash-1.5` - Fast, free
- `meta-llama/llama-3.2-3b-instruct` - Free
- `mistralai/mistral-7b-instruct` - Free

---

### Option 3: Google Gemini FREE

**Pros:**
- High quality (Gemini 1.5)
- Completely free
- Good for quality over volume

**Cons:**
- Limited to 1,500 requests/day
- 15 requests/minute

**Setup:**

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
   # PowerShell
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
   ```

**Capacity:** 1,500 jobs/day FREE

---

### Option 4: Together.ai ($25 Free Credits)

**Pros:**
- $25 free credits (~24,000 jobs)
- Fast inference
- Good quality models

**Cons:**
- Requires credit card after free credits
- Not completely free long-term

**Setup:**

1. **Get API Key**
   - Go to https://api.together.xyz/settings/api-keys
   - Sign up (get $25 credits)
   - Create API key

2. **Install Package**
   ```bash
   pip install openai
   ```

3. **Set Environment Variable**
   ```bash
   # PowerShell
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
   ```

**Capacity:** ~24,000 jobs with free credits

---

## Paid Options (For Reference)

### Cloud AI (Paid)

**Pros:**
- Better quality
- Higher rate limits
- More reliable

**Cons:**
- Costs money (~$1-30 per 1000 jobs)
- Requires payment method

**Setup:** See `CLOUD_AI_SETUP.md`

### Local Ollama (Free)

**Pros:**
- Free
- Private
- Works offline

**Cons:**
- Requires Docker/GPU
- Slower
- Lower quality

**Setup:** See `CLOUD_AI_SETUP.md`

---

## Quick Comparison

| Provider | Cost | Jobs/Day | Quality | Speed | Setup |
|----------|------|----------|---------|-------|-------|
| **Groq** | FREE | 14,400 | Good | Very Fast | Easy |
| **OpenRouter** | FREE | Unlimited* | Good | Medium | Easy |
| **Gemini** | FREE | 1,500 | Very Good | Fast | Easy |
| **Together.ai** | $25 credits | ~24,000 | Good | Fast | Easy |
| OpenAI GPT-3.5 | $1-2/1000 | Unlimited | Good | Fast | Easy |
| OpenAI GPT-4 | $15-30/1000 | Unlimited | Excellent | Medium | Easy |
| Ollama | FREE | Unlimited | Good | Medium | Complex |

*Some models free, rate limited

---

## Recommended Configurations

### For FREE High Volume (Groq)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: groq
  model: llama-3.1-70b-versatile
  min_score: 70
```
**Cost:** FREE (14,400 jobs/day)

### For FREE Quality (Gemini)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: gemini
  model: gemini-1.5-flash
  min_score: 70
```
**Cost:** FREE (1,500 jobs/day)

### For Testing (OpenRouter)
```yaml
ai:
  use_agents: true
  use_cloud: true
  provider: openrouter
  model: google/gemini-flash-1.5
  min_score: 70
```
**Cost:** FREE (unlimited with free models)

---

## Documentation

| File | Purpose |
|------|---------|
| `FREE_AI_SETUP.md` | **Complete free AI guide** |
| `CLOUD_AI_SETUP.md` | Paid cloud AI guide |
| `CLOUD_AI_QUICK.md` | Quick reference |
| `README_AGENTS.md` | Agent architecture details |
| `USAGE_GUIDE.md` | Step-by-step usage |
| `START_HERE.md` | Getting started |

---

## Summary

**What You Have:**
- ✅ Multi-agent AI system (4 agents)
- ✅ Cloud AI support (OpenAI, Claude, Gemini)
- ✅ **FREE AI support (Groq, OpenRouter, Gemini)**
- ✅ Local LLM support (Ollama)
- ✅ Complete documentation

**What You Need to Do:**
1. Choose: FREE (Groq/Gemini) or Paid (OpenAI/Claude)
2. Follow setup steps above
3. Update `configs/settings.yaml`
4. Start using!

**Recommendation:**
- **Start with:** Groq (FREE, 14,400 jobs/day)
- **Or use:** Gemini (FREE, 1,500 jobs/day, better quality)
- **Upgrade to:** GPT-4 or Claude 3.5 (paid, best quality)

---

**Status:** Ready to configure and use! 🚀

**See `FREE_AI_SETUP.md` for complete free tier setup guide.**
