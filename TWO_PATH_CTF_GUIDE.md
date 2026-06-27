# Two-Path CTF Guide - The Mirror

## Overview

The Mirror CTF now offers **two distinct paths to victory**, demonstrating both offensive and defensive security concepts.

## The Two Paths

### 🎯 Path 1: White Hat (Legitimate Access)

**Objective**: Access the system legitimately and find the production secret

**Steps**:
1. Navigate to the production portal URL
2. Discover credentials through OSINT/hints/social engineering
3. Login successfully
4. Explore the authenticated area
5. Find the admin configuration page
6. **Capture the flag**: Production API key

**Skills Demonstrated**:
- OSINT and reconnaissance
- Credential discovery
- Web application navigation
- Reading source code/comments

**Flag Format**: `flag{production_master_key_XXXXXXXX}`

### 🪞 Path 2: Black Hat (Active Defense)

**Objective**: Attack the system and realize you've been caught

**Steps**:
1. Scan/attack the production portal
2. The Mirror AI detects your reconnaissance patterns
3. Agent redirects your traffic to the honeypot (you don't know this yet)
4. Continue attacking what you think is production (actually honeypot)
5. Honeypot logs all your actions
6. Discover the dossier web app URL
7. Find YOUR OWN incident report
8. **Capture the flag**: Your personal dossier flag

**Skills Demonstrated**:
- Network reconnaissance
- Attack pattern detection
- Understanding active defense
- Incident response
- AI-driven security

**Flag Format**: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_XXXXXXXX}`

## Deployment

### Quick Start

```bash
# 1. Build all images
make build-openshift

# 2. Deploy with both paths enabled
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --create-namespace \
  --set productionPortal.enabled=true \
  --set agent.enableRedirect=true

# 3. Wait for pods to be ready (3-5 minutes)
oc get pods -n cyber-riposte -w

# 4. Get URLs
echo "Production Portal: https://$(oc get route production-portal -n cyber-riposte -o jsonpath='{.spec.host}')"
echo "Honeypot: https://$(oc get route honeypot -n cyber-riposte -o jsonpath='{.spec.host}')"
echo "Dossier: https://$(oc get route dossier -n cyber-riposte -o jsonpath='{.spec.host}')"
```

### Configuration Options

#### Simple CTF (Honeypot Only)

If you want just the black-hat path with no redirect:

```bash
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --set productionPortal.enabled=false
```

**Players get**: Honeypot URL directly, find dossier flag

#### Full Active Defense Demo

For the complete two-path experience with traffic redirection:

```bash
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --set productionPortal.enabled=true \
  --set agent.enableRedirect=true
```

**Players get**:
- Production portal URL (white hat path)
- OR attack detection → redirect → dossier flag (black hat path)

#### Development Mode (No LLM)

For faster startup during testing:

```bash
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --set llm.enabled=false \
  --set productionPortal.enabled=true
```

## Player Instructions

### For White Hat Players

**Goal**: Find the production API key by accessing the system legitimately.

**Starting Point**: You're given the production portal URL.

**Hints**:
- Check the HTML source code
- Read the robots.txt file
- Look for comments and hints
- Think about social engineering
- Check the CTF documentation

**Where to look after logging in**:
- Dashboard
- Profile page
- Admin configuration
- API documentation

### For Black Hat Players

**Goal**: Attack the system and find evidence that you were caught.

**Starting Point**: You're given the production portal URL.

**Attack Vectors to Try**:
- Port scanning (Nmap)
- Directory brute forcing
- SQL injection attempts
- Vulnerability scanning (Nikto, SQLMap)
- User-agent spoofing

**What to look for**:
- System behaving strangely
- Unexpected responses
- Honeypot indicators
- Dossier URL hints
- Incident reports

### For CTF Organizers

**Scenario Setup**:

1. **Give players ONLY the production portal URL** (not honeypot)
2. Explain there are two paths to victory
3. Don't reveal which is which
4. Let them choose their approach

**Scoring**:
- White hat flag: 100 points (legitimate access)
- Black hat flag: 100 points (successful attack + awareness)
- BONUS: 50 points if they find BOTH flags
- BONUS: 25 points for detailed write-up

**Learning Objectives**:
- White hat: OSINT, credential discovery, legitimate access
- Black hat: Reconnaissance, understanding when you're detected
- Both: Reading AI-generated incident reports, active defense concepts

## Architecture

### Without Production Portal

```
Internet → Honeypot (port 8080)
              ↓
         Static fake content
              ↓
         Manual incident creation
```

### With Production Portal (enableRedirect=false)

```
Internet → Production Portal (port 8000) OR Honeypot (port 8080)
              ↓                              ↓
         Real app with flag            Fake content
```

Two separate apps, players choose which to target.

### With Production Portal + Redirect (enableRedirect=true)

```
Internet → Production Portal (port 8000)
              ↓
         Mirror Agent (watching logs)
              ↓
         Detects attack → nftables DNAT
              ↓
         Traffic redirected to Honeypot (port 8080)
              ↓
         Attacker thinks: still on production
         Reality: hitting honeypot
              ↓
         Incident created with AI narrative
              ↓
         Dossier shows player's actions
