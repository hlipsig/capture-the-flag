# Implementation Plan: Active AI Defender for The Mirror

**Objective**: Add autonomous AI defender with GitOps integration to The Mirror scenario  
**Timeline**: Post-Tom CTF session  
**Status**: Planning phase

---

## Overview

Enhance The Mirror from passive detection to **active autonomous defense** using the GitOps + Real-Time Defense pattern. When Tom (or any attacker) scans the system, the AI will:

1. **Detect** the reconnaissance in real-time (already working)
2. **Decide** whether to take defensive action (new AI reasoning)
3. **Defend** by suspending Flux and applying countermeasures (new)
4. **Document** by committing changes to Git with reasoning (new)
5. **Defer** final approval to human via GitHub issue (new)

---

## Current State (What We Have)

### ✅ Working Components:
1. **Log-based detection** (`agent/log_detector.py`)
   - Detects Nmap, Nikto, gobuster, etc.
   - Pattern matching with confidence scores
   - Creates incidents in database

2. **AI narrator** (`agent/ai_narrator.py`)
   - Generates threat intelligence narratives
   - Hugging Face distilgpt2 model
   - Caches results

3. **Web dossier** (`agent/web_dossier.py`)
   - Displays incidents to users
   - Authentication with rate limiting
   - AI narratives visible

4. **Database schema**
   - Incidents, audit_log, evidence tables
   - AI narrative storage

### ⚠️ What's Missing:
- No autonomous defense actions
- No Flux integration
- No GitOps workflow
- No GitHub issue creation
- No LLM reasoning for decisions

---

## Target State (What We'll Build)

### The Complete Mirror Experience:

```
Tom's Scan → Detection → AI Reasoning → Autonomous Defense → Git Commit → Human Review

Example Flow:
1. Tom: nmap -p- mirror.apps...
2. Mirror detects: "Nmap port scan, 98% confidence"
3. AI reasons: "High-confidence reconnaissance, apply honeypot redirect"
4. AI suspends Flux
5. AI applies Istio VirtualService → redirect Tom to honeypot
6. AI commits to Git with reasoning
7. AI creates GitHub issue: "Review: Redirected 203.0.113.42 to honeypot"
8. Human reviews and approves
9. AI resumes Flux → GitOps reconciles
10. Tom is now trapped in honeypot, original service protected
```

---

## Implementation Phases

### Phase 1: Flux Integration (Foundation)

**Goal**: Add ability to suspend/resume Flux and commit to Git

**Files to Create**:
```
agent/flux_controller.py
agent/git_committer.py
agent/github_reviewer.py
```

**Components**:

1. **`FluxController`** class:
   ```python
   class FluxController:
       def suspend(kustomization: str, reason: str) -> bool
       def resume(kustomization: str) -> bool
       def is_suspended(kustomization: str) -> bool
       def get_suspension_duration(kustomization: str) -> timedelta
   ```

2. **`GitCommitter`** class:
   ```python
   class GitCommitter:
       def commit_defense(files: List[str], incident: Dict, reasoning: str) -> str
       def revert_defense(commit_sha: str) -> bool
       def get_commit_details(sha: str) -> Dict
   ```

3. **`GitHubReviewer`** class:
   ```python
   class GitHubReviewer:
       def create_review_issue(incident: Dict, commit_sha: str, action: str) -> str
       def add_comment(issue_url: str, comment: str)
       def close_issue(issue_url: str, resolution: str)
   ```

**Environment Variables Needed**:
```bash
FLUX_KUSTOMIZATION=mirror-app
GIT_REPO_PATH=/workspace/cyber-riposte
GITHUB_REPO=hlipsig/cyber-riposte
GITHUB_TOKEN=<already-configured>
```

**Testing**:
- Manual test: Suspend Flux, verify no reconciliation
- Manual test: Commit a file, verify Git push works
- Manual test: Create GitHub issue via API

---

### Phase 2: LLM Reasoning Engine (Decision Making)

**Goal**: Add AI decision-making with Claude/Anthropic API

**File to Create**:
```
agent/ai_defender.py
```

**Component**:

