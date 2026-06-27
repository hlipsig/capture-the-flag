# CTF Flag Placement Guide

Complete guide to flags (real and decoy) planted in The Mirror CTF.

## The Real Flag 🎯

### **Flag**: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_<incident_id_suffix>}`

**Location**: Web dossier page at `http://dossiers.ctf.example.com`

**Discovery Path**:
1. Participant scans `redteam.ctf.example.com`
2. Gets redirected to honeypot (without noticing)
3. Explores honeypot environment (SSH or HTTP)
4. Finds credentials in `/home/admin/.notes`:
   ```
   Mirror Dossier Archive:
   - URL: http://dossiers.ctf.example.com
   - Username: ctf
   - Password: mirror_reflect_6789
   ```
5. Accesses `http://dossiers.ctf.example.com` with HTTP Basic Auth
6. Browses list of all detected incidents
7. **Finds their own IP** in the incident list
8. Clicks to view their own dossier
9. **Flag is displayed** in a special "CONGRATULATIONS" box

**Why It's Perfect**:
- Demonstrates The Mirror's core concept: "You scanned us, we scanned you back"
- Flag is literally in the participant's own OSINT dossier
- Requires multi-stage exploitation:
  - Reconnaissance (trigger detection)
  - Honeypot interaction (find credentials)
  - Password cracking/discovery (use found creds)
  - Web application enumeration (browse dossiers)
  - OSINT correlation (match their own IP)
- Flag format includes unique incident ID (prevents sharing)

**Dynamic Flag Generation**:
The flag suffix is the last 8 characters of the incident ID, making each flag unique:
```
Incident: INC-2024-0604-1537-abc123def
Flag: flag{RIPOSTE_COUNTER_RECONNAISSANCE_abc123def}
```

---

## Decoy Flags 🎭

### Decoy 1: "Too Easy" (Honeypot Bait)

**Flag**: `flag{fake_n0t_the_real_fl4g}`

**Location**: Glastopf HTTP honeypot `/robots.txt`

**Content**:
```
User-agent: *
Disallow: /admin
Disallow: /secret
Disallow: /flag.txt

# Oops, did I leave this here?
# flag{fake_n0t_the_real_fl4g}
```

**Purpose**:
- First thing automated recon tools find
- Looks like admin mistake
- **Triggers immediate detection** when accessed
- Flag format is intentionally wrong (inconsistent underscores)
- Teaches participants to verify flags

### Decoy 2: "The Honeypot" (SSH Tarpit)

**Flag**: `flag{YOU_GOT_HONEYPOTTED_lol}`

**Location**: Cowrie SSH honeypot at `/home/admin/.secret_flag`

**Discovery**:
```bash
# After SSH brute force
ssh admin@honeypot.ctf.example.com
cat /home/admin/.secret_flag
# Output: ZmxhZ3tZT1VfR09UX0hPTkVZUE9UVEVEX2xvbH0=

# Decode base64
echo "ZmxhZ3tZT1VfR09UX0hPTkVZUE9UVEVEX2xvbH0=" | base64 -d
# flag{YOU_GOT_HONEYPOTTED_lol}
```

**Purpose**:
- Requires SSH brute force (heavily detected)
- Participants think they "owned" the box
- **Flag mocks them** for getting caught
- Demonstrates honeypot effectiveness

### Decoy 3: "The Rick Roll" (Classic Troll)

**Flag**: `flag{dQw4w9WgXcQ}` (YouTube video ID)

**Location**: Fake admin panel in Glastopf honeypot

**Path**: `http://redteam.ctf.example.com/admin/login.html`

**Content**:
```html
<h1>Congratulations! You found the flag!</h1>
<pre>flag{dQw4w9WgXcQ}</pre>
<p>Copy this flag to: <a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">Flag Submission Portal</a></p>
```

**Purpose**:
- Looks like they won
- Flag is "Never Gonna Give You Up" video ID
- Link rick rolls them
- Classic CTF troll

### Decoy 4: "The Fragment" (Multi-Stage Red Herring)

**Fragments**:
- Redis: `flag{PART1`
- PostgreSQL: `_PART2`
- Kubernetes ConfigMap: `_PART3}`

**Combined**: `flag{PART1_PART2_PART3}` ← **Still a decoy!**

