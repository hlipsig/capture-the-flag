# The Mirror - CTF Playbook

**A live-fire cybersecurity CTF where YOU are the attacker being watched.**

## Scenario Overview

You discover a production web server. As you enumerate and exploit it, an AI-powered threat intelligence system is analyzing your every move. Your goal: find your own security dossier and retrieve the flag.

**Difficulty**: Intermediate  
**Time**: 30-60 minutes  
**Skills**: Web recon, password cracking, OSINT, pattern recognition

---

## What Makes This CTF Unique

Unlike traditional CTFs where you attack targets in isolation, **The Mirror** creates a dossier on YOU as you play:

- Every scan you run is logged
- Every endpoint you probe is recorded  
- Every password you try is captured
- An AI system generates a threat intelligence report about YOUR attack patterns

Your final objective is to find and read your own incident report.

---

## Setup for Players

### Prerequisites

- OpenShift/Kubernetes cluster with public route support
- `oc` or `kubectl` CLI installed
- Basic knowledge of web reconnaissance tools (curl, browser dev tools, nmap)

### Quick Deploy

```bash
# Clone the repo
git clone https://github.com/hlipsig/capture-the-flag.git
cd capture-the-flag/scenario-the-mirror

# Create namespace
oc new-project cyber-riposte

# Deploy infrastructure (database, redis, agent)
oc apply -f k8s/postgres-deployment.yaml
oc apply -f k8s/redis-deployment.yaml
oc apply -f k8s/agent-pvc.yaml

# Create secrets
oc create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=mirror_agent \
  --from-literal=POSTGRES_PASSWORD=changeme \
  --from-literal=POSTGRES_DB=mirror_audit

oc create secret generic shodan-api-key \
  --from-literal=SHODAN_API_KEY=your_key_here

# Deploy the agent (threat intelligence system)
oc apply -f k8s/agent-rbac.yaml
oc create configmap mirror-config --from-file=action-pool.yaml
oc start-build mirror-agent --from-dir=. --follow
oc apply -f k8s/agent-deployment.yaml

# Deploy honeypot (your target)
oc apply -f k8s/simple-honeypot.yaml
oc apply -f k8s/honeypot-routes.yaml

# Deploy web dossier (where you'll find your report)
oc apply -f k8s/dossier-service.yaml

# Get URLs
echo "Honeypot URL: https://$(oc get route redteam -o jsonpath='{.spec.host}')"
echo "Dossier URL: https://$(oc get route dossier-web -o jsonpath='{.spec.host}')"
```

### Seed the Database

```bash
# Initialize database schema
oc exec -it postgres-0 -- psql -U mirror_agent -d mirror_audit -f /docker-entrypoint-initdb.d/schema.sql

# Add decoy incidents to make the challenge harder
oc exec -it postgres-0 -- psql -U mirror_agent -d mirror_audit << 'SQL'
-- Seed 7 decoy incidents
INSERT INTO incidents VALUES 
  ('INC-2026-06-09-143022', '45.127.83.229', NOW() - interval '2 days', NOW() - interval '2 days', 
   'active', 'ET SCAN WPScan WordPress Security Scanner', 0.92, 0, 
   'WordPress vulnerability scanner detected. Automated reconnaissance of CMS infrastructure.'),
  ('INC-2026-06-10-092145', '185.234.67.142', NOW() - interval '1 day', NOW() - interval '1 day',
   'active', 'ET WEB_SERVER SQL Injection Attempt', 0.88, 0,
   'SQL injection attempt targeting database layer. Manual exploitation effort detected.'),
  -- Add 5 more...
SQL
```

---

## Player Instructions

You'll receive only this information:

```
TARGET: https://redteam-cyber-riposte.apps.YOUR-CLUSTER.com
OBJECTIVE: Find the flag
HINT: The system is watching you.
```

---

## Attack Path (Spoiler - For Game Masters Only)

<details>
<summary>Click to reveal solution</summary>

### Phase 1: Reconnaissance

1. Visit the target URL in browser
2. View page source - find hint about SSH on port 30022 (red herring)
3. Check `/robots.txt` - discover:
   - Hint about "dossier archive"
   - Fake flag: `flag{fake_n0t_the_real_fl4g}`

### Phase 2: Credential Discovery

4. Try common paths from robots.txt: `/admin`, `/secret`, `/.git`
5. Find `/.credentials` (200 OK!)
6. Download and read the file:
   ```
   # Dossier Archive - CRITICAL SYSTEM
   # URL: https://dossiers-cyber-riposte.apps...
   # Username: ctf
   # Password Options (try all until one works):
   #   - Hi_TOM!
   #   - invisible_hand_1776
   #   - creative_destruction
   #   - wealth_of_nations
   #   - i_would_prefer_not_to
   #
   # Note: The scrivener's choice is correct.
   # Hint: Bartleby would understand.
   ```

### Phase 3: Literary Reference

7. Research "Bartleby" + "scrivener" → Herman Melville short story
8. Famous quote: "I would prefer not to"
9. Password is: `i_would_prefer_not_to`

### Phase 4: Access Dossier System

10. Navigate to dossier URL from credentials file
11. Login: `ctf` / `i_would_prefer_not_to`
12. See list of ~10 incidents (most are decoys)

### Phase 5: Find Your Own Report

