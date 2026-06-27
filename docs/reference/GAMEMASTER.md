# Game Master Guide - The Mirror CTF

Quick reference for running live CTF sessions.

## Pre-Game Checklist

- [ ] Deploy infrastructure: `./setup.sh`
- [ ] Verify honeypot accessible
- [ ] Verify dossier accessible  
- [ ] Test database connection
- [ ] Prepare incident template

## Give Players

```
TARGET: https://redteam-YOUR-CLUSTER.apps.com
OBJECTIVE: Find the flag
HINT: The system is watching you.
TIME LIMIT: 60 minutes
```

## Monitor Players Live

### Watch Honeypot Logs
```bash
oc logs -f -l app=simple-honeypot | grep -v kube-probe
```

### Watch Password Attempts
```bash
oc logs -f -l app=mirror-agent | grep -E "(password|authentication)"
```

## Create Incident for Player

```bash
# Get player IP
PLAYER_IP=$(oc logs -l app=simple-honeypot --tail=50 | grep -v kube-probe | tail -1 | awk '{print $NF}' | tr -d '"')

# Generate incident ID  
INCIDENT_ID="INC-$(date +%Y%m%d)-$(openssl rand -hex 4)"

# Create with flag
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit -c "
INSERT INTO incidents (incident_id, attacker_ip, first_seen, last_updated, status, detection_signature, detection_confidence, actions_count, ai_narrative)
VALUES (
  '$INCIDENT_ID',
  '$PLAYER_IP', 
  NOW(),
  NOW(),
  'active',
  'Multi-Stage Web Application Attack',
  0.98,
  0,
  'THREAT INTELLIGENCE REPORT - Comprehensive attack campaign detected.

ATTACK TIMELINE - All activity from $PLAYER_IP:
• Web reconnaissance and endpoint enumeration
• Discovered sensitive files (robots.txt, .credentials)
• Password brute force attack  
• Successful authentication compromise
• Accessed classified dossier system

TECHNIQUES: Web recon, OSINT, password cracking, literary references (Bartleby riddle)

SKILL LEVEL: Advanced - Solved multi-stage challenge

FLAG: flag{you_are_the_mirror_$(date +%Y%m%d)_$(openssl rand -hex 2)}

Well played. The mirror reveals your reflection.'
);"

echo "Incident created: $INCIDENT_ID"
echo "Dossier: https://dossiers-CLUSTER/dossiers/$INCIDENT_ID"
```

## Quick Commands

### Player Activity
```bash
oc logs -l app=simple-honeypot --tail=200 | grep PLAYER_IP
```

### Password Attempts
```bash
oc logs -l app=mirror-agent | grep "Failed password"
```

### All Incidents
```bash
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit -c \
  "SELECT incident_id, attacker_ip FROM incidents ORDER BY first_seen DESC LIMIT 10;"
```

## Troubleshooting

### Honeypot 404
```bash
oc get route redteam
oc get pods -l app=simple-honeypot
```

### Dossier Login Fails
Password is: `i_would_prefer_not_to` (underscores!)

### No Logs
```bash
oc logs -l app=simple-honeypot --tail=10
```

## Time Estimates

- **Fast**: 20-30 min
- **Average**: 35-50 min
- **Hint after**: 40 min if stuck

## Success Checklist

- [ ] Found robots.txt
- [ ] Found .credentials  
- [ ] Solved Bartleby riddle
- [ ] Logged into dossier
- [ ] Found own incident
- [ ] Got flag