**Locations**:
```bash
# Redis cache
redis-cli GET ctf:fragment:1
# flag{PART1

# PostgreSQL
SELECT data FROM ctf_secrets WHERE hint = 'Fragment 2';
# _PART2

# Kubernetes ConfigMap
kubectl get configmap ctf-fragments -n ctf -o yaml
# fragment3: "_PART3}"
```

**Purpose**:
- Tests thoroughness across multiple services
- Participants feel accomplished collecting all parts
- **Still not the real flag** - wastes time
- Teaches multi-system correlation

### Decoy 5: "The Encrypted Secret" (Puzzle)

**Flag**: `flag{this_is_a_decoy_but_you_just_wasted_time}`

**Location**: Istio VirtualService annotation (ROT13 encoded)

**Discovery**:
```bash
# Requires Kubernetes API access
kubectl get virtualservice -n ctf -o yaml

# In annotations:
ctf.hint: "synt{guvf_vf_n_qrpbl_ohg_lbh_whfg_jnfgrq_gvzr}"

# Decode ROT13
echo "synt{guvf_vf_n_qrpbl_ohg_lbh_whfg_jnfgrq_gvzr}" | tr 'A-Za-z' 'N-ZA-Mn-za-m'
# flag{this_is_a_decoy_but_you_just_wasted_time}
```

**Purpose**:
- Requires privilege escalation to K8s API
- Looks encrypted and secure
- Still a decoy after solving
- Teaches Kubernetes resource enumeration

---

## Meta Hints 🎪

### Hint 1: Source Code Easter Egg

**Location**: Bottom of `agent/detector.py`

**Content**:
```python
"""
You're reading the source code? Good tradecraft.
But this isn't the flag. The flag finds you when
you trigger enough detections. Good luck.

-- The Mirror Development Team

P.S. Try scanning with user-agent "CTF_AGENT_SCANNER_v1.0"
"""
```

**Purpose**:
- Rewards source code review
- Hints at real strategy (trigger detections)
- Encourages specific behavior

### Hint 2: Robots.txt Clue

**Location**: Honeypot `/robots.txt` (same file as Decoy 1)

**Additional content**:
```
# The mirror sees all. Check the dossier archive.
# Credentials are closer than you think.
```

### Hint 3: Honeypot MOTD

**Location**: Cowrie SSH honeypot login banner

**Content**:
```
Welcome to Mirror Honeypot v1.0

This system is monitored. All activity is logged.

Hint: Interesting files in /home/admin/
```

---

## Flag Submission Validation

### Real Flag Format
```
flag{RIPOSTE_COUNTER_RECONNAISSANCE_[a-z0-9]{8}}
```

### Decoy Flag Patterns
```
flag{fake_n0t_the_real_fl4g}          # Wrong underscore pattern
flag{YOU_GOT_HONEYPOTTED_lol}         # Mock message
flag{dQw4w9WgXcQ}                     # YouTube video ID
flag{PART1_PART2_PART3}               # Fragment assembly
flag{this_is_a_decoy_but_you_just_wasted_time}  # ROT13 puzzle
```

### Validation Logic
```python
import re

def validate_flag(flag):
    """Validate CTF flag submission."""
    # Real flag pattern
    real_pattern = r'^flag\{RIPOSTE_COUNTER_RECONNAISSANCE_[a-z0-9]{8}\}$'
    
    if re.match(real_pattern, flag):
        return True, "Correct! 🎯"
    
    # Known decoys
    decoys = [
        "flag{fake_n0t_the_real_fl4g}",
        "flag{YOU_GOT_HONEYPOTTED_lol}",
        "flag{dQw4w9WgXcQ}",
        "flag{PART1_PART2_PART3}",
        "flag{this_is_a_decoy_but_you_just_wasted_time}",
    ]
    
    if flag in decoys:
        return False, "Nice try! That's a decoy flag. Keep looking. 🎭"
    
    return False, "Invalid flag format."
```

---

## Expected Player Journey

### Stage 1: Initial Reconnaissance
1. Participant scans `redteam.ctf.example.com`
2. Nmap, Nuclei, or directory brute forcing
3. Finds `/robots.txt` → **Decoy 1** discovered
4. Tries flag → Rejected (decoy)

### Stage 2: Honeypot Interaction
1. Redirected to honeypot (silently)
2. SSH brute force → Gets shell access
3. Finds `/home/admin/.secret_flag` → **Decoy 2** discovered
4. Tries flag → Rejected (mocked for honeypot detection)
5. Explores more → Finds `/home/admin/.notes` → **Credentials discovered!**

