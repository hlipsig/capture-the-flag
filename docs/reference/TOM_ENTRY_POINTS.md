# Tom's Entry Points - The Mirror CTF

**Target**: Reconnaissance challenge where every action is monitored

---

## 🎯 Primary Entry Point (HTTP/HTTPS)

### **Main Target URL**
```
https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
```

**What Tom sees**:
- Web application (Glastopf HTTP honeypot)
- Looks like a real vulnerable web app
- Has directories to enumerate
- Has forms to test for SQL injection
- Has `/robots.txt` with hints and decoy flags

**What Tom doesn't know**:
- This is actually a honeypot
- Every request is being logged
- HTTP headers, User-Agent, and scan patterns are being analyzed
- Once detected, his traffic could be redirected (if Istio is configured)

---

## 🔐 SSH Entry Point (TCP Port 22)

### **SSH Access via NodePort**
```bash
ssh root@<cluster-external-ip> -p 30022
```

**Cluster Access Points**:
- API endpoint domain: `api.uu7a1hfd.eastus.aroapp.io`
- Try: `ssh root@api.uu7a1hfd.eastus.aroapp.io -p 30022`

**OR via OpenShift Router** (if we expose it):
- We could create a TCP passthrough route for SSH
- More complex but cleaner for Tom

**What Tom will find**:
- Cowrie SSH honeypot
- Appears to be a Linux server
- Accepts common credentials (root/root, admin/admin, etc.)
- Fake filesystem with planted files
- `/home/admin/.notes` - **The key file with dossier password!**

---

## 📋 Tom's Discovery Flow

### **Option 1: Web-First (Recommended)**

1. **Nmap scan** → `https://redteam-cyber-riposte.apps...`
   ```bash
   nmap -p 80,443 redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
   ```

2. **Directory brute force** → Finds `/robots.txt`, `/admin`, etc.
   ```bash
   gobuster dir -u https://redteam-cyber-riposte.apps... \
     -w /usr/share/wordlists/dirb/common.txt
   ```

3. **Finds decoy flag** in `/robots.txt`
   - `flag{fake_n0t_the_real_fl4g}`
   - Tries to submit → Rejected

4. **Checks page source** → Finds hint about SSH access
   ```html
   <!-- SSH access: Try the API endpoint on port 30022 -->
   ```

5. **SSH to honeypot** → Finds `/home/admin/.notes`

6. **Access dossier web** → Gets real flag

---

### **Option 2: SSH-First (Aggressive)**

1. **Full port scan** → Discovers NodePort 30022
   ```bash
   nmap -p- api.uu7a1hfd.eastus.aroapp.io
   ```

2. **SSH brute force** → Gets in via common credentials
   ```bash
   hydra -l root -P /usr/share/wordlists/rockyou.txt \
     ssh://api.uu7a1hfd.eastus.aroapp.io:30022
   ```

3. **Explores filesystem** → Finds `/home/admin/.notes`

4. **Access dossier web** → Gets real flag

---

### **Option 3: Service Enumeration (Thorough)**

1. **DNS enumeration**
   ```bash
   dig redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
   dig dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
   ```

2. **Subdomain discovery** → Finds multiple services
   - `redteam-*` - Main target
   - `dossiers-*` - Requires password (gets curious)

3. **Tries dossier web** → Gets 401 Unauthorized
   - Hint in auth dialog: "Credentials in honeypot"

4. **Goes back to web/SSH** → Finds `.notes` file

5. **Solves password puzzle** → Access dossier → Flag

---

## 🕸️ What Tom Can Scan/Enumerate

### **Web Target** (`redteam-cyber-riposte`)

**Open to enumerate**:
- `/robots.txt` - Decoy flags and hints
- `/admin` - Fake admin panel
- `/api` - Fake API endpoints
- `/upload` - File upload vulnerability (fake)
- `/login` - SQL injection testing ground (logged)
- Headers, cookies, response times

**What triggers detection**:
- Nmap scans with aggressive flags
- User-Agent: Nmap/Nikto/sqlmap/Burp Suite
- Directory brute forcing (high request rate)
- SQL injection attempts
- XXE/SSRF/XSS payloads
- Known vulnerability scanners

---

### **SSH Honeypot** (`port 30022`)

**What Tom finds**:
```
/home/admin/
├── .notes                    ← PASSWORD + DOSSIER URL! 🎯
├── .secret_flag              ← Decoy: flag{YOU_GOT_HONEYPOTTED_lol}
├── .bash_history             ← Decoy password: creative_destruction
└── Documents/
    └── economics_papers.pdf  ← Bait for Tom (fake file)

/etc/
└── motd                      ← Hint: "Hi_TOM!" decoy password

/tmp/
└── backup_config.txt         ← Decoy password: mirror_reflect_6789

/var/log/
└── auth.log                  ← Fake login attempts from "bartleby" user
```

