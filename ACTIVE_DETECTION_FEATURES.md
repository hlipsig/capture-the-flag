# Active Detection Features - Build #9

**Status**: Implementing  
**Build**: #9 in progress  
**Features**: Option A (Pure Detection) + Rate Limiting

---

## 🚨 NEW: Active Detection (Option A)

The Mirror agent now **actively detects Tom's scans** in real-time!

### How It Works:

1. **Log-Based Detection**
   - Watches nginx access logs from the honeypot
   - Detects scan patterns in User-Agent headers
   - Detects high request rates (brute force)

2. **Automatic Incident Creation**
   - Creates incident with Tom's REAL IP
   - Stores in PostgreSQL database
   - Incident appears in dossier web

3. **OSINT Collection** (optional)
   - Can run Shodan lookup on Tom's IP
   - Stores results in database
   - Shows in dossier view

### Detection Patterns:

**User-Agent Signatures**:
- `Nmap Scripting Engine` → 98% confidence
- `nmap` → 90% confidence
- `gobuster`, `dirbuster`, `ffuf`, `wfuzz` → 95% confidence
- `nikto`, `sqlmap` → 98% confidence
- `Burp Suite`, `OWASP ZAP` → 85-95% confidence
- `python-requests`, `curl` → 65-70% confidence (lower confidence)

**Rate-Based Detection**:
- \>20 requests in 60 seconds → 85% confidence
- Signature: "High Request Rate Detected"

### Example Detection:

```
Tom runs: nmap -p 80,443 redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io

Log entry:
203.0.113.42 - - [11/Jun/2026:12:34:56] "GET / HTTP/1.1" 200 1234 "-" "Nmap Scripting Engine"

Detection:
🚨 DETECTION: 203.0.113.42 - ET SCAN Nmap Scripting Engine User-Agent Detected (confidence: 0.98)
✅ Incident created: INC-2026-06-11-123456-203011342
```

---

## 🔐 NEW: Rate Limiting (Option B Feature)

The dossier web now **rate-limits failed password attempts**!

### How It Works:

1. **Failed Attempt Tracking**
   - Records every failed password attempt
   - Tracks by IP address
   - Stores username + password tried

2. **Thresholds**:
   - **5 failed attempts** in **5 minutes** → Lockout
   - **Lockout duration**: **15 minutes**

3. **Responses**:
   - Attempts 1-4: Normal 401 Unauthorized
   - Attempt 5+: 429 Too Many Requests
   - During lockout: "Try again in X seconds"

4. **Special Logging**:
   - Logs decoy password attempts
   - Example: `🎭 203.0.113.42 tried decoy password: wealth_of_nations`

### Example:

```
Tom tries passwords:
1. Hi_TOM!                 → ❌ Failed (attempt #1)
2. wealth_of_nations       → ❌ Failed (attempt #2) 🎭 Decoy logged
3. invisible_hand_1776     → ❌ Failed (attempt #3) 🎭 Decoy logged
4. creative_destruction    → ❌ Failed (attempt #4) 🎭 Decoy logged
5. wrong_password          → ❌ Failed (attempt #5)
6. i_would_prefer_not_to   → 🚫 RATE LIMITED!

Response:
HTTP 429 Too Many Requests
Retry-After: 900
Body: "Too many failed attempts. Try again in 900 seconds.
       The mirror is watching your brute force attempts."

15 minutes later...
Tom tries: i_would_prefer_not_to → ✅ SUCCESS!
```

### Bypass:

Tom needs to **read the hints carefully** and try the correct password within the first 5 attempts!

If he tries all decoys first, he'll be locked out and have to wait 15 minutes.

**Strategy**: This encourages careful reading over brute force.

---

## 🎮 TOM'S NEW EXPERIENCE

### Before (Passive):
```
Tom scans → Nothing happens
Tom finds credentials → Pre-planted file
Tom accesses dossier → Sees generic test incident
Tom views incident → Gets flag
```

**Problem**: Tom doesn't see his own IP! Not a true "mirror"

### After (Active):
```
Tom scans with Nmap → 🚨 DETECTED in real-time!
Incident created → INC-2026-...-<Tom's-IP-hash>
Database stores → Tom's IP: 203.0.113.42

Tom finds credentials → Pre-planted file
Tom tries passwords → Logs each attempt
  - Try 1: Hi_TOM! → ❌ Logged
  - Try 2: wealth_of_nations → ❌ 🎭 Decoy logged
  - Try 3: i_would_prefer_not_to → ✅ SUCCESS!

Tom accesses dossier → Sees incident list
Tom notices → HIS OWN IP IS THERE! 😱

Tom clicks his incident → Sees dossier:
  - His IP address
  - His Nmap user-agent
  - Detection: "ET SCAN Nmap Scripting Engine"
  - Confidence: 98%
  - Timestamp: When he scanned
  - OSINT data: (Shodan results on his IP if enabled)
  - FLAG with his incident ID!

Tom realizes → "They scanned ME back!" 🪞
```

**Impact**: **TRUE MIRROR EXPERIENCE** - Counter-reconnaissance in action!

---

## 📊 Detection Implementation

### Log Detector (`agent/log_detector.py`)

```python
class LogDetector:
    - parse_log_line()       # Parse nginx access logs
    - detect_scan_pattern()  # Match user-agent signatures
    - detect_high_rate()     # Detect request flooding
    - analyze_log_line()     # Full analysis
```