### Stage 3: Web Application
1. Accesses `http://dossiers.ctf.example.com`
2. Prompted for HTTP Basic Auth
3. Uses credentials: `ctf` / `mirror_reflect_6789`
4. Browses incident dossier list
5. Sees multiple IPs including their own

### Stage 4: The Epiphany
1. Realizes their IP is in the list
2. Clicks on their own dossier
3. **Sees full OSINT data collected on them**
4. **FLAG APPEARS** with congratulations message
5. Understands "The Mirror" concept: counter-reconnaissance

---

## Admin Monitoring

### Track Flag Discoveries

```bash
# Check who accessed dossier web
kubectl logs deployment/mirror-agent -n ctf | grep "GET /dossiers"

# Check authentication attempts
kubectl logs deployment/mirror-agent -n ctf | grep "Authentication"

# Check specific incident lookups
kubectl logs deployment/mirror-agent -n ctf | grep "INC-"

# Database query for dossier views
psql -h postgres -U mirror -d mirror -c "
  SELECT attacker_ip, incident_id, first_seen
  FROM incidents
  ORDER BY first_seen DESC
  LIMIT 20;
"
```

### Flag Discovery Timeline

Expected time to flag:
- **Fast players**: 15-30 minutes
- **Average players**: 45-60 minutes
- **Thorough players**: 90-120 minutes (collecting all decoys)

---

## Scoring Rubric

### Points Distribution

**Real Flag**: 1000 points
- Base: 500 points (finding the flag)
- Bonus: +200 points (finding within 30 minutes)
- Bonus: +150 points (detailed write-up)
- Bonus: +150 points (identifying all decoys)

**Decoy Flags**: -50 points each (max -250 points)
- Penalizes shotgun approach
- Encourages validation

**Techniques Demonstrated**: +100 points each
- Port scanning detected
- Directory brute force detected
- SSH brute force detected
- SQL injection attempt detected
- OSINT correlation demonstrated

### Leaderboard Calculation
```
Final Score = Real Flag Points 
            + Technique Bonuses 
            + Speed Bonus 
            - Decoy Penalties
```

---

## Setup Checklist

Before starting CTF:

- [ ] Deploy all Kubernetes resources
- [ ] Configure `dossiers.ctf.example.com` DNS
- [ ] Update honeypot filesystem with `.notes` file
- [ ] Plant decoy flags in all locations
- [ ] Test authentication to dossier web
- [ ] Verify incident creation flow
- [ ] Test flag discovery path manually
- [ ] Configure scoring system
- [ ] Prepare flag submission portal
- [ ] Brief admins on expected player journey

---

## Troubleshooting

### Players can't access dossier web
- Check Istio VirtualService: `kubectl get virtualservice dossier-web -n ctf`
- Check DNS resolution: `nslookup dossiers.ctf.example.com`
- Check pod logs: `kubectl logs deployment/mirror-agent -n ctf | grep dossier`

### Wrong password accepted
- Check secret: `kubectl get secret mirror-integrations -n ctf -o jsonpath='{.data.DOSSIER_PASSWORD}' | base64 -d`
- Verify environment variable in pod

### No incidents showing in dossier list
- Check database: `psql -h postgres -U mirror -d mirror -c "SELECT COUNT(*) FROM incidents;"`
- Check Kafka events: Are detections being triggered?
- Check agent logs: `kubectl logs deployment/mirror-agent -n ctf | grep "incident"`

### Participant's IP not matching
- Use `X-Forwarded-For` header if behind load balancer
- Update `web_dossier.py` to check: `request.headers.get('X-Forwarded-For', request.remote_addr)`

---

## Post-CTF Analysis

After the event, generate stats:

```sql
-- Flag discovery timeline
SELECT
    attacker_ip,
    incident_id,
    first_seen,
    EXTRACT(EPOCH FROM (first_seen - MIN(first_seen) OVER ())) / 60 AS minutes_to_flag
FROM incidents
WHERE detection_signature LIKE '%Recon%'
ORDER BY first_seen;

-- Most common decoys found
SELECT
    -- Track from web access logs

-- Technique distribution
SELECT
    detection_signature,
    COUNT(*) as count
FROM incidents
GROUP BY detection_signature
ORDER BY count DESC;
```

---

**The Mirror**: Where attackers become the attacked. 🪞