```python
class AIDefender:
    """
    LLM-powered decision engine for autonomous defense.
    
    Uses Claude API to reason about threats and decide on countermeasures.
    """
    
    def __init__(self, anthropic_api_key: str, model: str = "claude-sonnet-4.5"):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.model = model
    
    def decide_countermeasure(
        self,
        incident: Dict,
        available_actions: List[str]
    ) -> Dict:
        """
        Reason about incident and decide on countermeasure.
        
        Args:
            incident: Detection details (IP, signature, confidence, etc.)
            available_actions: List of possible defenses
        
        Returns:
            {
                "action": "redirect_to_honeypot",
                "confidence": 0.95,
                "reasoning": "High-confidence Nmap scan suggests...",
                "apply_immediately": True,
                "requires_human_review": True
            }
        """
        
    def generate_commit_message(
        self,
        incident: Dict,
        action_taken: str,
        reasoning: str
    ) -> str:
        """Generate detailed Git commit message."""
        
    def generate_review_issue_body(
        self,
        incident: Dict,
        action_taken: str,
        reasoning: str,
        commit_sha: str
    ) -> str:
        """Generate GitHub issue body for human review."""
```

**Reasoning Prompt Template**:
```
You are an autonomous cybersecurity defense AI. You have detected:

Incident: {incident_id}
Threat Type: {detection_signature}
Source IP: {attacker_ip}
Confidence: {detection_confidence}
Evidence: {evidence_summary}

Available Countermeasures:
1. block_ip: Apply NetworkPolicy to block source IP
2. redirect_to_honeypot: Use Istio to redirect to honeypot
3. rate_limit: Apply rate limiting rules
4. alert_only: Create alert without automated action

Your task:
1. Reason about the threat level and intent
2. Choose the most appropriate countermeasure
3. Explain your reasoning
4. Rate your confidence (0-1)

Respond in JSON format:
{
  "action": "redirect_to_honeypot",
  "confidence": 0.95,
  "reasoning": "Detailed explanation...",
  "apply_immediately": true,
  "requires_human_review": true
}
```

**Environment Variables Needed**:
```bash
ANTHROPIC_API_KEY=<key>
AI_DEFENDER_MODEL=claude-sonnet-4.5
AI_DEFENDER_ENABLED=true
AI_CONFIDENCE_THRESHOLD=0.90
```

**Testing**:
- Test with sample incident: Nmap scan
- Test with sample incident: SQL injection
- Verify reasoning quality and JSON format
- Test with low confidence (should defer to human)

---

### Phase 3: Defense Actions (Countermeasures)

**Goal**: Implement actual defense mechanisms

**File to Create/Update**:
```
agent/defense_actions.py
```

**Actions to Implement**:

1. **Redirect to Honeypot** (Perfect for The Mirror!)
   ```python
   def redirect_to_honeypot(
       attacker_ip: str,
       incident_id: str
   ) -> Tuple[bool, Path]:
       """
       Create Istio VirtualService to redirect attacker to honeypot.
       
       Returns:
           (success, yaml_file_path)
       """
       virtual_service = {
           "apiVersion": "networking.istio.io/v1beta1",
           "kind": "VirtualService",
           "metadata": {
               "name": f"redirect-{incident_id}",
               "labels": {
                   "incident": incident_id,
                   "action": "honeypot-redirect"
               }
           },
           "spec": {
               "hosts": ["mirror-agent.cyber-riposte.svc.cluster.local"],
               "http": [
                   {
                       "match": [{
                           "sourceLabels": {"ip": attacker_ip}
                       }],
                       "route": [{
                           "destination": {
                               "host": "honeypot.cyber-riposte.svc.cluster.local"
                           }
                       }]
                   }
               ]
           }
       }
       
       # Apply immediately
       kubectl.apply(virtual_service)
       
       # Save to file for Git commit
       yaml_file = save_to_file(virtual_service)
       
       return True, yaml_file
   ```

2. **Block IP** (Simple but effective)
   ```python
   def block_ip(attacker_ip: str, incident_id: str) -> Tuple[bool, Path]:
       """Apply NetworkPolicy to block IP."""
   ```

3. **Rate Limit** (For credential stuffing, brute force)
   ```python
   def apply_rate_limit(attacker_ip: str, rate: str) -> Tuple[bool, Path]:
       """Apply EnvoyFilter for rate limiting."""
   ```

4. **Alert Only** (Low confidence or unknown threats)
   ```python
   def alert_only(incident: Dict) -> str:
       """Create GitHub issue without automated action."""
   ```

