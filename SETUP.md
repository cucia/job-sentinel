# Setup

This file contains the full installation and run steps for JobSentinel.

## 1) Create sessions (interactive login)

```powershell
python -m core.session linkedin https://www.linkedin.com/login
python -m core.session indeed https://www.indeed.com/account/login
python -m core.session naukri https://www.naukri.com/nlogin/login
```

This opens a browser. Log in and press Enter in the terminal to save:
- `sessions/linkedin.json`
- `sessions/indeed.json`
- `sessions/naukri.json`

## 2) Start services

LinkedIn + dashboard:
```powershell
docker-compose up -d jobsentinel-linkedin dashboard
```

Indeed (optional):
```powershell
docker-compose up -d jobsentinel-indeed
```

Naukri (optional):
```powershell
docker-compose up -d jobsentinel-naukri
```

All platforms (optional):
```powershell
docker-compose up -d jobsentinel-linkedin jobsentinel-indeed jobsentinel-naukri
```

Dashboard: http://localhost:5000

## 3) Resume path

Place your resume at:
```
resumes/resume.pdf
```

Or change `configs/settings.yaml`:
```yaml
app:
  resume_path: resumes/resume.pdf
```

## 4) Optional settings

Key switches in `configs/settings.yaml`:
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

## 5) Logs

View logs per service:
```powershell
docker-compose logs -f jobsentinel-linkedin
docker-compose logs -f dashboard
```
