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

Core modules:
- `core/` controller, storage, settings, logging
- `platforms/` platform-specific collectors/apply/enrichers
- `dashboard/` UI + CSV export

## Containers

Separate services per platform:
- `jobsentinel-linkedin` (LinkedIn only)
- `jobsentinel-indeed` (Indeed only)
- `jobsentinel-naukri` (Naukri only)
- `dashboard` (UI)

Start specific services:
```powershell
docker-compose up -d jobsentinel-linkedin dashboard
docker-compose up -d jobsentinel-indeed
docker-compose up -d jobsentinel-naukri
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
platforms:
  enabled:
    - linkedin
    # - indeed
```

### Dashboard toggles

The dashboard has toggles for:
- Platform on/off (LinkedIn, Indeed, Naukri)
- AI filter on/off

These toggles update `configs/settings.yaml`.

Service controls are available in the dashboard for local Docker start/stop.

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