---

## 🚨 What Gets Detected

Every action Tom takes is logged and analyzed:

### **HTTP Requests**
```json
{
  "timestamp": "2026-06-09T22:00:00Z",
  "src_ip": "203.0.113.42",
  "request": "GET /admin HTTP/1.1",
  "user_agent": "Nmap Scripting Engine",
  "detected": true,
  "signature": "ET SCAN Nmap User-Agent",
  "confidence": 0.98
}
```

### **SSH Attempts**
```json
{
  "timestamp": "2026-06-09T22:05:00Z",
  "src_ip": "203.0.113.42",
  "service": "SSH",
  "username": "root",
  "password": "root",
  "detected": true,
  "signature": "SSH Brute Force Detected",
  "confidence": 0.85
}
```

### **What Happens After Detection**

1. **Incident Created** in PostgreSQL database
2. **OSINT Collected** on Tom's IP (Shodan, WHOIS, rDNS)
3. **GitHub Issue Created** (if enabled) in `hlipsig/capture-the-flag`
4. **Dossier Compiled** with all evidence
5. **Added to Dossier Web** - Tom can later see himself!

---

## 🎮 Tom's Optimal Path

```
1. Scan redteam-cyber-riposte.apps... (HTTP/HTTPS)
   ↓
2. Find /robots.txt with decoy flag + hint
   ↓
3. Notice comment in HTML about SSH on port 30022
   ↓
4. SSH brute force → Get into Cowrie honeypot
   ↓
5. Find /home/admin/.notes file
   ↓
6. Read 5 password candidates + literary hints
   ↓
7. Solve Bartleby puzzle → i_would_prefer_not_to
   ↓
8. Access https://dossiers-cyber-riposte.apps...
   ↓
9. Login with ctf / i_would_prefer_not_to
   ↓
10. See incident list → Sees his own IP! 😱
   ↓
11. Click his own incident → FLAG APPEARS! 🎯
   ↓
12. Realizes "The Mirror" scanned him back
```

---

## 📝 Instructions to Give Tom

### **Simple Version**:
```
Target: https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io

Your mission: Find the flag.

Note: Traditional CTF rules apply. All scanning/testing is authorized 
against this specific target only. Stay within scope.
```

### **Detailed Version** (if Tom gets stuck):
```
Target: https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io

Reconnaissance is expected. The system is hardened but intentionally 
has discoverable weaknesses. 

Hints:
- Check the usual suspects (/robots.txt, common ports)
- Credentials are often stored in insecure places
- Classic literature beats modern economics
- You're not the only one doing reconnaissance...

Flag format: flag{RIPOSTE_COUNTER_RECONNAISSANCE_xxxxxxxx}
```

---

## 🔧 Technical Setup Summary

| Component | URL/Access | Status |
|-----------|------------|--------|
| **HTTP Honeypot** | `https://redteam-cyber-riposte.apps...` | ✅ Route created |
| **SSH Honeypot** | `api.uu7a1hfd.eastus.aroapp.io:30022` | ✅ NodePort 30022 |
| **Dossier Web** | `https://dossiers-cyber-riposte.apps...` | ✅ Route created |
| **Glastopf Pod** | Running? | ⚠️ Check status (0/1 ready) |
| **Cowrie Pod** | Running? | ⚠️ Check status (0/1 ready) |
| **Mirror Agent** | Detecting? | 🔄 Build in progress |

---

## ⚠️ Current Gaps

1. **Honeypots not running** - Cowrie/Glastopf are 0/1 ready
   - Need to debug why they're failing
   - Tom can't find `.notes` file if Cowrie isn't running

2. **No events flowing** - Agent needs events to detect Tom
   - Option A: Deploy Kafka + Suricata (full IDS)
   - Option B: Manually create incidents for testing
   - Option C: Agent watches honeypot logs directly

3. **SSH NodePort may not be externally accessible**
   - OpenShift cluster might not expose NodePorts externally
   - May need LoadBalancer service or HAProxy config

---

## 🚀 Next Steps

1. **Fix honeypots** - Get Cowrie and Glastopf running
2. **Test HTTP route** - Verify `redteam-cyber-riposte` is accessible
3. **Test SSH access** - Verify port 30022 is reachable externally
4. **Plant files** - Add `.notes` to Cowrie filesystem
5. **Create test incident** - So dossier web isn't empty

---

**Entry Point Summary for Tom**:
- 🌐 **Web**: https://redteam-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
- 🔐 **SSH**: `api.uu7a1hfd.eastus.aroapp.io:30022` (if externally accessible)
- 🎯 **Goal**: Find the flag (which is in the dossier of his own scan!)