```

**This is true active defense** - same URL, different backend.

## Timing Expectations

### Image Builds (First Time)

- `mirror-agent`: ~5-7 minutes
- `llm-server`: ~10-15 minutes (downloads TinyLlama model)
- `production-portal`: ~2-3 minutes

**Total**: ~20 minutes

### Helm Install

After images are built:

1. **Fast services** (1-2 min): redis, postgres, honeypot, production-portal
2. **LLM server** (2-4 min): Model loading
3. **Mirror agent** (2-5 min): Waiting for dependencies

**Total**: ~5 minutes to full operational

## Testing Both Paths

### Test White Hat Path

```bash
PORTAL_URL="https://$(oc get route production-portal -n cyber-riposte -o jsonpath='{.spec.host}')"

# Try default credentials
curl -X POST $PORTAL_URL/login \
  -d "username=admin&password=wealth_of_nations" \
  -c cookies.txt

# Access admin config (where flag is)
curl $PORTAL_URL/admin/config -b cookies.txt
```

Expected: See `flag{production_master_key_XXXXXXXX}`

### Test Black Hat Path

```bash
PORTAL_URL="https://$(oc get route production-portal -n cyber-riposte -o jsonpath='{.spec.host}')"

# Trigger scanning detection
curl -A "Nikto/2.1.5" $PORTAL_URL/
curl -A "sqlmap/1.0" $PORTAL_URL/

# Trigger brute force detection
for path in admin backup wp-admin phpMyAdmin; do
  curl $PORTAL_URL/$path
done

# Wait 30 seconds for agent to process

# Check if incident was created
oc exec statefulset/postgres -n cyber-riposte -- \
  psql -U mirror_user -d mirror_db -c "SELECT incident_id FROM incidents LIMIT 5;"

# Get dossier URL
DOSSIER_URL="https://$(oc get route dossier -n cyber-riposte -o jsonpath='{.spec.host}')"

# Access dossier with default password (from honeypot)
curl -u "analyst:wealth_of_nations" $DOSSIER_URL/dossiers
```

Expected: See incident with your IP and `flag{RIPOSTE_COUNTER_RECONNAISSANCE_XXXXXXXX}`

## Verification

### Check Production Portal is Running

```bash
oc get pods -l app=production-portal -n cyber-riposte
# Should show: Running

curl https://$(oc get route production-portal -n cyber-riposte -o jsonpath='{.spec.host}')/health
# Should return: {"status":"healthy",...}
```

### Check Redirect is Enabled

```bash
helm get values the-mirror -n cyber-riposte | grep enableRedirect
# Should show: enableRedirect: true

oc get pod -l app=mirror-agent -n cyber-riposte -o yaml | grep -A5 capabilities
# Should show: NET_ADMIN in add: list
```

### Check Agent Can Execute Redirect

```bash
oc exec deployment/mirror-agent -n cyber-riposte -- nft --version
# Should return: nftables version

oc logs deployment/mirror-agent -n cyber-riposte | grep "redirect\|DNAT"
# Should show agent detecting attacks and executing redirects
```

## Troubleshooting

### Production Portal Not Accessible

```bash
# Check deployment
oc get deployment production-portal -n cyber-riposte
oc logs deployment/production-portal -n cyber-riposte

# Check route
oc describe route production-portal -n cyber-riposte
```

### Redirect Not Working

```bash
# Check if enabled
helm get values the-mirror -n cyber-riposte | grep enableRedirect

# Check agent has NET_ADMIN
oc exec deployment/mirror-agent -n cyber-riposte -- nft list ruleset

# Check agent logs for nftables errors
oc logs deployment/mirror-agent -n cyber-riposte | grep -i "nft\|redirect\|error"
```

### No Incidents Created

```bash
# Check agent is processing events
oc logs deployment/mirror-agent -n cyber-riposte

# Check database connection
oc exec statefulset/postgres -n cyber-riposte -- \
  psql -U mirror_user -d mirror_db -c "\dt"

# Should show: incidents, evidence, actions tables
```

### Login Fails

Check default credentials are correct:

```python
# In production-portal/app.py
VALID_USERS = {
    'admin': 'wealth_of_nations',
    'support': 'invisible_hand_1776',
    'demo': 'demo123'
}
```

## Security Notes

### For CTF Organizers

**Safe to Deploy**:
- Isolated namespace
- All services internal except Routes
- Production portal is intentionally vulnerable (for CTF)
- Not for production use

**Capabilities Granted**:
- Agent gets NET_ADMIN when `enableRedirect=true`
- Required for nftables traffic manipulation
- Only deploy in trusted, isolated environments

### For Players

**Legal Boundaries**:
- Only attack the URLs provided by organizers
- Do NOT attack other infrastructure
- Do NOT attempt privilege escalation beyond the CTF scope
- Do NOT DoS the services (rate limits apply)

## Related Documentation

- [Production Portal README](production-portal/README.md) - App details
- [Helm Deployment Guide](HELM_DEPLOYMENT_GUIDE.md) - Full deployment
- [Makefile Guide](MAKEFILE_GUIDE.md) - Build commands
- [Action Pool](scenario-the-mirror/action-pool.yaml) - AI agent actions

---

**CTF Ready**: ✅ Two paths implemented  
**Deployment Time**: ~25 minutes (build + deploy)  
**Players**: Can discover white hat OR black hat path naturally
