# Changelog

All notable changes to JobSentinel are documented in this file.

## [2.0.0] - 2026-04-30

### 🎉 Major Release: Multi-Agent System

This release transforms JobSentinel into an intelligent multi-agent system with advanced AI capabilities.

### Added

#### Multi-Agent AI System
- **8 Specialized Agents** working in coordination:
  - JobEvaluatorAgent - Job-candidate matching with detailed reasoning
  - ApplicationAgent - Application strategy planning
  - ReviewAgent - Borderline case analysis
  - StrategyAgent - Batch prioritization
  - NavigationAgent - Page navigation and redirect handling
  - FormDetectionAgent - Form detection and analysis
  - FormFillerAgent - Intelligent form filling
  - RecoveryAgent - Failure recovery with retry logic
- **TaskContext** - Shared state object for agent coordination
- **AgentOrchestrator** - Coordinates multi-agent workflows

#### Advanced Application System
- ATS-specific field mapping (Greenhouse, Lever, Workday, Taleo, etc.)
- Submission verification with confidence scoring
- Human behavior simulation (delays, mouse movements)
- Retry logic with exponential backoff
- CAPTCHA and authentication detection
- External redirect handling
- Screenshot capture for uncertain cases

#### Intelligent Filtering
- Quality scoring (skill match, role alignment, experience fit)
- Shortlist probability prediction
- Visibility optimization (timing, platform, competition)
- Diversity control (role types, companies, locations)
- Adaptive strategy (learns from outcomes)
- Feedback learning (improves over time)

#### Modern Dashboard
- AI Command Center with real-time monitoring
- Live agent activity feed
- Analytics dashboard with charts (pipeline, trends, platforms)
- Agent performance metrics
- Bulk actions (approve/reject multiple jobs)
- Quick action buttons
- WebSocket live updates
- Modern dark theme UI
- Page-specific CSS styling

#### Resume Onboarding
- Resume upload (PDF, DOCX, TXT)
- LLM-powered resume parsing
- Automatic profile field extraction
- Skills and keywords detection
- Contact information extraction

#### Cloud AI Integration
- Support for configured cloud AI providers:
  - Groq (FREE - 14,400 req/day)
  - OpenRouter (FREE - Gemini Flash)
  - Google Gemini (FREE - 1,500 req/day)
  - Together AI ($25 free credits)
  - OpenAI (paid)
  - Anthropic (paid)
- Easy provider switching via configuration

#### Documentation
- SYSTEM_STATUS.md - Comprehensive system status report
- MULTI_AGENT_SYSTEM.md - Multi-agent architecture
- RELIABILITY_ENHANCEMENTS.md - Reliability improvements
- RESUME_ONBOARDING.md - Resume upload feature
- COMMAND_CENTER.md - Dashboard upgrade
- CLOUD_AI_SETUP.md - Cloud AI configuration
- FREE_AI_SETUP.md - Free AI provider options
- AI_AGENTS_STATUS.md - Agent system status

### Changed

#### Core Pipeline
- Refactored controller.py for multi-agent support
- Enhanced job evaluation with agent-based decision making
- Improved error handling and recovery
- Better logging with agent context

#### Dashboard
- Redesigned UI with modern dark theme
- Reorganized navigation with Command Center as default
- Enhanced analytics with multiple chart types
- Improved job listing with bulk actions
- Better session management UI
- Enhanced profile editor with resume upload

#### Configuration
- Added `ai.use_agents` flag for multi-agent system
- Added `ai.use_cloud` flag for cloud AI providers
- Added `ai.provider` and `ai.model` for cloud configuration
- Added advanced filter flags (quality, visibility, diversity)
- Simplified settings structure

### Fixed
- Form detection reliability issues
- Submission verification accuracy
- Session management edge cases
- Dashboard WebSocket connection stability
- CSV export with special characters
- Profile field parsing errors

### Performance
- Reduced API calls with intelligent caching
- Optimized form detection with ATS-specific mappings
- Improved page load times with async operations
- Better memory management with context cleanup

### Security
- Enhanced session storage security
- Improved credential handling
- Better error message sanitization
- Secure file upload validation

---

## [1.0.0] - 2026-04-20

### Initial Release

#### Core Features
- Multi-platform job collection (LinkedIn, Indeed, Naukri)
- SQLite database storage
- Basic AI-powered job evaluation
- Automatic application submission
- Session management
- Flask dashboard
- CSV export

#### AI Features
- Rule-based job scoring
- Heuristic job evaluation with optional cloud-backed agent scoring
- Keyword matching
- Experience level filtering

#### Dashboard
- Job listing by status
- Manual approve/reject
- Session management
- Profile editor
- System logs viewer

#### Platforms
- LinkedIn integration with Easy Apply
- Indeed integration
- Naukri integration

---

## Version History

- **2.0.0** (2026-04-30) - Multi-Agent System Release
- **1.0.0** (2026-04-20) - Initial Release

---

## Upgrade Guide

### From 1.0.0 to 2.0.0

1. **Update Configuration**
   ```yaml
   ai:
     use_agents: true      # Enable multi-agent system
     use_cloud: true       # Enable cloud AI
     provider: groq        # Choose provider
     model: llama-3.1-70b-versatile
   ```

2. **Install New Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Database Migration**
   - No migration needed - schema is backward compatible
   - New fields will be added automatically

4. **Update Docker**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

5. **Test the System**
   - Visit http://localhost:5000
   - Check Command Center for agent activity
   - Verify AI evaluation is working
   - Test resume upload feature

---

## Roadmap

### Planned Features

#### v2.1.0 (Q2 2026)
- [ ] Portal Scanner - Direct API integration with ATS systems
- [ ] Interview Preparation - STAR story generation
- [ ] Pattern Analysis - Success pattern identification
- [ ] Follow-up Manager - Application tracking and reminders

#### v2.2.0 (Q3 2026)
- [ ] Dynamic CV Generation - Tailored CVs per job
- [ ] Batch Processing - Parallel job evaluation
- [ ] Mobile App - iOS/Android companion app
- [ ] Email Integration - Application status tracking

#### v3.0.0 (Q4 2026)
- [ ] Multi-user Support - Team collaboration
- [ ] Advanced Analytics - ML-powered insights
- [ ] API Access - RESTful API for integrations
- [ ] Plugin System - Custom platform integrations

---

## Breaking Changes

### 2.0.0
- Dashboard default route changed from `/` to `/command-center`
- Settings structure changed - see upgrade guide
- Agent system requires configured cloud AI
- Some internal APIs refactored for multi-agent support

---

## Contributors

- **cucia** - Project creator and maintainer
- **Claude (Anthropic)** - AI assistant for development

---

## Acknowledgments

- Playwright team for browser automation
- AI provider teams for cloud model access
- Flask team for web framework
- All AI provider teams (Groq, OpenRouter, Google, etc.)

---

**Last Updated:** 2026-04-30
