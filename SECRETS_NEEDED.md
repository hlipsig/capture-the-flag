# Secrets Required for Mirror Agent Configuration

**Date Created:** 2026-06-09  
**Status:** Pending - Need to gather these secrets

---

## Required Secrets Checklist

### 1. ✅ DATABASE_URL (Already Configured)
- **Status:** ✅ Already set up
- **Current Value:** `postgresql://mirror_agent:changeme@postgres.cyber-riposte.svc.cluster.local:5432/mirror_audit`
- **Action:** None needed - PostgreSQL is running in the cluster

---

### 2. 🔑 SHODAN_API_KEY (High Priority)

**What it's for:** OSINT lookups on attacker IPs
- Discovers open ports on attacker infrastructure
- Identifies services and versions running
- Finds known vulnerabilities
- Essential for the "counter-reconnaissance" feature

**Where to get it:**
1. Go to: https://account.shodan.io/register
2. Sign up for an account
3. Navigate to: https://account.shodan.io/
4. Copy your API key

**Pricing:**
- Free tier: 100 API results/month (good for testing)
- Membership: $59/month for unlimited queries
- Academic: Free with .edu email

**Current Value:** `placeholder-update-me`

**Format:** String like `ABC123XYZ456DEF789...`

---

### 3. 📋 GITHUB_TOKEN (Medium Priority)

**What it's for:** Auto-creating GitHub issues for incident reports
- Agent creates detailed incident reports as GitHub issues
- Includes attacker dossier, evidence, and remediation steps
- Enables team collaboration on threat response

**Where to get it:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Mirror Agent - Incident Reports"
4. Set expiration (recommend: 90 days or No expiration)
5. Select scopes:
   - ✅ `repo` (if using private repositories)
   - OR ✅ `public_repo` (if using public repositories only)
6. Click "Generate token"
7. **Copy the token immediately** (you won't see it again!)

**Current Value:** `placeholder-update-me`

**Format:** Starts with `ghp_` like `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 4. 🔔 SLACK_WEBHOOK_URL (Optional but Nice)

**What it's for:** Real-time notifications to Slack
- Alerts on-call team when threats detected
- Posts incident summaries to Slack channel
- Enables quick response even when away from desk

**Where to get it:**
1. Go to: https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Mirror Agent" 
4. Select your workspace
5. Click "Incoming Webhooks" in left sidebar
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select the channel (e.g., #security-alerts)
9. Click "Allow"
10. Copy the Webhook URL (starts with `https://hooks.slack.com/services/...`)

**Current Value:** `https://hooks.slack.com/services/placeholder`

**Format:** `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

---

## How to Provide the Secrets When You Return

### Option 1: Paste them in chat (secure session)

Just send me a message like this:
```
SHODAN_API_KEY=abc123def456...
GITHUB_TOKEN=ghp_xyz789...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Option 2: I'll ask you for them

When you reconnect, just say "I have the secrets" and I'll prompt you for each one.

---

## What I'll Do With Them

Once you provide the secrets, I'll update the OpenShift configuration:

```bash
# Update Shodan API key
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"SHODAN_API_KEY":"your-actual-key"}}'

# Update GitHub token
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"GITHUB_TOKEN":"ghp_your-token"}}'

# Update Slack webhook
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"SLACK_WEBHOOK_URL":"https://hooks.slack.com/..."}}'

# Restart the agent to pick up new secrets
oc rollout restart deployment/mirror-agent -n cyber-riposte
```

---

## Priority Guide

**Start with this order:**

1. **SHODAN_API_KEY** - Core functionality, enables OSINT lookups
2. **SLACK_WEBHOOK_URL** - Quick to set up, immediate value for notifications
3. **GITHUB_TOKEN** - Nice for incident tracking but not critical for initial testing

**Minimum to get started:** Just the Shodan API key! The agent will work without GitHub/Slack, you just won't get those integrations.

---

## Testing After Configuration

Once secrets are updated, test with:

```bash
# Check agent logs
oc logs -f deployment/mirror-agent -n cyber-riposte

# Should see:
# ✅ "OSINT module initialized with Shodan API"
# ✅ "GitHub integration enabled"
# ✅ "Slack notifications enabled"
```

---

## Security Notes

- **Never commit these secrets to git**
- **Use secure channels** to share them (this chat session is encrypted)
- **Rotate GitHub tokens** every 90 days
- **Slack webhooks** can be revoked and regenerated if compromised
- **Shodan API keys** are tied to your account - keep them private

---

## Current Secret Status in OpenShift

**Namespace:** `cyber-riposte`  
**Secret Name:** `mirror-agent-secrets`

**Current values:**
```yaml
SHODAN_API_KEY: "placeholder-update-me"           # 🔴 NEEDS UPDATE
DATABASE_URL: "postgresql://mirror_agent:..."      # ✅ CONFIGURED
GITHUB_TOKEN: "placeholder-update-me"              # 🔴 NEEDS UPDATE
SLACK_WEBHOOK_URL: "https://hooks.../placeholder" # 🔴 NEEDS UPDATE
```

---

## Questions?

When you return with the secrets, you can also ask me:
- How to test if the secrets are working
- How to rotate/update secrets later
- How to see what the agent does with these credentials
- Troubleshooting if something doesn't work

---

## Quick Reference Links

- **Shodan:** https://account.shodan.io/
- **GitHub Tokens:** https://github.com/settings/tokens
- **Slack Apps:** https://api.slack.com/apps
- **OpenShift Console:** https://console-openshift-console.apps.uu7a1hfd.eastus.aroapp.io
- **This Deployment:** `/Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror/`

---

**See you when you're back with the secrets!** 🔐
