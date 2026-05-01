# Multi-Agent Coordination System - Implementation Guide

## Overview

The Job Sentinel system has been upgraded with a **multi-agent coordinated job application engine** where specialized agents communicate and delegate tasks dynamically.

---

## Architecture

### Agent Flow

```
Job → Evaluator Agent → Application Agent
                ↓
        Navigation Agent → Form Detection Agent → Form Filler Agent → Submit
                ↓                    ↓                    ↓
        Recovery Agent ← ← ← ← ← ← ← ← (on failure)
```

### Agent Delegation

Agents can delegate to each other based on context:
- **Navigation fails** → Recovery Agent
- **Auth required** → Recovery Agent
- **Form detected** → Form Filler Agent
- **Submission fails** → Recovery Agent (retry logic)

---

## Components

### 1. Task Context (`src/ai/task_context.py`)

Shared state object passed between all agents:

```python
TaskContext:
  - job_id, job_key, platform
  - URLs (source, apply, company, current)
  - Status tracking
  - Detection flags (form, auth, captcha, redirect)
  - Form fields (detected, filled, missing)
  - Execution tracking (attempts, errors, retries)
  - Results (submission status, confirmation)
```

### 2. Specialized Agents (`src/ai/agents.py`)

#### NavigationAgent
- Handles navigation to apply URLs
- Detects external redirects
- Identifies company career pages
- Detects authentication requirements

#### FormDetectionAgent
- Scans DOM for forms
- Identifies input fields, selects, file uploads
- Extracts field metadata (type, name, label, required)
- Maps form structure to task context

#### RecoveryAgent
- Handles failures with recovery strategies
- Manages retry logic
- Handles auth requirements
- Detects and reports CAPTCHAs
- Implements fallback strategies

#### AgentOrchestrator
- Coordinates all agents
- Manages delegation flow
- Tracks state transitions
- Logs agent interactions
- Integrates with existing form_filler

### 3. Multi-Agent Wrapper (`src/ai/multi_agent_wrapper.py`)

Integration layer between orchestrator and controller:
- `apply_with_agents_sync()` - Main entry point
- `test_navigation_only()` - Debug/testing function
- Handles browser context management
- Maps results to controller format

### 4. Controller Integration (`src/core/controller.py`)

Multi-agent mode is opt-in via settings:

```python
use_multi_agent = settings.get("ai", {}).get("use_multi_agent", False)

if use_multi_agent:
    result = apply_with_agents_sync(job, profile, settings, platform)
else:
    result = apply_fn(job, resume_path, settings)  # existing flow
```

---

## Configuration

Enable multi-agent mode in `configs/settings.yaml`:

```yaml
ai:
  use_multi_agent: true  # Enable coordinated multi-agent system
  use_agents: true       # Enable AI agents for evaluation
  use_llm: true
  llm_model: "llama3.2:latest"
```

---

## Features

### 1. Dynamic Navigation
- Follows external redirects automatically
- Detects company career pages
- Updates context with navigation state

### 2. Intelligent Form Detection
- Scans all form elements
- Identifies required vs optional fields
- Extracts field metadata for smart filling

### 3. Integrated Form Filling
- Uses existing `form_filler.py` module
- Passes detected fields + profile data
- Dynamically fills based on field types

### 4. Recovery Strategies
- **Auth Required**: Flags for manual login
- **CAPTCHA Detected**: Flags for manual intervention
- **No Forms Found**: Searches for apply buttons
- **Submission Failed**: Retries with backoff (max 2 retries)

### 5. Comprehensive Logging
- Logs each agent transition
- Tracks all attempts and errors
- Records delegation flow
- Provides detailed failure reasons

---

## Usage

### Enable Multi-Agent Mode

1. Update `configs/settings.yaml`:
```yaml
ai:
  use_multi_agent: true
```

2. Run controller:
```bash
python -m src.core.controller
```

### Test Navigation Only

```python
from src.ai.multi_agent_wrapper import test_navigation_only
import asyncio

result = asyncio.run(test_navigation_only(job, profile, settings, platform))
print(result["task_context"])
```

---

## Agent Communication Protocol

### Delegation Flow

1. **NavigationAgent** navigates to URL
   - Success → delegate to FormDetectionAgent
   - Failure → delegate to RecoveryAgent

