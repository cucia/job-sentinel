# Session Creation Guide

## Overview

Create sessions manually using your real browser to bypass automation detection and Cloudflare.

---

## Why Manual Session Creation?

**The Problem:**
- Platforms detect automated browsers (Playwright, Selenium)
- Cloudflare blocks automation
- Can't sign in with automated tools

**The Solution:**
- You log in with your real browser (no detection)
- Export cookies using browser extension
- Save to session file
- Docker uses your real human session ✅

---

## Quick Start

### 1. Install Browser Extension

**Chrome/Edge:**
- Install [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)

**Firefox:**
- Install [Export Cookies](https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/)

### 2. Create Session for Each Platform

**LinkedIn:**
```powershell
# Get instructions
python scripts/create_session_linkedin.py

# Save session
python scripts/create_session_linkedin.py save
```

**Indeed:**
```powershell
# Get instructions
python scripts/create_session_indeed.py

# Save session
python scripts/create_session_indeed.py save
```

**Naukri:**
```powershell
# Get instructions
python scripts/create_session_naukri.py

# Save session
python scripts/create_session_naukri.py save
```

### 3. Run Docker

```bash
docker-compose up -d
```

Docker automatically loads sessions from `sessions/` folder.

---

## Detailed Steps

### Step 1: Get Instructions

```powershell
python scripts/create_session_naukri.py
```

This shows you the login URL and what to do.

### Step 2: Log In

- Open your browser
- Go to the platform's login page
- Log in normally
- Complete Cloudflare verification
- Complete 2FA if required
- Verify you see your dashboard

### Step 3: Export Cookies

**Using EditThisCookie (Chrome/Edge):**
1. Click the cookie icon in toolbar
2. Click the "Export" button (download icon)
3. Cookies copied to clipboard!

**Using Export Cookies (Firefox):**
1. Right-click on the page
2. Select "Export Cookies" > "Copy to Clipboard"

### Step 4: Save Session

```powershell
python scripts/create_session_naukri.py save
```

- Paste the cookies (Ctrl+V)
- Press Enter twice
- Session saved to `sessions/naukri.json`

### Step 5: Verify

```powershell
dir sessions\naukri.json
```

Should show the file exists (size > 1KB).

---

## How It Works

```
Your Browser (Real Human)
    ↓ login manually
    ↓ pass Cloudflare
    ↓ export cookies
sessions/naukri.json
    ↓ Docker reads this
Container (Automation)
    ↓ uses your real session
    ↓ platform trusts it
    ↓ applies to jobs ✅
```

**Key:** Platform sees legitimate session from real browser, so it doesn't block Docker automation!

---

## Files

### Session Scripts (Windows):
```
scripts/
├── create_session_linkedin.py   # LinkedIn session creator
├── create_session_indeed.py     # Indeed session creator
└── create_session_naukri.py     # Naukri session creator
```

### Session Files (Created):
```
sessions/
├── linkedin.json   # LinkedIn session
├── indeed.json     # Indeed session
└── naukri.json     # Naukri session
```

---

## Troubleshooting

### "Invalid JSON" Error

**Solution:**
- Make sure you used EditThisCookie extension
- Click the Export button (not just copy)
- Paste the entire JSON array

### Missing Required Cookies

**Solution:**
- Make sure you're fully logged in
- See your dashboard before exporting
- Try logging out and in again

### Session Not Working in Docker

**Solution:**
- Re-create the session (cookies may have expired)
- Make sure you completed Cloudflare verification
- Check file exists: `dir sessions\naukri.json`

---

## Session Lifespan

- **LinkedIn:** ~30 days
- **Indeed:** ~14 days
- **Naukri:** ~30 days

Re-create sessions when you see authentication errors.

---

## Security

### Session Files Contain:
- Login cookies (including Cloudflare)
- Authentication tokens
- Session identifiers

### Keep Them Safe:
- ✅ Already in `.gitignore`
- ✅ Not included in Docker images
- ✅ Stored locally only
- ⚠️ Don't share or commit

---

## Summary

**On Windows:**
- Python only (no automation software)
- Manual session creator scripts
- Your regular browser + extension

**In Docker:**
- Playwright + Firefox (containerized)
- All automation (containerized)
- Uses your session files

**Clean separation - automation stays in Docker!**
