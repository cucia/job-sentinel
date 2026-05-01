# Docker Build & Deployment Guide

## Prerequisites

1. Docker Desktop installed and running
2. Git repository cloned
3. In project directory: `C:\Users\qucia\Music\job-sentinel`

## Build & Start Services

### Option 1: Build and Start All Services

```powershell
# Navigate to project directory
cd C:\Users\qucia\Music\job-sentinel

# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Option 2: Build and Start Specific Services

```powershell
# Build and start Ollama (for LLM)
docker-compose up -d ollama

# Build and start Dashboard
docker-compose build dashboard
docker-compose up -d dashboard

# Build and start LinkedIn collector
docker-compose build jobsentinel-linkedin
docker-compose up -d jobsentinel-linkedin

# Build and start Indeed collector
docker-compose build jobsentinel-indeed
docker-compose up -d jobsentinel-indeed

# Build and start Naukri collector
docker-compose build jobsentinel-naukri
docker-compose up -d jobsentinel-naukri
```

## Post-Build Setup

### 1. Pull Ollama Model (Required for AI Agents)

```powershell
# Wait for Ollama to start (10 seconds)
Start-Sleep -Seconds 10

# Pull the LLM model
docker exec jobsentinel-ollama ollama pull llama3.2:latest

# Verify model is loaded
docker exec jobsentinel-ollama ollama list
```

### 2. Access Dashboard

Open browser: http://localhost:5000

### 3. Configure Profile

1. Go to http://localhost:5000/profile
2. Fill in your details:
   - Name, email, phone
   - Role and experience
   - Skills (comma-separated)
   - Keywords (comma-separated)

### 4. Login to Platforms

1. Go to http://localhost:5000/sessions
2. For each platform (LinkedIn, Indeed, Naukri):
   - Click "Start Login"
   - Login in the browser
   - Click "Save Session"
   - Click "Check Session" to verify

## Enable AI Agents

### Edit Configuration

```powershell
# Open settings file
notepad configs\settings.yaml
```

Change these lines:
```yaml
ai:
  use_llm: true      # Change from false to true
  use_agents: true   # Change from false to true
```

Save and restart services:
```powershell
docker-compose restart
```

## Verify Build

### Check Running Containers

```powershell
docker-compose ps
```

Expected output:
```
NAME                      STATUS
jobsentinel-ollama        Up
dashboard                 Up
jobsentinel-linkedin      Up (optional)
jobsentinel-indeed        Up (optional)
jobsentinel-naukri        Up (optional)
```

### Check Logs

```powershell
# Dashboard logs
docker-compose logs dashboard

# LinkedIn collector logs
docker-compose logs jobsentinel-linkedin

# Ollama logs
docker-compose logs ollama
```

### Test Dashboard

```powershell
# Test dashboard is responding
curl http://localhost:5000
```

## Troubleshooting

### Build Fails

```powershell
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Ollama Not Working

```powershell
# Check Ollama status
docker exec jobsentinel-ollama ollama list

# Restart Ollama
docker-compose restart ollama

# Pull model again
docker exec jobsentinel-ollama ollama pull llama3.2:latest
```

### Dashboard Not Loading

```powershell
# Check if port is in use
netstat -ano | findstr :5000

# Restart dashboard
docker-compose restart dashboard

# Check logs
docker-compose logs dashboard --tail 50
```

### Collectors Not Running

```powershell
# Check logs
docker-compose logs jobsentinel-linkedin --tail 50

# Restart collector
docker-compose restart jobsentinel-linkedin
```

## Docker Commands Reference

### Start/Stop

```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Stop specific service
docker-compose stop dashboard

# Start specific service
docker-compose start dashboard
```

### Logs

```powershell
# View all logs
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# Specific service logs
docker-compose logs dashboard

# Last 50 lines
docker-compose logs --tail 50
```

### Rebuild

```powershell
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build dashboard

# Rebuild without cache
docker-compose build --no-cache
```

### Clean Up

```powershell
# Stop and remove containers
docker-compose down

# Remove volumes too
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **dashboard** | 5000 | Web UI |
| **dashboard** | 6080 | VNC (browser automation) |
| **ollama** | 11434 | LLM server |
| **jobsentinel-linkedin** | - | LinkedIn job collector |
| **jobsentinel-indeed** | - | Indeed job collector |
| **jobsentinel-naukri** | - | Naukri job collector |

## Data Persistence

Data is stored in these locations:
- `./sessions/` - Platform login sessions
- `./data/` - Database and logs
- `ollama_data` - Docker volume for Ollama models

## Quick Start Commands

```powershell
# Full setup (run these in order)
cd C:\Users\qucia\Music\job-sentinel
docker-compose build
docker-compose up -d
Start-Sleep -Seconds 10
docker exec jobsentinel-ollama ollama pull llama3.2:latest
docker-compose ps

# Open dashboard
start http://localhost:5000
```

## Next Steps

1. ✅ Build Docker images
2. ✅ Start services
3. ✅ Pull Ollama model
4. ⬜ Configure profile
5. ⬜ Enable AI agents
6. ⬜ Login to platforms
7. ⬜ Start collecting jobs

---

**Note:** Run these commands in PowerShell or CMD, not in Git Bash.
