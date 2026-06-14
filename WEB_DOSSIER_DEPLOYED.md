# Web Dossier Deployment - COMPLETE ✅

**Date**: 2026-06-09  
**Status**: Deployed and configuring  
**Build**: In progress (build #6)

---

## ✅ What We Just Deployed

### 1. Web Dossier Application
**File**: `agent/web_dossier.py` (copied from capture-the-flag repo)

**Features**:
- Password-protected web interface (HTTP Basic Auth)
- Lists all incidents from PostgreSQL database
- Shows detailed dossier for each incident
- **CTF Flag display**: When participant views their own IP's dossier
- Real-time database integration

### 2. Updated Agent Code
**File**: `agent/main.py`

**Changes**:
- ✅ Added `import os`
- ✅ Added `run_dossier_web_server()` function
- ✅ Starts dossier web server on port 8081 in background thread
- ✅ Runs alongside health check server (port 8080)

### 3. Kubernetes Resources

**Service**: `dossier-web`
```yaml
Service: dossier-web.cyber-riposte.svc.cluster.local
Port: 8081
Selector: app=mirror-agent
```

**OpenShift Route**: 
```
URL: https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
TLS: Edge termination
HTTP: Redirects to HTTPS
```

### 4. Agent Deployment Updates

**New ports**:
- 8080: Health checks (existing)
- 8081: Web dossier (new)

**New environment variables**:
```yaml
DOSSIER_PORT: "8081"
DOSSIER_PASSWORD: (from secret)
GITHUB_REPO: "hlipsig/capture-the-flag"  # Fixed!
```

---

## 🔐 Authentication Setup

### Credentials
- **Username**: `ctf` (hardcoded)
- **Password**: `i_would_prefer_not_to` (from Bartleby, the Scrivener)

### Where Tom Finds It
**File**: `/home/admin/.notes` on honeypot

```
=== Admin Notes ===
Last updated: 2026-06-04

Mirror Dossier Archive Access:
- URL: http://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
- Username: ctf
- Password: i_would_prefer_not_to

Bartleby would understand.

---
Other passwords to try (if first doesn't work):
- Hi_TOM!
- invisible_hand_1776
- creative_destruction
- wealth_of_nations

The scrivener's choice is the correct one.
```

---

## 🎯 CTF Flag Mechanism

### How It Works

1. **Participant triggers detection** → Incident created in database
2. **Participant explores honeypot** → Finds credentials in `.notes`
3. **Participant accesses dossier web** → Authenticates with discovered password
4. **Participant browses incidents** → Sees their own IP in the list
5. **Participant views own dossier** → **FLAG APPEARS!**

### Flag Format
```
flag{RIPOSTE_COUNTER_RECONNAISSANCE_<incident_id_suffix>}
```

Example:
```
Incident ID: INC-2024-0604-1537-abc123def
Flag: flag{RIPOSTE_COUNTER_RECONNAISSANCE_abc123def}
```

**Why it's unique**:
- Each incident has unique ID
- Flag includes last 8 characters of incident ID
- Prevents sharing flags between participants

---

## 🔄 Deployment Status

### Build Status
```bash
Build #6: In progress
Previous build #5: ✅ Completed successfully
```

### What's Building
- Updated `agent/main.py` with dossier web server
- New file `agent/web_dossier.py`
- Updated port configuration (8080 + 8081)

### After Build Completes
1. Agent pod will restart automatically
2. Two web servers will start:
   - Port 8080: Health checks (`/healthz`, `/readyz`)
   - Port 8081: Dossier web (`/`, `/dossiers`, `/dossiers/<id>`)
3. Route will become accessible at HTTPS URL

---

## 🧪 How to Test

### Test 1: Health Check
```bash
curl https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io/health
# Expected: {"status": "ok", "service": "dossier-web"}
```

### Test 2: Authentication Required
```bash
curl https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io/
# Expected: 401 Unauthorized with Basic Auth challenge
```

### Test 3: Access with Password
```bash
curl -u "ctf:i_would_prefer_not_to" \
  https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io/dossiers
# Expected: HTML page with incident list
```

### Test 4: Browser Access
1. Open: https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
2. Browser prompts for credentials
3. Username: `ctf`
4. Password: `i_would_prefer_not_to`
5. Should see incident list (empty if no incidents yet)

---

## 📋 Complete Secrets Configuration

| Secret Key | Value | Status |
|------------|-------|--------|
| **SHODAN_API_KEY** | `5izLcW3lPTVkJo...` | ✅ Configured |
| **GITHUB_TOKEN** | `github_pat_11AB5...` | ✅ Configured (fine-grained) |
| **GITHUB_REPO** | `hlipsig/capture-the-flag` | ✅ Configured |
| **DATABASE_URL** | `postgresql://...` | ✅ Configured |
| **DOSSIER_PASSWORD** | `i_would_prefer_not_to` | ✅ Configured |
| **SLACK_WEBHOOK_URL** | `placeholder` | ⚠️ Optional |

---

## 🎮 Tom's CTF Journey

### Stage 1: Reconnaissance (Normal CTF Stuff)
- Scans target
- Gets redirected to honeypot (via Istio - if configured)
- Or directly accesses honeypot (current state)

### Stage 2: Honeypot Exploration (Discovery)
- SSH into Cowrie honeypot
- Explores filesystem
- Finds `/home/admin/.notes`
- Discovers dossier URL + 5 password candidates

### Stage 3: The Literary Puzzle (Tom's Specialty!)
- Reads hints: "Bartleby", "scrivener's choice"
- Economics passwords are red herrings
- If knows Bartleby → instant win
- If not → Googles "Bartleby scrivener" → finds famous phrase

### Stage 4: Dossier Access (Revelation)
- Accesses https://dossiers-cyber-riposte.apps...
- Logs in with `ctf` / `i_would_prefer_not_to`
- **Sees list of ALL detected incidents**
- **Sees his own IP in the list** 😱

### Stage 5: The Flag (Victory!)
- Clicks on his own incident
- Sees full OSINT dossier about himself
- **Flag displays**: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_...}`
- Understands "The Mirror" concept: "I scanned them, they scanned me back"

---

## ⏭️ Next Steps

### After Build Completes (Automatic)
1. ✅ Agent pod restarts with new code
2. ✅ Dossier web server starts on port 8081
3. ✅ Route becomes accessible

### Manual Testing (Us)
1. Wait for build to complete
2. Check agent logs for "Starting web dossier server on port 8081"
3. Test route accessibility
4. Test authentication
5. Create test incident to verify database integration

### For Full CTF (Still Needed)
1. **Fix honeypots** - Cowrie/Glastopf need to run
2. **Plant `.notes` file** - In honeypot filesystem
3. **Create test incident** - So Tom sees something in dossier list
4. **Test end-to-end flow** - From scan → flag

---

## 📊 Deployment Architecture

```
┌─────────────────────────────────────┐
│  Tom's Browser                      │
│  https://dossiers-cyber-riposte...  │
└──────────────┬──────────────────────┘
               │
               │ HTTPS (TLS Edge)
               ▼