**Files Created**:
- Kubernetes manifests in `k8s/emergency-defenses/`
- Each action creates YAML file for Git commit

**Testing**:
- Test redirect: Send traffic, verify it goes to honeypot
- Test block: Send traffic, verify it's blocked
- Test rate limit: Send burst, verify throttling

---

### Phase 4: Integration (Tie It All Together)

**Goal**: Connect detection → reasoning → action → Git → review

**File to Update**:
```
agent/log_detector.py (enhance existing)
agent/main.py (add defender initialization)
```

**Enhanced Detection Flow**:

```python
# In log_detector.py

from agent.ai_defender import AIDefender
from agent.flux_controller import FluxController
from agent.git_committer import GitCommitter
from agent.github_reviewer import GitHubReviewer
from agent.defense_actions import DefenseActions

def analyze_log_line(self, line: str) -> Optional[Dict]:
    # Existing detection logic...
    detection = self.detect_scan_pattern(parsed)
    if not detection:
        return None
    
    incident = self._create_incident(detection)
    
    # NEW: AI reasoning
    if self.ai_defender_enabled:
        decision = self.ai_defender.decide_countermeasure(
            incident,
            available_actions=[
                "redirect_to_honeypot",
                "block_ip",
                "rate_limit",
                "alert_only"
            ]
        )
        
        # Execute if high confidence
        if decision["apply_immediately"] and decision["confidence"] >= 0.90:
            self._execute_autonomous_defense(incident, decision)
    
    return detection

def _execute_autonomous_defense(self, incident: Dict, decision: Dict):
    """Execute autonomous defense with GitOps workflow."""
    
    logger.info(f"🛡️ Autonomous defense initiated: {decision['action']}")
    
    try:
        # 1. Suspend Flux
        self.flux_controller.suspend(
            self.kustomization,
            f"{incident['incident_id']}: {decision['action']}"
        )
        
        # 2. Apply defense immediately
        success, defense_file = self.defense_actions.execute(
            decision["action"],
            incident
        )
        
        if not success:
            logger.error("Defense failed, resuming Flux")
            self.flux_controller.resume(self.kustomization)
            return
        
        logger.info(f"✅ Defense applied: {decision['action']}")
        
        # 3. Commit to Git
        commit_message = self.ai_defender.generate_commit_message(
            incident,
            decision["action"],
            decision["reasoning"]
        )
        
        commit_sha = self.git_committer.commit_defense(
            files=[defense_file],
            incident=incident,
            message=commit_message
        )
        
        logger.info(f"✅ Committed to Git: {commit_sha[:8]}")
        
        # 4. Create GitHub review issue
        issue_body = self.ai_defender.generate_review_issue_body(
            incident,
            decision["action"],
            decision["reasoning"],
            commit_sha
        )
        
        issue_url = self.github_reviewer.create_review_issue(
            title=f"🛡️ AI Defense: {decision['action']} - {incident['attacker_ip']}",
            body=issue_body,
            labels=["ai-defense", "requires-review", f"confidence-{int(decision['confidence']*100)}"]
        )
        
        logger.info(f"✅ Review issue created: {issue_url}")
        
        # 5. Store in database
        self.db.update_incident(
            incident['incident_id'],
            {
                "autonomous_defense_applied": True,
                "defense_action": decision["action"],
                "defense_reasoning": decision["reasoning"],
                "defense_confidence": decision["confidence"],
                "github_review_url": issue_url,
                "flux_suspended": True,
                "commit_sha": commit_sha
            }
        )
        
        logger.info(f"🎯 Autonomous defense complete. Awaiting review at: {issue_url}")
        
    except Exception as e:
        logger.exception(f"Autonomous defense failed: {e}")
        logger.warning("Resuming Flux...")
        self.flux_controller.resume(self.kustomization)
```

**Testing**:
- End-to-end test: Trigger Nmap scan
- Verify: Detection → AI reasoning → Redirect applied → Git commit → Issue created
- Verify: Flux suspended during defense
- Verify: Can approve via GitHub issue
- Verify: Flux resumes after approval

---

### Phase 5: Database Schema Updates

**Goal**: Track autonomous defense actions

**File to Update**:
```
db/schema.sql
```