2. **FormDetectionAgent** scans for forms
   - Forms found → delegate to FormFillerAgent
   - No forms → delegate to RecoveryAgent

3. **FormFillerAgent** fills and submits
   - Success → mark completed
   - Failure → delegate to RecoveryAgent

4. **RecoveryAgent** handles failures
   - Can retry → delegate back to appropriate agent
   - Max retries reached → mark failed
   - Manual intervention needed → mark for review

### State Tracking

Each agent records attempts in task context:

```python
task_context.add_attempt(
    agent_type=AgentType.NAVIGATOR,
    action="navigate_to_apply_url",
    result="success",
    metadata={"redirected_to": url}
)
```

---

## Return Values

Multi-agent system returns tuple: `(status, easy_apply_flag)`

**Status values:**
- `"applied"` - Successfully submitted
- `"review"` - Needs manual intervention (auth/captcha)
- `"skipped"` - Failed after retries
- `"failed"` - Unexpected error

**Easy Apply Flag:**
- `True` - Used platform's easy apply
- `False` - Used external form
- `None` - Unknown/not applicable

---

## Error Handling

### Automatic Recovery
- Navigation failures → retry once
- Form submission failures → retry twice
- Temporary errors → exponential backoff

### Manual Intervention Required
- Authentication required
- CAPTCHA detected
- No forms or apply buttons found

### Logging
All errors logged to task context:
```python
task_context.errors = [
    "[timestamp] Navigation failed: timeout",
    "[timestamp] Form submission failed: network error"
]
```

---

## Backward Compatibility

✓ Existing platform apply functions still work
✓ Multi-agent mode is opt-in via settings
✓ Falls back to traditional flow if disabled
✓ No breaking changes to existing modules

---

## Testing

### Test Multi-Agent Flow

```bash
# Enable multi-agent mode
# Edit configs/settings.yaml: use_multi_agent: true

# Run controller
python -m src.core.controller

# Check logs for agent transitions
# Look for: [Orchestrator], [MultiAgent], [Controller]
```

### Debug Navigation

```python
from src.ai.multi_agent_wrapper import test_navigation_only
from src.ai.task_context import create_task_context

job = {
    "job_key": "test123",
    "job_url": "https://example.com/jobs/123",
    "title": "Test Job",
    "company": "Test Company"
}

result = asyncio.run(test_navigation_only(job, profile, settings, "linkedin"))
print(result["task_context"]["attempts"])
```

---

## Performance

### Advantages
- Handles external redirects automatically
- Detects and adapts to different form structures
- Recovers from transient failures
- Reduces manual intervention

### Considerations
- Slightly slower than direct apply (due to detection steps)
- Requires browser automation (Playwright)
- LLM calls for agent decisions (optional)

---

## Future Enhancements

- Multi-page form handling
- File upload automation (resume, cover letter)
- Dynamic field value generation
- Learning from successful applications
- Parallel application processing
- Integration with more platforms

---

## Files Modified/Created

### Created
- `src/ai/task_context.py` - Shared task context structure
- `src/ai/multi_agent_wrapper.py` - Integration wrapper

### Modified
- `src/ai/agents.py` - Added NavigationAgent, FormDetectionAgent, RecoveryAgent, enhanced AgentOrchestrator
- `src/core/controller.py` - Added multi-agent mode integration

### Unchanged (Integration Points)
- `src/ai/form_filler.py` - Used by FormFillerAgent
- `src/core/browser.py` - Used for browser context
- Platform-specific apply functions - Still available as fallback

---

## Troubleshooting

**Issue**: "Multi-agent mode not activating"
- Solution: Check `configs/settings.yaml` has `use_multi_agent: true`

**Issue**: "Navigation timeout"
- Solution: Increase timeout in NavigationAgent or check network

**Issue**: "Forms not detected"
- Solution: Check if page uses non-standard form structure, may need manual apply

**Issue**: "Auth required loop"
- Solution: Ensure platform session is valid, login manually first

---

## Design Principles

1. **Agents communicate, don't execute blindly**
2. **Delegation based on context, not hardcoded flow**
3. **Recovery is built-in, not an afterthought**
4. **State is shared, decisions are distributed**
5. **Existing modules are reused, not replaced**
