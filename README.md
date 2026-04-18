# JobSentinel


JobSentinel is a cybersecurity job automation system that:
- collects jobs from multiple platforms,
- stores them in a local SQLite database,
- applies automatically when possible,
- and exposes a dashboard for tracking and export.

The goal is to scale to many platforms while keeping the core workflow stable and modular.

## How it works

1) Collect jobs from each enabled platform.
2) Store jobs in SQLite (`data/jobsentinel.db`).
3) Optionally enrich jobs with "About the job" content (LinkedIn only).
4) Apply automatically; anything blocked goes to **Review**.
5) Show results in the dashboard (tabs + CSV export).

## Project Structure

```
src/
├── ai/                    # AI/ML layer
│   ├── scorer.py         # Job scoring (rule-based + LLM)
│   ├── llm.py            # Ollama client for LLM evaluation
│   ├── form_filler.py    # Application form automation
│   └── chat.py           # Profile chat assistant
├── core/                 # Business logic
│   ├── controller.py     # Main pipeline
│   ├── storage.py         # SQLite database
│   ├── config.py          # Settings management
│   └── ...
├── platforms/            # Platform integrations
│   ├── linkedin/
│   ├── indeed/
│   └── naukri/
└── services/             # External services
    └── session_manager.py
dashboard/               # Flask UI
configs/                 # Configuration files
```

## Containers

Services defined in docker-compose.yml:
- `ollama` - Local LLM server (optional)
- `jobsentinel-linkedin` (LinkedIn only)
- `jobsentinel-indeed` (Indeed only)
- `jobsentinel-naukri` (Naukri only)
- `dashboard` (UI)

Start services:
```powershell
# With LLM evaluation
docker-compose up -d ollama jobsentinel-linkedin dashboard

# Without LLM
docker-compose up -d jobsentinel-linkedin dashboard
```

## Settings

All settings live in `configs/settings.yaml`. Key switches:

```yaml
app:
  run_interval_seconds: 60
  apply_all: true
  use_ai: false
  use_policy: false
  entry_level_only: false
  enrich_before_ai: true

ai:
  use_llm: false              # Enable Ollama for job scoring
  llm_model: llama3.2:latest # Ollama model to use
  min_score: 70
  uncertainty_margin: 5

platforms:
  enabled:
    - linkedin
    # - indeed
```

### Dashboard toggles

The dashboard has toggles for:
- Platform on/off (LinkedIn, Indeed, Naukri)
- AI filter on/off
- LLM evaluation on/off (requires Ollama)

These toggles update `configs/settings.yaml`.

## LLM Integration (Optional)

JobSentinel can use a local LLM via Ollama for smarter job matching:

1. Start Ollama: `docker-compose up -d ollama`
2. Pull a model: `docker exec jobsentinel-ollama ollama pull llama3.2:latest`
3. Enable in settings: `ai.use_llm: true`

Supported models: llama3.2, mistral, phi4

## Data locations

- Sessions: `sessions/*.json`
- Database: `data/jobsentinel.db`
- Resume: `resumes/resume.pdf`

## CSV export

Download jobs from the dashboard:
- `http://localhost:5000/export.csv`
- `http://localhost:5000/export.csv?status=applied`

## Setup

Full setup steps are in `SETUP.md`.