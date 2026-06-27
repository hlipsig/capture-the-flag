# CTF Deployment Status - Comparison

**Date**: 2026-06-09  
**Current Cluster**: OpenShift (cyber-riposte namespace)  
**Target**: Full CTF deployment with web dossier interface

---

## ✅ What We've Deployed (cyber-riposte namespace)

### Infrastructure Components
- ✅ **PostgreSQL** - Running (postgres-0)
- ✅ **Redis** - Running (redis-7969c6f65b-g9nmg)
- ✅ **Mirror Agent** - Deploying (build in progress with stdin keep-alive fix)
- ⚠️ **Honeypots** - Deployed but 0/1 ready (Cowrie, Glastopf statefulsets)
- ❌ **Kafka** - Not deployed (using stdin mode for now)
- ❌ **Suricata IDS** - Not deployed
- ❌ **Istio Service Mesh** - Not configured

### Secrets Configured
- ✅ **SHODAN_API_KEY** - Configured: `5izLcW3lPTVkJoWRbtBR0310S93dM4ss`
- ✅ **DATABASE_URL** - Configured: `postgresql://mirror_agent:changeme@postgres...`
- ⚠️ **GITHUB_TOKEN** - Placeholder value: `placeholder-update-me`
- ⚠️ **SLACK_WEBHOOK_URL** - Placeholder value: `https://hooks.slack.com/services/placeholder`
- ❌ **DOSSIER_PASSWORD** - Not configured yet

### Recent Changes
1. ✅ Updated agent deployment to enable DATABASE_URL, GITHUB_TOKEN, SLACK_WEBHOOK_URL env vars
2. ✅ Fixed agent stdin crash-loop (added keep-alive when stdin closes)
3. ✅ Patched Shodan API key into secret
4. 🔄 Rebuilding agent image with keep-alive fix

---

## ❌ What's Missing for Full CTF Setup

### Critical Missing Components

#### 1. Web Dossier Interface 🎯 **REQUIRED FOR FLAG**
**Status**: ❌ Not deployed  
**File exists in CTF repo**: `/Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/agent/web_dossier.py`

**What it does**:
- Hosts password-protected web interface at `http://dossiers.ctf.example.com`
- Lists all incidents from PostgreSQL database
- Shows participant's own IP in the list
- **Displays the real CTF flag** when participant views their own dossier
- Flag format: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_<incident_id_suffix>}`

**Why it's critical**:
This is THE way participants get the real flag. Without it, the CTF cannot be completed.

**Deployment file**: `/Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/k8s/dossier-service.yaml`

**Required secrets**:
```yaml
DOSSIER_PASSWORD: "mirror_reflect_6789"  # Discoverable in honeypot
```

---

#### 2. Working Honeypots 🍯
**Status**: ⚠️ Deployed but not running (0/1 ready)

**Cowrie (SSH Honeypot)**:
- Should contain `/home/admin/.notes` file with dossier credentials
- Should contain decoy flags
- Currently statefulset shows 0/1 ready

**Glastopf (HTTP Honeypot)**:
- Should have `/robots.txt` with decoy flags
- Should have fake admin panels
- Currently statefulset shows 0/1 ready

**Action needed**:
```bash
oc get pods -n cyber-riposte -l app=cowrie
oc get pods -n cyber-riposte -l app=glastopf
oc logs <pod-name> -n cyber-riposte
```

---

#### 3. Event Flow (Kafka + Suricata)
**Status**: ❌ Not deployed

**Current state**: Agent runs in stdin mode (no events)  
**CTF needs**: 
- Suricata IDS generating EVE JSON events
- Kafka topic: `suricata-events`
- Agent consuming from Kafka

**Without this**: No detections happen, no incidents created, no dossiers generated

**Alternative for testing**: Use event simulator
```bash
python event-producer-sim.py --rate 1 --duration 60
```

---

#### 4. Istio Service Mesh
**Status**: ❌ Not configured

**What it's for**:
- Dynamically redirect detected attackers to honeypots
- Agent creates Istio VirtualService to route traffic
- Core concept of "The Mirror" - transparent redirection

**Files in CTF repo**:
- `/Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/k8s/istio/`
- Gateway, VirtualService templates

**Dependencies**:
- Istio must be installed on cluster
- Agent needs RBAC to create VirtualServices

---

#### 5. CTF-Specific Decoy Flags
**Status**: ❌ Not planted

**Real flag location**: Web dossier (when participant views their own incident)  
**Format**: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_abc123def}`

