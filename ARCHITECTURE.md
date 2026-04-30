# JobSentinel Architecture

**Version:** 2.0 (Multi-Agent System)  
**Last Updated:** 2026-04-30

---

## Overview

JobSentinel is an intelligent job application automation system built on a multi-agent architecture. The system uses specialized AI agents that coordinate through a shared context to handle complex job application workflows.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Dashboard (Flask + WebSocket)                           │  │
│  │  - Command Center  - Analytics  - Jobs  - Sessions      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Controller Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Main Pipeline (controller.py)                           │  │
│  │  - Job Collection  - Evaluation  - Application          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent AI Layer                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agent Orchestrator                                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │ Evaluator  │  │ Navigator  │  │  Form      │        │  │
│  │  │   Agent    │→ │   Agent    │→ │ Detector   │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │         ↓               ↓               ↓               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │   Form     │  │  Recovery  │  │  Review    │        │  │
│  │  │  Filler    │  │   Agent    │  │   Agent    │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │                                                          │  │
│  │  Shared: TaskContext (state coordination)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Platform Integration Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   LinkedIn   │  │    Indeed    │  │    Naukri    │         │
│  │  - Collector │  │  - Collector │  │  - Collector │         │
│  │  - Apply     │  │  - Apply     │  │  - Apply     │         │
│  │  - Enricher  │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data & Storage Layer                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite Database (jobsentinel.db)                        │  │
│  │  - jobs  - decisions  - feedback  - model_state         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  File Storage                                            │  │
│  │  - Sessions  - Logs  - Profiles  - Resumes              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Cloud AI   │  │   Ollama     │  │  Playwright  │         │
│  │  (Groq, etc) │  │   (Local)    │  │  (Browser)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Dashboard (UI Layer)

**Technology:** Flask + WebSocket + Jinja2 Templates

**Components:**
- `dashboard/app.py` - Main Flask application
- `dashboard/templates/` - HTML templates
- `dashboard/static/` - CSS/JS assets
- `dashboard/websocket_handler.py` - Real-time updates

**Features:**
- Command Center with live agent monitoring
- Analytics dashboard with charts
- Job management (list, filter, bulk actions)
- Session management
- Profile editor with resume upload
- System logs viewer

**Communication:**
- REST API for CRUD operations
- WebSocket for real-time updates
- Server-Sent Events for notifications

---

### 2. Controller (Pipeline Layer)

**File:** `src/core/controller.py`

**Responsibilities:**
- Job collection orchestration
- Pipeline mode management (queue vs direct_latest)
- AI evaluation coordination
- Application execution
- Daily limit enforcement
- Error handling and logging

**Pipeline Modes:**

1. **Queue Mode** (Traditional)
   - Collect → Enqueue → Evaluate → Apply
   - Jobs processed in FIFO order
   - Good for continuous operation

2. **Direct Latest Mode** (Optimized)
   - Collect → Select Latest → Evaluate → Apply
   - Prioritizes recent jobs
   - Better for competitive markets

**Flow:**
```
Collect Jobs → Filter (Entry Level, Policy) → AI Evaluate → 
Filter (Quality, Visibility, Diversity) → Prioritize → Apply
```

---

### 3. Multi-Agent AI System

**File:** `src/ai/agents.py`

#### Agent Architecture

Each agent is a specialized class inheriting from `BaseAgent`:

```python
class BaseAgent:
    def __init__(self, profile: dict, settings: dict)
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str
```

#### Agents

**1. JobEvaluatorAgent**
- **Purpose:** Evaluate job-candidate match
- **Input:** Job details, candidate profile
- **Output:** Decision (APPLY/REJECT/REVIEW), score, confidence, reasoning
- **Prompt Engineering:** Structured evaluation criteria

**2. ApplicationAgent**
- **Purpose:** Plan application strategy
- **Input:** Job, evaluation result
- **Output:** Strategy (easy_apply/manual/skip), priority, estimated time
- **Logic:** Considers Easy Apply availability, match quality

**3. ReviewAgent**
- **Purpose:** Analyze borderline cases
- **Input:** Job, evaluation result
- **Output:** Review reason, questions, recommendation, key points
- **Use Case:** Human decision support

**4. StrategyAgent**
- **Purpose:** Prioritize job batches
- **Input:** List of (job, evaluation) tuples
- **Output:** Prioritized list with rankings
- **Logic:** Considers score, Easy Apply, recency, company reputation

**5. NavigationAgent**
- **Purpose:** Handle page navigation
- **Input:** TaskContext, Playwright page
- **Output:** Navigation result, detected URLs
- **Features:** Redirect detection, ATS detection, auth detection

