# JobSentinel

**AI-Powered Job Application Automation System**

JobSentinel is an intelligent job automation system that uses multi-agent AI to:
- 🤖 Collect jobs from multiple platforms (LinkedIn, Indeed, Naukri)
- 🧠 Evaluate jobs with specialized AI agents
- ⚡ Apply automatically with intelligent form filling
- 📊 Track everything in a modern AI Command Center dashboard
- 🎯 Optimize applications with quality filtering and visibility prediction

**Status:** ✅ Production Ready | **Version:** 2.0 (Multi-Agent System)

The system uses 8 specialized AI agents working in coordination to maximize your job search success.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/cucia/job-sentinel.git
cd job-sentinel

# 2. Run with Docker (recommended)
docker-compose up

# 3. Open dashboard
# Visit http://localhost:5000
```

**📚 Full documentation:** [docs/README.md](docs/README.md)

## 📖 Documentation

- **[Complete Documentation](docs/README.md)** - Full documentation index
- **[Quick Start Guide](docs/setup/QUICKSTART.md)** - Get started in 5 minutes
- **[System Ready Guide](docs/SYSTEM_READY.md)** - Production deployment
- **[Agent Optimizations](docs/architecture/AGENT_OPTIMIZATIONS.md)** - Performance details
- **[Session Management](docs/guides/SESSION_CREATION_GUIDE.md)** - Platform authentication

## 📊 Features

1. **Collect** - Scrape jobs from LinkedIn, Indeed, Naukri
2. **Evaluate** - AI agents analyze job-candidate fit with detailed reasoning
3. **Filter** - Quality scoring, visibility optimization, diversity control
4. **Apply** - Intelligent form filling with ATS-specific field mapping
5. **Verify** - Submission verification with confidence scoring
6. **Track** - Monitor everything in the AI Command Center dashboard

## 🤖 Multi-Agent AI System

JobSentinel uses 8 specialized AI agents:

1. **JobEvaluatorAgent** - Evaluates job-candidate match with detailed reasoning
2. **ApplicationAgent** - Plans optimal application strategy  
3. **ReviewAgent** - Analyzes borderline cases for human review
4. **StrategyAgent** - Prioritizes batches of jobs
5. **NavigationAgent** - Handles page navigation and redirects
6. **FormDetectionAgent** - Detects and analyzes application forms
7. **FormFillerAgent** - Fills forms with ATS-specific mapping
8. **RecoveryAgent** - Handles failures with intelligent recovery

Each agent specializes in one task and coordinates with others through a shared TaskContext.

## 🎯 Key Features

### Intelligent Application
- ✅ Multi-agent coordination for complex workflows
- ✅ ATS-specific field mapping (Greenhouse, Lever, Workday, etc.)
- ✅ Submission verification with confidence scoring
- ✅ Human behavior simulation (delays, mouse movements)
- ✅ Retry logic with exponential backoff
- ✅ CAPTCHA and auth detection

### Advanced Filtering
- ✅ Quality scoring (skill match, role alignment, experience fit)
- ✅ Shortlist probability prediction
- ✅ Visibility optimization (timing, platform, competition)
- ✅ Diversity control (role types, companies, locations)
- ✅ Adaptive strategy (learns from outcomes)
- ✅ Feedback learning (improves over time)

### Modern Dashboard
- ✅ AI Command Center with real-time monitoring
- ✅ Live agent activity feed
- ✅ Analytics with charts (pipeline, trends, platforms)
- ✅ Bulk actions (approve/reject multiple jobs)
- ✅ Resume upload with LLM parsing
- ✅ WebSocket live updates
- ✅ CSV export

### Cloud AI Integration
- ✅ 7 AI providers supported (Groq, OpenRouter, Gemini, etc.)
- ✅ FREE options available (14,400 req/day with Groq)
- ✅ Automatic fallback to local Ollama
- ✅ Easy provider switching

## 📁 Project Structure

```
src/
├── ai/                    # AI/ML layer (25 modules)
│   ├── agents.py         # Multi-agent system ⭐
│   ├── task_context.py   # Task coordination ⭐
│   ├── verification.py   # Submission verification ⭐
│   ├── field_maps.py     # ATS field mappings ⭐
│   ├── form_filler.py    # Form automation
│   ├── human_behavior.py # Human simulation
│   ├── cloud_llm.py      # Cloud AI integration
│   ├── resume_parser.py  # Resume parsing
│   ├── quality_scorer.py # Quality filtering
│   └── ...
├── core/                 # Business logic
│   ├── controller.py     # Main pipeline ⭐
│   ├── storage.py        # SQLite database
│   ├── config.py         # Settings management
│   └── ...
├── platforms/            # Platform integrations
│   ├── linkedin/
│   ├── indeed/
│   └── naukri/
└── services/
    └── session_manager.py