**New Columns for `incidents` table**:
```sql
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS autonomous_defense_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS defense_action VARCHAR(128);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS defense_reasoning TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS defense_confidence DECIMAL(3,2);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS github_review_url TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS flux_suspended BOOLEAN DEFAULT FALSE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS flux_resumed_at TIMESTAMPTZ;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS human_review_status VARCHAR(32); -- pending/approved/rejected
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(128);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS commit_sha VARCHAR(64);
```

**New Table: `defense_actions`**:
```sql
CREATE TABLE IF NOT EXISTS defense_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id VARCHAR(64) REFERENCES incidents(incident_id),
    action_type VARCHAR(128) NOT NULL,
    action_config JSONB,
    ai_reasoning TEXT,
    ai_confidence DECIMAL(3,2),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    committed_at TIMESTAMPTZ,
    commit_sha VARCHAR(64),
    github_issue_url TEXT,
    flux_suspended_at TIMESTAMPTZ,
    flux_resumed_at TIMESTAMPTZ,
    human_review_status VARCHAR(32), -- pending/approved/rejected/modified
    human_review_comment TEXT,
    reviewed_by VARCHAR(128),
    reviewed_at TIMESTAMPTZ,
    rollback_sha VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_defense_actions_incident ON defense_actions(incident_id);
CREATE INDEX idx_defense_actions_review_status ON defense_actions(human_review_status);
CREATE INDEX idx_defense_actions_applied ON defense_actions(applied_at DESC);
```

---

### Phase 6: Web Dossier Enhancements

**Goal**: Show autonomous defense actions in dossier UI

**File to Update**:
```
agent/web_dossier.py
```

**New Section in Dossier Template**:
```html
{% if incident.autonomous_defense_applied %}
<div class="section" style="border-color: #ff9900; background: #221100;">
    <h3 style="color: #ff9900;">🛡️ Autonomous Defense Actions</h3>
    
    <p><strong>Action Taken:</strong> {{ incident.defense_action }}</p>
    <p><strong>AI Confidence:</strong> {{ "%.0f"|format(incident.defense_confidence * 100) }}%</p>
    
    <div style="margin: 15px 0; padding: 10px; background: #111100; border-left: 3px solid #ff9900;">
        <strong>AI Reasoning:</strong><br>
        {{ incident.defense_reasoning }}
    </div>
    
    <p><strong>Status:</strong> 
        {% if incident.human_review_status == 'pending' %}
        <span style="color: #ffaa00;">⏳ Awaiting Human Review</span>
        {% elif incident.human_review_status == 'approved' %}
        <span style="color: #00ff00;">✅ Approved by {{ incident.reviewed_by }}</span>
        {% elif incident.human_review_status == 'rejected' %}
        <span style="color: #ff0000;">❌ Rejected by {{ incident.reviewed_by }}</span>
        {% endif %}
    </p>
    
    {% if incident.github_review_url %}
    <p><strong>Review Issue:</strong> 
        <a href="{{ incident.github_review_url }}" style="color: #ff9900;">
            View on GitHub →
        </a>
    </p>
    {% endif %}
    
    {% if incident.commit_sha %}
    <p><strong>Git Commit:</strong> 
        <code style="background: #002200; color: #ff9900;">{{ incident.commit_sha[:8] }}</code>
    </p>
    {% endif %}
    
    <p style="margin-top: 15px; font-size: 0.85em; color: #aa8800; font-style: italic;">
        This defense was applied autonomously by the AI Defender system.
    </p>
</div>
{% endif %}
```

---

### Phase 7: GitHub Issue Webhook Handler

**Goal**: Allow humans to approve/reject via GitHub comments

**File to Create**:
```
agent/github_webhook_handler.py
```