**6. FormDetectionAgent**
- **Purpose:** Detect and analyze forms
- **Input:** TaskContext, Playwright page
- **Output:** Detected fields with metadata
- **Features:** ATS-specific mapping, generic fallback

**7. RecoveryAgent**
- **Purpose:** Handle failures
- **Input:** TaskContext, page, failure reason
- **Output:** Recovery strategy
- **Strategies:** Retry, wait, manual intervention, skip

**8. AgentOrchestrator**
- **Purpose:** Coordinate agent workflows
- **Method:** `execute_application(task_context, page)`
- **Flow:** Navigate → Detect Form → Fill Form → Submit → Verify

#### Task Context

**File:** `src/ai/task_context.py`

Shared state object passed between agents:

```python
@dataclass
class TaskContext:
    # Identification
    job_id: str
    job_key: str
    platform: str
    
    # URLs
    source_url: str
    apply_url: Optional[str]
    current_url: Optional[str]
    
    # State
    status: TaskStatus
    current_agent: Optional[str]
    
    # Detection
    form_detected: bool
    auth_required: bool
    captcha_detected: bool
    
    # Form data
    detected_fields: List[FormField]
    filled_fields: List[str]
    missing_fields: List[str]
    
    # Execution
    attempts: List[AgentAttempt]
    errors: List[str]
    retry_count: int
    
    # Results
    submission_successful: bool
    confirmation_message: Optional[str]
```

---

### 4. Intelligent Filtering System

**Components:**

**Quality Scorer** (`src/ai/quality_scorer.py`)
- Evaluates skill match, role alignment, experience fit
- Returns overall score and quality tier (A/B/C/D)

**Shortlist Predictor** (`src/ai/shortlist_predictor.py`)
- Predicts probability of getting shortlisted
- Uses quality score + job metadata

**Adaptive Strategy** (`src/ai/adaptive_strategy.py`)
- Decides whether to apply based on quality and probability
- Learns from outcomes over time

**Feedback Learner** (`src/ai/feedback_learner.py`)
- Tracks application outcomes
- Provides confidence boosts for similar jobs

**Visibility Predictor** (`src/ai/visibility_predictor.py`)
- Optimizes application timing
- Considers hour of day, day of week, platform, competition

**Diversity Controller** (`src/ai/diversity_controller.py`)
- Ensures application diversity
- Prevents over-concentration in one area

---

### 5. Form Automation System

**Form Filler** (`src/ai/form_filler.py`)
- Fills application forms with profile data
- Handles text, select, file, checkbox inputs
- Uses ATS-specific field mappings

**Field Maps** (`src/ai/field_maps.py`)
- ATS-specific field selectors
- Supported: Greenhouse, Lever, Workday, Taleo, iCIMS, etc.
- Fallback to generic detection

**Human Behavior** (`src/ai/human_behavior.py`)
- Simulates human-like delays
- Random mouse movements
- Typing speed variation

**Verification** (`src/ai/verification.py`)
- Verifies submission success
- Checks success messages, URLs, errors
- Returns confidence score

---

### 6. Platform Integration Layer

**Structure:**
```
src/platforms/<platform>/
├── collector.py  # Job collection
├── apply.py      # Application logic
├── enricher.py   # Job enrichment (optional)
└── __init__.py
```

**Collector Responsibilities:**
- Search for jobs based on keywords
- Extract job details (title, company, location, etc.)
- Detect Easy Apply availability
- Return standardized job dict

**Apply Responsibilities:**
- Navigate to job application page
- Fill application form
- Submit application
- Return status (applied/review/skipped)

**Enricher Responsibilities:**
- Fetch additional job details
- Extract full description
- Return enriched fields

---

### 7. Data Layer

**Database** (`src/core/storage.py`)