### Rate Limiter (`agent/web_dossier.py`)

```python
# Global state
failed_attempts: Dict[str, List[tuple]] = {}

Functions:
- is_rate_limited()           # Check if IP is locked out
- record_failed_attempt()     # Log failed password
- requires_auth()             # Enhanced decorator with rate limiting
```

---

## 🔧 DEPLOYMENT STATUS

### Build #9 Changes:

1. **New file**: `agent/log_detector.py`
   - Log parsing and pattern matching
   - Incident creation on detection
   - OSINT integration hook

2. **Updated**: `agent/web_dossier.py`
   - Added rate limiting
   - Added failed attempt tracking
   - Enhanced logging for decoy passwords
   - Fixed database column names (detection_confidence)

3. **Database fixes**:
   - `confidence` → `detection_confidence`
   - `osint_data` → `attacker_info`

### After Build #9:

- ✅ Tom's scans will be detected in real-time
- ✅ Incidents created with his actual IP
- ✅ Failed passwords logged and rate-limited
- ✅ Dossier shows his actual reconnaissance
- ✅ True "mirror" experience achieved!

---

## 🧪 TESTING AFTER BUILD #9

### Test 1: Active Detection
```bash
# Trigger detection with Nmap user-agent
curl -A "Nmap Scripting Engine" \
  https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io/

# Check if incident was created
oc exec postgres-0 -n cyber-riposte -- \
  psql -U mirror_agent -d mirror_audit -c \
  "SELECT incident_id, attacker_ip, detection_signature FROM incidents ORDER BY first_seen DESC LIMIT 5;"
```

### Test 2: Rate Limiting
```bash
# Try 6 wrong passwords rapidly
for i in {1..6}; do
  curl -u "ctf:wrong_password_$i" \
    https://dossiers-cyber-riposte.apps.../dossiers
  echo "Attempt $i"
done

# Should get 429 on attempt 6
```

### Test 3: Decoy Logging
```bash
# Try decoy passwords
curl -u "ctf:wealth_of_nations" https://dossiers-cyber-riposte.apps.../

# Check agent logs for decoy detection
oc logs deployment/mirror-agent -n cyber-riposte | grep "🎭"
```

### Test 4: End-to-End
```bash
# Full Tom simulation
1. Scan with real Nmap: nmap -p 80,443 redteam-cyber-riposte.apps...
2. Wait 5 seconds for detection
3. Access dossier with correct password
4. See your own IP in incident list!
5. View dossier with your data
```

---

## ⚠️ KNOWN LIMITATIONS

### Log Watching Not Yet Integrated

The `log_detector.py` module is created but **not yet started** in `main.py`.

**To fully activate**, need to add to `agent/main.py`:

```python
# In main() function, after starting dossier web server:

# Start log detector thread (if log file exists)
log_file = os.getenv("HONEYPOT_LOG_FILE", "/var/log/honeypot/access.log")
if os.path.exists(log_file):
    from agent.log_detector import watch_logs_and_create_incidents
    log_thread = threading.Thread(
        target=watch_logs_and_create_incidents,
        args=(log_file, None, None),
        daemon=True
    )
    log_thread.start()
    logger.info(f"Log detector started on {log_file}")
```

**Alternative**: Manually create incidents when Tom scans (for immediate testing)

---

## 🎯 RECOMMENDED APPROACH

### For Immediate Testing (Manual Detection):

Since we don't have access to honeypot logs yet, use **manual incident creation**:

```python
# When Tom tells you he's scanning, create incident:
oc exec postgres-0 -n cyber-riposte -- psql -U mirror_agent -d mirror_audit -c "
INSERT INTO incidents (
  incident_id, attacker_ip, first_seen, last_updated,
  status, detection_signature, detection_confidence, actions_count
) VALUES (
  'INC-2026-06-11-TOM-scan001',
  'TOM_ACTUAL_IP_HERE',
  NOW(),
  NOW(),
  'active',
  'ET SCAN Nmap Scripting Engine User-Agent Detected',
  0.98,
  3
);"
```

Then Tom will see HIS IP in the dossier!

### For Full Automation (Future):

1. Deploy log aggregation (fluentd/fluent-bit)
2. Stream honeypot logs to agent
3. Enable log_detector thread
4. Real-time detection works automatically

---

## 📋 SUMMARY

| Feature | Status | Details |
|---------|--------|---------|
| **Active Detection** | ✅ Code ready | Detects scans via log analysis |
| **Rate Limiting** | ✅ Implemented | 5 attempts / 15 min lockout |
| **Decoy Logging** | ✅ Implemented | Logs when Tom tries decoys |
| **Database Fixes** | ✅ Fixed | Column names corrected |
| **Log Integration** | ⏳ Pending | Need to connect log source |
| **Manual Testing** | ✅ Ready | Can create incidents manually |

---

## 🎉 THE NEW EXPERIENCE

**Tom's Perspective**:

> "I scanned their server with Nmap... wait, why is MY IP in their incident database?! 
> They have my user-agent string! They know exactly what I did! 
> This isn't just a honeypot - they're literally watching ME and profiling MY actions!
> The 'Mirror' reflects my reconnaissance back at me. That's brilliant!"

**Mission Accomplished**: Counter-reconnaissance demonstrated! 🪞🎯

---

**Build #9 will enable Tom to see himself being watched!**