**Webhook Endpoints**:
```python
@app.route('/github/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub issue comment events."""
    
    event = request.headers.get('X-GitHub-Event')
    if event != 'issue_comment':
        return '', 200
    
    payload = request.json
    comment = payload['comment']['body'].strip()
    issue_url = payload['issue']['html_url']
    user = payload['comment']['user']['login']
    
    # Parse commands
    if comment == '/approve':
        handle_approval(issue_url, user)
    elif comment == '/reject':
        handle_rejection(issue_url, user)
    
    return '', 200

def handle_approval(issue_url: str, user: str):
    """Resume Flux, update database, close issue."""
    
    # Get incident from database
    incident = db.get_incident_by_review_url(issue_url)
    
    # Resume Flux
    flux_controller.resume(incident['kustomization'])
    
    # Update database
    db.update_incident(incident['incident_id'], {
        "human_review_status": "approved",
        "reviewed_by": user,
        "reviewed_at": datetime.utcnow(),
        "flux_suspended": False,
        "flux_resumed_at": datetime.utcnow()
    })
    
    # Close issue
    github.add_comment(issue_url, f"✅ Approved by @{user}. Flux resumed.")
    github.close_issue(issue_url, "approved")

def handle_rejection(issue_url: str, user: str):
    """Revert commit, resume Flux, update database, close issue."""
    
    incident = db.get_incident_by_review_url(issue_url)
    
    # Revert the defense commit
    git_committer.revert_defense(incident['commit_sha'])
    
    # Resume Flux (will reconcile to reverted state)
    flux_controller.resume(incident['kustomization'])
    
    # Update database
    db.update_incident(incident['incident_id'], {
        "human_review_status": "rejected",
        "reviewed_by": user,
        "reviewed_at": datetime.utcnow(),
        "flux_suspended": False,
        "flux_resumed_at": datetime.utcnow()
    })
    
    # Close issue
    github.add_comment(issue_url, f"❌ Rejected by @{user}. Defense reverted, Flux resumed.")
    github.close_issue(issue_url, "rejected")
```

**Setup Required**:
- Register webhook in GitHub repo settings
- Point to: https://mirror-agent.../github/webhook
- Secret token for verification

---

## File Structure (After Implementation)

```
scenario-the-mirror/
├── agent/
│   ├── ai_defender.py              # NEW: LLM reasoning for defense decisions
│   ├── ai_narrator.py              # Existing: Hugging Face narratives
│   ├── defense_actions.py          # NEW: Honeypot redirect, block, rate limit
│   ├── flux_controller.py          # NEW: Suspend/resume Flux
│   ├── git_committer.py            # NEW: Commit defenses with reasoning
│   ├── github_reviewer.py          # NEW: Create/manage review issues
│   ├── github_webhook_handler.py   # NEW: Handle /approve and /reject
│   ├── log_detector.py             # Updated: Add autonomous defense trigger
│   ├── main.py                     # Updated: Initialize all components
│   ├── web_dossier.py              # Updated: Show defense actions
│   └── db.py                       # Updated: New queries
│
├── db/
│   └── schema.sql                  # Updated: defense_actions table
│
├── k8s/
│   ├── emergency-defenses/         # NEW: Generated defense manifests
│   │   ├── redirect-INC-*.yaml
│   │   └── block-INC-*.yaml
│   └── (existing files)
│
└── PLAN_ACTIVE_AI_DEFENDER.md      # This file
```

---

## Configuration

**Environment Variables to Add**:
```bash
# AI Defender
ANTHROPIC_API_KEY=sk-ant-...
AI_DEFENDER_ENABLED=true
AI_DEFENDER_MODEL=claude-sonnet-4.5
AI_CONFIDENCE_THRESHOLD=0.90

# Flux GitOps
FLUX_KUSTOMIZATION=mirror-app
FLUX_NAMESPACE=flux-system

# Git
GIT_REPO_PATH=/workspace/cyber-riposte
GIT_BRANCH=main
GIT_USER_NAME="AI Defender"
GIT_USER_EMAIL="ai-defender@cyber-riposte.local"

# GitHub (already have token)
GITHUB_REPO=hlipsig/cyber-riposte
GITHUB_WEBHOOK_SECRET=<generate>

# Defense Actions
HONEYPOT_SERVICE=honeypot.cyber-riposte.svc.cluster.local
DEFENSE_ACTION_NAMESPACE=cyber-riposte
```

---

## Testing Plan

### Unit Tests:
1. Test `AIDefender.decide_countermeasure()` with various incidents
2. Test `FluxController.suspend()` and `resume()`
3. Test each defense action (redirect, block, rate limit)
4. Test Git commit formatting
5. Test GitHub issue creation

### Integration Tests:
1. **Test 1: Nmap Scan → Honeypot Redirect**
   - Trigger: nmap scan
   - Expected: Redirect to honeypot, Git commit, GitHub issue
   - Verify: Flux suspended, defense active