dashboard/               # Flask UI ⭐
├── app.py              # Main application
├── templates/          # HTML templates
└── static/             # CSS/JS assets
configs/                # Configuration files
data/                   # Database and logs
sessions/               # Platform sessions
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

## ⚙️ Configuration

All settings live in `configs/settings.yaml`:

```yaml
app:
  run_interval_seconds: 60
  apply_all: true
  use_ai: true              # Enable AI evaluation
  pipeline_mode: direct_latest
  easy_apply_first: true
  entry_level_only: false

ai:
  use_agents: true          # Enable multi-agent system ⭐
  use_cloud: true           # Use cloud AI providers ⭐
  provider: groq            # groq, openai, gemini, etc.
  model: llama-3.1-70b-versatile
  min_score: 70
  
  # Advanced filters
  use_quality_filter: true
  use_visibility_filter: true
  use_diversity_control: true

platforms:
  enabled:
    - linkedin
    # - indeed
    # - naukri
```

See `CLOUD_AI_SETUP.md` for cloud AI configuration and `FREE_AI_SETUP.md` for free provider options.

## 📊 Dashboard

Access the AI Command Center at `http://localhost:5000`

### Pages
- **Command Center** - Real-time agent monitoring and job queue
- **Analytics** - Charts and insights (pipeline, trends, platforms)
- **Jobs** - Browse jobs by status (applied, review, queued, etc.)
- **Sessions** - Manage platform login sessions
- **Profile** - Edit profile and upload resume
- **Automation** - Configure platforms and AI settings
- **Logs** - View system logs

### Features
- Real-time agent activity feed
- Bulk approve/reject actions
- Quick action buttons
- WebSocket live updates
- CSV export
- Resume upload with LLM parsing
- Modern dark theme UI

## 🧠 AI Configuration

### Cloud AI (Recommended)

JobSentinel supports 7 cloud AI providers with **FREE options**:

```yaml
ai:
  use_cloud: true
  provider: groq  # FREE: 14,400 requests/day
  model: llama-3.1-70b-versatile
```

**Free Providers:**
- **Groq** - 14,400 req/day FREE (recommended)
- **OpenRouter** - Gemini Flash FREE
- **Google Gemini** - 1,500 req/day FREE
- **Together AI** - $25 free credits

See `FREE_AI_SETUP.md` for setup instructions.

### Local AI (Ollama)

For offline use:

```yaml
ai:
  use_cloud: false
  use_llm: true
  llm_model: llama3.2:latest
```

1. Install Ollama: `https://ollama.ai`
2. Pull model: `ollama pull llama3.2`
3. Run: Model will be used automatically

## 📁 Data Storage

- **Database:** `data/jobsentinel.db` - SQLite database with jobs, decisions, feedback
- **Sessions:** `sessions/*.json` - Platform login sessions
- **Resume:** `resumes/resume.pdf` - Your resume for applications
- **Logs:** `data/jobsentinel.log` - Application logs
- **Profiles:** `profiles/*.yaml` - Candidate profiles

## 📤 Export

Download jobs as CSV from the dashboard:
- All jobs: `http://localhost:5000/export.csv`
- By status: `http://localhost:5000/export.csv?status=applied`
- By platform: `http://localhost:5000/export.csv?platform=linkedin`

## 📚 Documentation

- **SETUP.md** - Complete setup instructions
- **QUICKSTART.md** - Quick start guide
- **CLOUD_AI_SETUP.md** - Cloud AI configuration
- **FREE_AI_SETUP.md** - Free AI provider options
- **MULTI_AGENT_SYSTEM.md** - Multi-agent architecture
- **FEATURES.md** - Feature list
- **SYSTEM_STATUS.md** - Current system status ⭐

## 🐛 Troubleshooting

### AI not working
- Check `ai.use_cloud: true` in settings.yaml
- Verify API key is set in environment (GROQ_API_KEY, etc.)
- Check logs: `tail -f data/jobsentinel.log`

### Sessions expired
- Go to Sessions page in dashboard
- Click "Start Login" for the platform
- Complete login in VNC viewer
- Click "Save Session"

### No jobs found
- Check platform is enabled in settings.yaml
- Verify search keywords match your profile
- Check session is valid (green status in dashboard)

### Application failed
- Check logs for specific error
- Verify resume exists at `resumes/resume.pdf`
- Try manual application to test the job posting

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional platform integrations
- Enhanced ATS field mappings
- Improved verification logic
- Better error recovery strategies
- UI/UX enhancements

## 📄 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This tool is for personal use only. Always review applications before submission and comply with platform terms of service. Use responsibly and ethically.