13. Browse incident reports
14. Look for YOUR IP address (you'll see it in the report)
15. Your incident will have detailed timeline of YOUR attack:
    - Every page you visited
    - Every password you tried
    - Exact timestamps
    - AI-generated threat assessment

### Phase 6: Capture the Flag

16. Your incident report contains the real flag
17. **Flag format**: `flag{you_are_the_mirror_YYYYMMDD_XXXX}`

</details>

---

## Creating Incidents (For Game Masters)

When players attack, create incidents manually:

```bash
# Get player's IP from honeypot logs
PLAYER_IP=$(oc logs -l app=simple-honeypot --tail=20 | grep -v kube-probe | tail -1 | awk '{print $NF}' | tr -d '"')

# Create incident with unique ID
INCIDENT_ID="INC-$(date +%Y%m%d)-$(openssl rand -hex 4)"

# Insert into database
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit -c "
INSERT INTO incidents (
  incident_id, attacker_ip, first_seen, last_updated, status,
  detection_signature, detection_confidence, actions_count, ai_narrative
) VALUES (
  '$INCIDENT_ID', '$PLAYER_IP', NOW(), NOW(), 'active',
  'Web Application Reconnaissance Detected', 0.98, 0,
  'Advanced reconnaissance activity detected from $PLAYER_IP. Multiple endpoints probed. 
   
   ATTACK TIMELINE:
   - Browser-based enumeration
   - Credential file discovery
   - Password brute force attempts
   - Successful authentication
   
   FLAG: flag{you_are_the_mirror_$(date +%Y%m%d)_$(openssl rand -hex 2)}'
);"

# Give player the incident ID
echo "Your incident: https://dossiers-CLUSTER/dossiers/$INCIDENT_ID"
```

---

## Monitoring Players

### Watch Live Activity

```bash
# See all honeypot requests
oc logs -f -l app=simple-honeypot | grep -v kube-probe

# See authentication attempts
oc logs -f -l app=mirror-agent | grep -E "(password|authentication)"

# Count unique attacking IPs
oc logs -l app=simple-honeypot | grep -v kube-probe | awk '{print $NF}' | sort -u
```

### Database Queries

```bash
# List all incidents
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit -c \
  "SELECT incident_id, attacker_ip, detection_signature FROM incidents ORDER BY first_seen DESC;"

# See password attempts
oc logs -l app=mirror-agent | grep "Failed password"
```

---

## Difficulty Variants

### Easy Mode
- Give players the dossier URL upfront
- Provide 2-3 password hints instead of 5
- Include fewer decoy incidents (3-4 total)

### Hard Mode
- Don't mention robots.txt
- Hide the `.credentials` file at obscure path like `/assets/.config/auth.txt`
- Add 15+ decoy incidents to make finding theirs harder
- Require Nmap scan to find SSH port hint
- Multi-stage flags (partial flag in one incident, rest in another)

### Expert Mode
- Players must run Nmap to trigger detection
- No hints about dossier system (they must find it from OSINT)
- Password requires combining clues from multiple files
- Add time-based lockouts on failed passwords
- Real SSH honeypot that logs all commands

---

## Educational Value

Players learn:

1. **Reconnaissance Techniques**: robots.txt, directory enumeration, source code analysis
2. **OSINT Skills**: Literary references, contextual password cracking
3. **Attack Attribution**: How defenders track and profile attackers
4. **Threat Intelligence**: What incident reports look like from defender perspective
5. **Operational Security**: Every action leaves traces
6. **Critical Thinking**: Pattern recognition, avoiding red herrings

---

## Architecture

```
┌─────────────┐
│   Player    │
│  (Attacker) │
└──────┬──────┘
       │
       │ HTTP Requests
       ▼
┌─────────────────┐      Logs      ┌──────────────────┐
│ Simple Honeypot │ ────────────► │  Mirror Agent    │
│   (nginx)       │                │ (Threat Intel)   │
└─────────────────┘                └────────┬─────────┘
                                            │
                                            │ Stores
                                            ▼
                                   ┌─────────────────┐
                                   │   PostgreSQL    │
                                   │   (Incidents)   │
                                   └────────┬────────┘
                                            │
                                            │ Reads
                                            ▼
                                   ┌─────────────────┐
                                   │  Web Dossier    │
                                   │ (Flask Portal)  │
                                   └─────────────────┘
                                            │
                                            │ HTTPS
                                            ▼
                                      ┌──────────┐
                                      │  Player  │
                                      └──────────┘
```

---

## Troubleshooting

### Honeypot not accessible
```bash
oc get route redteam
oc get pods -l app=simple-honeypot
oc logs -l app=simple-honeypot
```

### Dossier web app down
```bash
oc get pods -l app=mirror-agent
oc logs -l app=mirror-agent | tail -50
# If crash loop, check for AI model loading issues
```

### Database connection issues
```bash
oc get pods postgres-0
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit -c "\dt"
```

### No incidents appearing
- Incidents must be created manually via SQL
- Check honeypot logs show player activity
- Verify database credentials are correct

---

## Credits

**Scenario Design**: The Mirror CTF  
**Concept**: AI-powered threat intelligence meets capture-the-flag  
**Technical Stack**: OpenShift, Python, Flask, PostgreSQL, nginx  
**Literary Reference**: "Bartleby, the Scrivener" by Herman Melville

---

## License

MIT License - Free to use for educational purposes

---

## Support

Issues: https://github.com/hlipsig/capture-the-flag/issues  
Discussions: https://github.com/hlipsig/capture-the-flag/discussions