2. **Test 2: SQL Injection → IP Block**
   - Trigger: SQLi attempt
   - Expected: NetworkPolicy applied, committed, issue created
   - Verify: Attacker blocked

3. **Test 3: Approval Workflow**
   - Comment `/approve` on issue
   - Expected: Flux resumed, database updated, issue closed
   - Verify: Defense remains active

4. **Test 4: Rejection Workflow**
   - Comment `/reject` on issue
   - Expected: Git revert, Flux resumed, defense removed
   - Verify: Back to original state

### End-to-End Test (With Tom!):
1. Tom scans The Mirror
2. AI detects and redirects him to honeypot
3. Tom explores honeypot (doesn't realize)
4. We review GitHub issue
5. Approve the redirect
6. Tom is permanently trapped in honeypot
7. Real Mirror service is protected

---

## Success Metrics

After implementation:
- ✅ Detection → Defense time: <2 seconds
- ✅ All defenses committed to Git: 100%
- ✅ All defenses require human review: 100%
- ✅ GitOps compliance maintained: Yes
- ✅ Full audit trail: Git commits + GitHub issues
- ✅ Reversibility: `git revert` works

---

## Rollout Strategy

### Phase 1: Build Components (Post-Tom CTF)
- Implement all 7 phases above
- Unit test each component
- Integration test the flow

### Phase 2: Deploy to Staging
- Test with simulated attacks
- Verify Flux suspend/resume
- Verify Git commits work
- Verify GitHub issues created

### Phase 3: Test with Real Scans
- Use Nmap against staging
- Verify AI reasoning quality
- Tune confidence thresholds
- Refine commit messages

### Phase 4: Production Deployment
- Deploy to cyber-riposte namespace
- Configure webhooks
- Set conservative thresholds initially
- Monitor first few autonomous actions

### Phase 5: Tune & Expand
- Adjust confidence thresholds based on human approval rate
- Add more defense actions
- Improve AI reasoning prompts
- Expand to other scenarios

---

## Questions to Answer During Implementation

1. **Flux Setup**: Do we already have Flux installed in the cluster?
2. **Kustomization Name**: What's the actual kustomization managing The Mirror?
3. **Git Credentials**: How does the pod authenticate to push to GitHub?
4. **Istio**: Is Istio installed for VirtualService redirects?
5. **Webhook Endpoint**: What's the public URL for GitHub webhooks?
6. **Anthropic API**: What's the rate limit on the API key?
7. **Confidence Tuning**: Start at 0.90 or 0.95 threshold?

---

## Risks & Mitigations

### Risk 1: AI Makes Wrong Decision
**Mitigation**: 
- Require human review for all actions
- Start with high confidence threshold (0.95)
- Log all reasoning for analysis

### Risk 2: Flux Suspension Too Long
**Mitigation**:
- Auto-alert if suspended >4 hours
- Escalate to on-call
- Add auto-resume after timeout

### Risk 3: Git Conflicts
**Mitigation**:
- Pull before commit
- Handle merge conflicts gracefully
- Alert on commit failures

### Risk 4: GitHub API Rate Limits
**Mitigation**:
- Batch multiple incidents into one issue
- Use authenticated requests (higher limits)
- Cache issue creation

### Risk 5: Breaking GitOps
**Mitigation**:
- Never modify files Flux manages directly
- Only add new files in `emergency-defenses/`
- Keep kustomization structure intact

---

## Future Enhancements (Post-Implementation)

1. **Multi-stage Defenses**
   - Escalate from redirect → rate limit → block
   - Based on attacker persistence

2. **Self-Learning Thresholds**
   - Track human approval/rejection rates
   - Auto-adjust confidence thresholds
   - Learn which actions work best

3. **Collaborative Defense**
   - Share threat intelligence across scenarios
   - Block IP in one scenario affects others
   - Coordinated response

4. **Automatic Rollback**
   - If defense causes service degradation
   - Revert automatically and alert
   - Requires health monitoring

5. **LLM-Generated Defenses**
   - AI writes custom Kubernetes manifests
   - Beyond predefined actions
   - Human reviews before applying

---

## Timeline Estimate

- **Phase 1** (Flux Integration): 2-3 hours
- **Phase 2** (LLM Reasoning): 2-3 hours
- **Phase 3** (Defense Actions): 3-4 hours
- **Phase 4** (Integration): 2-3 hours
- **Phase 5** (Database): 1 hour
- **Phase 6** (Web Dossier): 1-2 hours
- **Phase 7** (Webhooks): 2-3 hours

**Total**: ~15-20 hours of implementation + testing

**Realistic Schedule**: 2-3 days of focused work

---

## Next Steps (After Tom's CTF)

1. ✅ Review this plan with you
2. ⏳ Implement Phase 1 (Flux integration)
3. ⏳ Test Flux suspend/resume manually
4. ⏳ Implement Phase 2 (LLM reasoning)
5. ⏳ Test AI decision quality
6. ⏳ Continue through phases 3-7
7. ⏳ End-to-end integration test
8. ⏳ Deploy to production

---

**This plan transforms The Mirror from passive observer to active autonomous defender while maintaining GitOps principles and human oversight.** 🛡️🤖🪞

---

## ADDENDUM: Mature Defensive Actions

**Update**: Replaced simple honeypot/block actions with comprehensive defense catalog.

**See**: `DEFENSIVE_ACTIONS_CATALOG.md` for complete details.

### Key Changes:

**Old Approach** (Demo-level):
- Redirect to honeypot
- Block IP
- Alert only

**New Approach** (Production-ready):
- **6 Tiers of Defense** (speed-optimized)
- **Network isolation** (<1s) - NetworkPolicies
- **Workload isolation** (3s) - Namespace migration
- **Service mesh policies** (5s) - Istio AuthZ, mTLS
- **Traffic engineering** (7s) - Rate limiting, circuit breakers
- **Attack surface reduction** (15s) - Scale down, honeypots
- **Resource constraints** (2s) - Quotas, PDBs

### Competitive AI Scenario:

**The Race**:
```
AI Attacker: Recon (0s) → Enumerate (5s) → Exploit (10s) → Win?
AI Defender: Detect (0.5s) → Reason (1.5s) → Isolate (3s) → Win!
```

**Outcome**: 
- If defender acts in <5s, exploitation fails
- Battlefield changes faster than attacker can adapt
- Not just detection - **prevention through reconfiguration**

### Implementation Updates:

**Phase 3: Defense Actions** becomes:
1. Implement Tier 1 actions (NetworkPolicy) - <1s response
2. Implement Tier 2 actions (Workload isolation) - ~3s response
3. Implement Tier 6 actions (Resource quotas) - ~2s response
4. Add Tier 3-5 in later phases

**AI Decision Matrix**:
- Reconnaissance → Tier 1 (block immediately)
- Exploitation → Tier 2 (isolate workload)
- Lateral movement → Tier 3 (service mesh)
- Data exfiltration → Tier 1 (egress lockdown)
- Credential attack → Tier 4 (rate limiting)
- DoS → Tier 6 (resource constraints)

### Files to Update:

`agent/defense_actions.py` now implements:
```python
class DefenseActions:
    # Tier 1: <1 second
    def apply_network_policy_isolation(incident: Dict) -> tuple[bool, Path]
    def apply_egress_lockdown(incident: Dict) -> tuple[bool, Path]
    
    # Tier 2: 2-5 seconds
    def isolate_workload_to_namespace(incident: Dict) -> tuple[bool, list[Path]]
    def apply_pod_security_hardening(incident: Dict) -> tuple[bool, Path]
    
    # Tier 3: 3-7 seconds
    def apply_istio_authorization_policy(incident: Dict) -> tuple[bool, Path]
    def enforce_mtls(incident: Dict) -> tuple[bool, Path]
    
    # Tier 4: 5-10 seconds
    def apply_rate_limiting(incident: Dict) -> tuple[bool, Path]
    def apply_circuit_breaker(incident: Dict) -> tuple[bool, Path]
    
    # Tier 5: 10-20 seconds
    def scale_down_attack_surface(incident: Dict) -> tuple[bool, list[Path]]
    def inject_honeypot_clone(incident: Dict) -> tuple[bool, list[Path]]
    
    # Tier 6: <3 seconds
    def apply_resource_quotas(incident: Dict) -> tuple[bool, Path]
    def apply_pod_disruption_budget(incident: Dict) -> tuple[bool, Path]
```

**Priority**: Implement Tier 1, 2, and 6 first (fastest, most effective).

---

**This transforms The Mirror from a demo into a legitimate AI-vs-AI competitive defense platform.** ⚡🛡️