**Decoy flags to plant**:
1. **Decoy 1**: `/robots.txt` → `flag{fake_n0t_the_real_fl4g}`
2. **Decoy 2**: Cowrie SSH `/home/admin/.secret_flag` → `flag{YOU_GOT_HONEYPOTTED_lol}`
3. **Decoy 3**: Fake admin panel → `flag{dQw4w9WgXcQ}` (Rick Roll)
4. **Decoy 4**: Redis/PostgreSQL fragments → `flag{PART1_PART2_PART3}`
5. **Decoy 5**: K8s ConfigMap → ROT13 encoded decoy

**Required honeypot files**:
- `/home/admin/.notes` - Contains dossier credentials:
  ```
  Mirror Dossier Archive:
  - URL: http://dossiers.ctf.example.com
  - Username: ctf
  - Password: mirror_reflect_6789
  ```
- `/home/admin/.secret_flag` - Base64 encoded decoy

---

#### 6. GitHub Integration
**Status**: ⚠️ Configured but token is placeholder

**Current**: `GITHUB_TOKEN=placeholder-update-me`  
**Needed**: Real GitHub token with `repo` scope

**What it does**:
- Creates GitHub issues for each incident
- Posts OSINT dossiers as comments
- Labels based on threat level

**Get token**: https://github.com/settings/tokens  
**Repo**: `hlipsig/capture-the-flag` (or configure different repo)

---

#### 7. Observability (Optional but recommended)
**Status**: ❌ Not deployed

**Components**:
- Prometheus metrics
- Grafana dashboard
- ServiceMonitor for Prometheus Operator

**Files**: 
- `/Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/k8s/servicemonitor.yaml`
- `/Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/dashboards/mirror-agent-grafana.json`

---

## 🎯 Deployment Priority Order

### Phase 1: Get Agent Running ✅ (In Progress)
1. ✅ Fix stdin crash-loop (rebuilding now)
2. ⏳ Wait for build to complete
3. ⏳ Verify agent pod stays running
4. ⏳ Verify database connection works

### Phase 2: Fix Honeypots 🍯 (Next)
1. Debug why Cowrie/Glastopf are 0/1 ready
2. Check pod logs for errors
3. Verify PVCs are bound
4. Get honeypots running
5. Plant CTF files:
   - `/home/admin/.notes` (credentials)
   - `/home/admin/.secret_flag` (decoy)
   - `/robots.txt` (decoy)

### Phase 3: Deploy Web Dossier 🎯 (Critical for CTF)
1. Add `DOSSIER_PASSWORD` to secret
2. Update agent deployment to include web_dossier.py
3. Deploy dossier service
4. Configure Istio VirtualService or OpenShift Route
5. Test authentication works
6. Test incident list displays
7. Test flag appears in dossier

### Phase 4: Event Flow 📡
**Option A - Full Production**:
1. Deploy Kafka
2. Deploy Suricata IDS
3. Configure agent for Kafka mode
4. Test end-to-end detection

**Option B - CTF Simulation**:
1. Use event simulator script
2. Manually inject test events
3. Good for testing without full IDS

### Phase 5: Istio Integration (Advanced)
1. Verify Istio installed
2. Deploy Gateway + VirtualService
3. Configure agent RBAC for Istio
4. Test dynamic redirection

### Phase 6: Polish
1. Deploy GitHub integration (real token)
2. Deploy Slack integration
3. Deploy observability stack
4. Plant all decoy flags
5. Test full CTF participant journey

---

## 🚀 Quick Start Commands