┌─────────────────────────────────────┐
│  OpenShift Router                   │
│  (Edge TLS Termination)             │
└──────────────┬──────────────────────┘
               │
               │ HTTP
               ▼
┌─────────────────────────────────────┐
│  Service: dossier-web               │
│  Port: 8081                         │
└──────────────┬──────────────────────┘
               │
               │
               ▼
┌─────────────────────────────────────┐
│  Pod: mirror-agent-xxx              │
│  ┌───────────────────────────────┐  │
│  │ Port 8080: Health Check       │  │
│  │ Port 8081: Web Dossier        │  │
│  │                               │  │
│  │ Flask App (web_dossier.py)    │  │
│  │  - HTTP Basic Auth            │  │
│  │  - PostgreSQL queries         │  │
│  │  - CTF flag generation        │  │
│  └───────┬───────────────────────┘  │
└──────────┼──────────────────────────┘
           │
           │ PostgreSQL Protocol
           ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  - incidents table                  │
│  - evidence table                   │
│  - audit_log table                  │
└─────────────────────────────────────┘
```

---

## 🎨 Password Puzzle Summary

**Real Password**: `i_would_prefer_not_to`  
**Literary Source**: Herman Melville's "Bartleby, the Scrivener" (1853)  
**Decoys**: 4 economics references + 1 obvious name reference  
**Hints**: "Bartleby would understand", "The scrivener's choice"

Perfect for Tom who loves:
- ✅ Classic literature (Melville is canon)
- ✅ Economics (decoys test if he gets distracted)
- ✅ Puzzles (requires reading comprehension, not brute force)

---

## 🚀 URL to Give Tom

When ready for CTF:

```
Target: https://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io

Hint: "Access requires credentials. Where would an admin keep notes?"
```

**DO NOT TELL HIM**:
- The password
- The username
- That his scan will be detected
- That he'll see himself in the dossier
- That this is "The Mirror" concept

Let him discover it all!

---

**Status**: Web Dossier deployed! Build in progress. Tom's literary adventure awaits. 🎭🪞