**Schema:**
```sql
CREATE TABLE jobs (
    job_key TEXT PRIMARY KEY,
    platform TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    description TEXT,
    job_url TEXT,
    status TEXT,  -- queued, applied, review, rejected, skipped, deferred
    easy_apply INTEGER,
    score INTEGER,
    decision TEXT,
    feedback_label TEXT,
    ai_result TEXT,  -- JSON
    posted_at TEXT,
    posted_text TEXT,
    created_at TEXT,
    updated_at TEXT,
    applied_at TEXT
);

CREATE TABLE decisions (
    job_key TEXT,
    decision TEXT,
    score INTEGER,
    timestamp TEXT
);

CREATE TABLE feedback (
    job_key TEXT,
    label TEXT,  -- approved, rejected, applied
    source TEXT,  -- dashboard, bulk, quick
    timestamp TEXT
);

CREATE TABLE model_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**File Storage:**
- `sessions/<platform>.json` - Browser sessions
- `data/jobsentinel.log` - Application logs
- `profiles/<name>.yaml` - Candidate profiles
- `resumes/<name>.pdf` - Resume files

---

## Data Flow

### Job Collection Flow

```
1. Controller calls platform collector
2. Collector searches job board
3. Collector extracts job details
4. Collector returns list of jobs
5. Controller deduplicates by job_key
6. Controller stores in database
```

### Evaluation Flow

```
1. Controller loads job from database
2. Controller calls JobEvaluatorAgent
3. Agent constructs evaluation prompt
4. Agent calls LLM (cloud or local)
5. Agent parses LLM response
6. Agent returns decision dict
7. Controller applies filters (quality, visibility, diversity)
8. Controller updates job status
```

### Application Flow (Multi-Agent)

```
1. Controller calls AgentOrchestrator.execute_application()
2. Orchestrator creates TaskContext
3. NavigationAgent navigates to apply URL
4. NavigationAgent detects ATS type
5. FormDetectionAgent scans for forms
6. FormDetectionAgent uses ATS-specific mapping
7. FormFillerAgent fills form fields
8. FormFillerAgent simulates human behavior
9. FormFillerAgent submits form
10. VerificationAgent checks submission
11. RecoveryAgent handles failures (if any)
12. Orchestrator returns final result
13. Controller updates database
```

---

## Configuration System

**File:** `configs/settings.yaml`

**Structure:**
```yaml
app:
  # Pipeline settings
  run_interval_seconds: 60
  pipeline_mode: direct_latest
  apply_all: true
  
  # Filtering
  use_ai: true
  entry_level_only: false
  easy_apply_first: true

ai:
  # Multi-agent system
  use_agents: true
  
  # Cloud AI
  use_cloud: true
  provider: groq
  model: llama-3.1-70b-versatile
  
  # Local AI
  use_llm: false
  llm_model: llama3.2:latest
  
  # Scoring
  min_score: 70
  uncertainty_margin: 5
  
  # Advanced filters
  use_quality_filter: true
  use_visibility_filter: true
  use_diversity_control: true

platforms:
  enabled:
    - linkedin
  
  sessions:
    linkedin: sessions/linkedin.json
  
  linkedin:
    search:
      keywords: [security]
      location: India
      max_results: 100

limits:
  daily_applications: 10

storage:
  db_path: data/jobsentinel.db
  history_limit: 400
```

---

## Security Considerations

### Session Management
- Sessions stored as encrypted cookies
- Automatic session validation
- Expiry detection and refresh

### Credential Handling
- API keys stored in environment variables
- No hardcoded credentials
- Secure file permissions

### Data Privacy
- Local SQLite database
- No data sent to external services (except AI providers)
- Resume files stored locally

### Browser Automation
- Headless mode for production
- VNC for debugging
- Automatic cleanup of browser instances

---

## Performance Optimization

### Caching
- LLM responses cached per job
- Session cookies cached
- Form field mappings cached

### Async Operations
- Playwright async API
- Concurrent job evaluation
- Background WebSocket updates

### Resource Management
- Browser instance pooling
- Database connection pooling
- Memory cleanup after each job

---

## Error Handling

### Retry Logic
- Exponential backoff for network errors
- Max 3 retries per job
- Different strategies per error type

### Recovery Strategies
- Auth required → Manual intervention
- CAPTCHA → Manual intervention
- Form not found → Try alternative selectors
- Submission failed → Retry with delay
- Network error → Wait and retry

### Logging
- Structured logging with context
- Error stack traces
- Agent attempt history in TaskContext

---

## Testing Strategy

### Unit Tests
- Agent logic
- Form detection
- Field mapping
- Verification logic

### Integration Tests
- Platform collectors
- Application flow
- Database operations

### End-to-End Tests
- Full pipeline execution
- Multi-agent coordination
- Dashboard functionality

---

## Deployment

### Local Development
```bash
python -m src.core.controller --platforms linkedin &
python -m dashboard.app
```

### Docker Deployment
```bash
docker-compose up -d
```

### Production Considerations
- Use headless mode
- Set up monitoring
- Configure log rotation
- Set daily limits
- Use cloud AI for reliability

---

## Future Architecture

### Planned Improvements

**Microservices**
- Separate services for collection, evaluation, application
- Message queue for job processing
- Distributed task execution

**API Layer**
- RESTful API for external integrations
- Webhook support for events
- OAuth for authentication

**Advanced AI**
- Fine-tuned models for job evaluation
- Reinforcement learning for strategy optimization
- Multi-modal analysis (job descriptions + company data)

**Scalability**
- Horizontal scaling with worker pools
- Redis for caching and queuing
- PostgreSQL for production database

---

**Last Updated:** 2026-04-30  
**Version:** 2.0