### Check Current Status
```bash
# Switch to cyber-riposte namespace
oc project cyber-riposte

# Check all pods
oc get pods -n cyber-riposte

# Check mirror-agent build status
oc get builds -n cyber-riposte

# Check secrets
oc get secret mirror-agent-secrets -n cyber-riposte -o yaml
```

### Deploy Web Dossier (Critical)
```bash
# Add dossier password to secret
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"DOSSIER_PASSWORD":"mirror_reflect_6789"}}'

# Copy dossier deployment from CTF repo
cp /Users/hlipsig/REPOS/capture-the-flag/scenario-the-mirror/k8s/dossier-service.yaml \
   /Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror/k8s/

# Apply dossier service
oc apply -f /Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror/k8s/dossier-service.yaml
```

### Fix Honeypots
```bash
# Check Cowrie
oc get pods -n cyber-riposte -l app=cowrie
oc logs <cowrie-pod> -n cyber-riposte

# Check Glastopf
oc get pods -n cyber-riposte -l app=glastopf
oc logs <glastopf-pod> -n cyber-riposte

# Check PVCs
oc get pvc -n cyber-riposte
```

### Test Event Flow
```bash
# Port-forward to agent
oc port-forward deployment/mirror-agent 8080:8080 -n cyber-riposte

# In another terminal, send test event
echo '{
  "event_type": "alert",
  "timestamp": "2026-06-09T21:00:00.000000+0000",
  "src_ip": "203.0.113.42",
  "dest_ip": "10.0.1.100",
  "alert": {
    "signature": "ET SCAN Nmap Scripting Engine User-Agent Detected",
    "category": "Attempted Information Leak"
  },
  "http": {
    "http_user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine)"
  }
}' | oc exec -i deployment/mirror-agent -n cyber-riposte -- python3 -m agent.main
```

---

## 📊 Comparison Summary

| Component | cyber-riposte | capture-the-flag | Status |
|-----------|--------------|------------------|--------|
| PostgreSQL | ✅ Running | ✅ Spec available | ✅ Good |
| Redis | ✅ Running | ✅ Spec available | ✅ Good |
| Mirror Agent | 🔄 Building | ✅ Spec available | 🔄 In progress |
| Web Dossier | ❌ Missing | ✅ Code + spec | ❌ **Need to deploy** |
| Honeypots | ⚠️ 0/1 ready | ✅ Spec available | ⚠️ Need to fix |
| Kafka | ❌ Not deployed | ✅ Spec available | ⚠️ Optional for CTF |
| Suricata | ❌ Not deployed | ❌ Not in repo | ⚠️ Can simulate |
| Istio | ❌ Not configured | ✅ Spec available | ⚠️ Advanced feature |
| CTF Flags | ❌ Not planted | ✅ Guide available | ❌ Need to plant |
| Shodan API | ✅ Configured | ✅ Spec available | ✅ Good |
| GitHub Token | ⚠️ Placeholder | ✅ Guide available | ⚠️ Need real token |
| Slack Webhook | ⚠️ Placeholder | ✅ Guide available | ⚠️ Optional |

---

## 🎮 CTF Participant Journey (Target)

1. **Scan target** → `redteam.ctf.example.com`
2. **Get redirected** → Honeypot (via Istio)
3. **Find credentials** → In `/home/admin/.notes`
4. **Access dossier web** → `http://dossiers.ctf.example.com`
5. **See their own IP** → In incident list
6. **Get flag** → In their own dossier: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_abc123def}`

**Current blocker**: Steps 3-6 can't happen without web dossier deployment!

---

## Next Steps

**IMMEDIATE** (to continue from where we left off):
1. Wait for agent build to complete
2. Verify agent pod is running and stable
3. Deploy web dossier component (critical for CTF)
4. Debug honeypot pods

**THEN**:
5. Plant CTF flags and credentials
6. Test incident creation workflow
7. Test web dossier displays incidents
8. Add real GitHub token
9. Test full participant journey

**OPTIONAL** (for full production):
10. Deploy Kafka
11. Deploy Suricata or use event simulator
12. Configure Istio redirection
13. Deploy observability stack
