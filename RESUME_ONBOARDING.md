# Resume-Based Onboarding - Implementation Guide

## Overview

Resume-based onboarding has been successfully implemented in Job Sentinel. Users can now upload their resume to automatically populate their profile.

---

## Features Implemented

### 1. Resume Parser Module (`src/ai/resume_parser.py`)
- Extracts structured data from PDF, DOCX, and TXT files
- Uses regex patterns for basic extraction
- Enhanced with LLM (Groq/OpenAI) for better accuracy
- Extracts: name, email, phone, skills, experience, education, LinkedIn, GitHub, current company, role

### 2. Extended Profile Store (`src/ai/profile_store.py`)
- `init_profile_from_resume()` - Initialize profile from parsed resume data
- `update_profile_fields()` - Update specific profile fields
- `get_missing_fields()` - Identify missing critical fields

### 3. CLI Onboarding (`src/cli/onboard.py`)
- Command: `python -m src.cli.onboard --resume <path> [--name <profile_name>]`
- Interactive flow:
  1. Parse resume
  2. Display extracted data
  3. User verification/editing
  4. Prompt for missing fields
  5. Save profile

### 4. Dashboard Integration (`dashboard/`)
- Resume upload form in profile page
- Auto-fills profile fields after parsing
- User can review and edit extracted data
- Endpoint: `POST /upload-resume`

---

## Usage

### CLI Method

```bash
# Basic usage
python -m src.cli.onboard --resume path/to/resume.pdf

# With custom profile name
python -m src.cli.onboard --resume resume.pdf --name john_doe
```

### Dashboard Method

1. Navigate to Profile page
2. Click "Upload Resume" section at top
3. Select resume file (PDF, DOCX, or TXT)
4. Click "Parse Resume"
5. Review extracted data
6. Edit any fields as needed
7. Click "Save profile"

---

## Architecture

```
Resume Upload
    ↓
resume_parser.py (extract text + parse with LLM/regex)
    ↓
profile_store.py (init_profile_from_resume)
    ↓
User Verification (CLI or Dashboard)
    ↓
profile_store.py (save_profile)
    ↓
controller.py (load_profile) → AI Agents → Form Filler → Apply
```

---

## Dependencies

Required packages:
- `PyPDF2` - for PDF parsing
- `python-docx` - for DOCX parsing
- `openai` - for LLM-based extraction (if using Groq/OpenAI)

Install:
```bash
pip install PyPDF2 python-docx openai
```

---

## Configuration

Set API key in `.env` for enhanced parsing:
```
GROQ_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
```

If no API key is set, falls back to regex-only parsing.

---

## Profile Fields Extracted

- **Basic Info**: name, email, phone
- **Professional**: role, current_company, experience, education
- **Skills**: skills (list)
- **Links**: linkedin_url, github_url, portfolio_url

### Fields Requiring Manual Input
- Preferred location
- Preferred roles/keywords
- Work preferences (authorization, sponsorship, relocation, etc.)
- Salary expectations

---

## Integration Points

### Existing Systems
✓ Profile system (`profile_store.py`) - extended, not replaced
✓ Form filler (`form_filler.py`) - uses profile data automatically
✓ AI agents (`agents.py`) - uses profile for job evaluation
✓ Controller (`controller.py`) - loads profile at start of cycle
✓ Dashboard (`app.py`) - integrated upload endpoint

### Backward Compatibility
✓ Existing profiles continue to work
✓ Manual profile creation still supported
✓ No breaking changes to existing modules

---

## Testing

### Test CLI Onboarding
```bash
python -m src.cli.onboard --resume test_resume.pdf
```

### Test Dashboard Upload
1. Start dashboard: `python -m dashboard.app`
2. Navigate to http://localhost:5000/profile
3. Upload resume via form

---

## Future Enhancements

- Multi-file resume support (cover letter + resume)
- Resume version history
- Auto-update profile from LinkedIn
- Batch resume processing
- Resume quality scoring

---

## Troubleshooting

**Issue**: "PyPDF2 not installed"
- Solution: `pip install PyPDF2`

**Issue**: "Failed to extract PDF text"
- Solution: Ensure PDF is text-based, not scanned image

**Issue**: "LLM parsing failed"
- Solution: Check API key in `.env`, falls back to regex parsing

**Issue**: "No data extracted"
- Solution: Try different file format or check resume formatting

---

## Files Modified/Created

### Created
- `src/ai/resume_parser.py` - Resume parsing logic
- `src/cli/onboard.py` - CLI onboarding interface
- `src/cli/__init__.py` - CLI package marker

### Modified
- `src/ai/profile_store.py` - Added resume integration functions
- `dashboard/app.py` - Added upload endpoint
- `dashboard/templates/profile.html` - Added upload form

### Unchanged (Integration Points)
- `src/ai/form_filler.py` - Already uses profile data
- `src/core/controller.py` - Already loads profile
- `src/core/config.py` - Profile loading logic intact
