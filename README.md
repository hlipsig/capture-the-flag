# Capture The Flag - The Mirror

An AI-agent-driven defensive security CTF scenario based on The Mirror concept from [cyber-riposte](https://github.com/hlipsig/cyber-riposte).

## Scenario Overview

**The Mirror** is an autonomous security response system that:
1. Detects reconnaissance and attack patterns from telemetry (Suricata IDS alerts)
2. Automatically redirects attackers to honeypots using Istio service mesh
3. Collects evidence via passive OSINT
4. Tracks incidents in a PostgreSQL database
5. **Creates GitHub issues with full incident reports, threat actor dossiers, and evidence**

> *"In fencing, a riposte uses your opponent's forward momentum against them. The Mirror is a digital riposte — they scanned us, so we scanned them back."*

## CTF Integration

This CTF deployment integrates with GitHub to automatically:
- **Create issues** in this repo for each detected incident
- **Attach evidence** as issue comments (OSINT dossiers, audit logs)
- **Apply labels** based on threat level and attack type
- **Post notifications** to Slack channels
- **Track incident lifecycle** from detection to resolution

Each CTF participant's reconnaissance attempt triggers:
1. Real-time detection by The Mirror agent
2. Traffic redirection to Cowrie (SSH) or Glastopf (HTTP) honeypot
3. Passive OSINT collection on the attacker's IP
4. GitHub issue creation with full incident report
5. Slack notification to game administrators

## Architecture

```
┌─────────────────┐
│  Suricata IDS   │──┐
│  (EVE logs)     │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────────────┐
│  Kafka Topic    │◀─┘    │  The Mirror Agent        │
│  (events)       │──────▶│  - Detection             │
└─────────────────┘       │  - OSINT collection      │
                          │  - Action execution      │
                          │  - Incident tracking     │
                          └───────────┬──────────────┘
                                      │
                          ┌───────────┼──────────────┐
                          │           │              │
                          ▼           ▼              ▼
                  ┌─────────────┐ ┌──────┐  ┌──────────────┐
                  │  PostgreSQL │ │ Redis│  │ Istio Mesh   │
                  │  (incidents)│ │(cache)│  │(VirtualSvc)  │
                  └─────────────┘ └──────┘  └──────┬───────┘
                                                    │
                                            ┌───────┼───────┐
                                            │               │
                                            ▼               ▼
                                    ┌─────────────┐ ┌─────────────┐
                                    │   Cowrie    │ │  Glastopf   │
                                    │ (SSH honey) │ │ (HTTP honey)│
                                    └─────────────┘ └─────────────┘
                                            │               │
                                            └───────┬───────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │ GitHub Issues    │
                                          │ + Slack Notifs   │
                                          └──────────────────┘
```

## Setup

### Prerequisites

- OpenShift or Kubernetes cluster
- Istio service mesh installed
- Kafka (Red Hat AMQ Streams)
- PostgreSQL database
- Redis cache
- GitHub personal access token with `repo` scope
- (Optional) Slack webhook URL

### Environment Variables

Create a Kubernetes Secret with:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mirror-integrations
  namespace: ctf
stringData:
  GITHUB_TOKEN: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  GITHUB_REPO: hlipsig/capture-the-flag
  SLACK_WEBHOOK_URL: https://hooks.slack.com/services/xxx/yyy/zzz
  DATABASE_URL: postgresql://user:pass@postgres:5432/mirror
  REDIS_URL: redis://redis:6379/0
  SHODAN_API_KEY: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Deployment

```bash
# Deploy all components
cd scenario-the-mirror
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n ctf

# Check agent logs
kubectl logs -f deployment/mirror-agent -n ctf
```

## Gameplay

### For CTF Participants

1. You are given a target hostname: `redteam.ctf.example.com`
2. Your goal: Find flags hidden in the infrastructure
3. **What you don't know**: Every scan, probe, or attack is being monitored
4. The Mirror will:
   - Detect your reconnaissance (port scans, directory brute force, etc.)
   - Silently redirect you to a honeypot that *looks* like the real system
   - Collect intelligence on your IP, tools, and techniques
   - Create a GitHub issue documenting your entire attack chain

### For Game Administrators

Monitor incidents in real-time:

- **GitHub Issues**: View all incidents at https://github.com/hlipsig/capture-the-flag/issues
- **Slack Notifications**: Receive alerts in #ctf-incidents channel
- **Grafana Dashboard**: Real-time metrics at http://grafana.ctf.example.com
- **Database Queries**: 
  ```sql
  SELECT * FROM incidents WHERE created_at > NOW() - INTERVAL '1 hour';
  ```

### Example Incident Issue

When a participant scans the target, a GitHub issue is automatically created:

```markdown
# [INC-2024-0615-0314] Reconnaissance Detected

**Status**: 🔴 Active
**Detected**: 2024-06-15T03:14:07Z
**Attacker IP**: `203.0.113.42`
**Confidence**: 0.97

---

## Summary

Reconnaissance activity detected from 203.0.113.42. Signature: Nmap port scan. Confidence: 0.97

## Attacker Profile

- **IP Address**: 203.0.113.42
- **Organization**: Example ISP
- **Country**: United States
- **ASN**: AS12345
- **Reverse DNS**: participant-vm.example.com

## Detection Signals

- **IDS Alert**: Port scan detected (confidence: 0.95)
- **User-Agent**: Nmap Scripting Engine (confidence: 1.0)

## Actions Taken

- ✅ **Redirect traffic to honeypot via Istio VirtualService** (2024-06-15T03:14:10Z)
  - Result: success
- ✅ **Run passive OSINT on source IP** (2024-06-15T03:14:12Z)
  - Result: success

## Evidence

### OSINT Data
- [WHOIS](https://github.com/hlipsig/capture-the-flag/issues/123#issuecomment-001)
- [Shodan](https://github.com/hlipsig/capture-the-flag/issues/123#issuecomment-002)

### Honeypot Logs
- [Cowrie SSH Session](https://github.com/hlipsig/capture-the-flag/issues/123#issuecomment-003)

## Timeline

- **2024-06-15T03:14:07Z**: Detection triggered
- **2024-06-15T03:14:10Z**: Redirected to honeypot
- **2024-06-15T03:14:12Z**: OSINT collection complete

## Recommendations

- Review OSINT data for additional IOCs
- Check if this IP is part of a larger campaign
- Consider adjusting detection thresholds if false positive

---

**Generated**: 2024-06-15T03:14:15Z
**Agent Version**: 1.0.0
🤖 Generated by [The Mirror](https://github.com/hlipsig/capture-the-flag)
```

## Features

### Automated Incident Response

- **Detection**: Rule-based + Claude AI decision layer
- **Redirection**: Istio VirtualService routes attackers to honeypots
- **OSINT**: Passive intelligence gathering (WHOIS, Shodan, rDNS, Certificate Transparency)
- **Evidence**: PCAP capture, honeypot logs, audit trail
- **Database**: PostgreSQL stores all incidents and evidence
- **Caching**: Redis caches OSINT lookups (7-day TTL)
- **Rate Limiting**: Token bucket prevents API quota exhaustion

### GitHub Integration

- **Issue Creation**: One issue per incident with full report
- **Evidence Comments**: OSINT dossiers posted as comments
- **Labels**: Auto-applied based on severity and attack type
- **Milestones**: Group incidents by week/month
- **Notifications**: Slack webhooks for real-time alerts

### Observability

- **Prometheus Metrics**: Event rates, detection latency, action success
- **Grafana Dashboards**: Real-time incident visualization
- **Audit Logs**: Complete action history in database
- **OpenTelemetry Traces**: End-to-end request tracing

## Configuration

### Action Pool

Edit `k8s/agent-configmap.yaml` to customize responses:

```yaml
actions:
  - id: "redirect-to-honeypot"
    tier: 1
    cooldown_seconds: 3600
    expires_after_seconds: 86400  # 24 hours
```

### Detection Rules

Edit `agent/detector.py` to add custom detection logic:

```python
def detect_custom_pattern(event):
    if event.get("alert", {}).get("signature") == "My Custom Rule":
        return {
            "signature": "Custom Attack Detected",
            "confidence": 0.95,
            "timestamp": event["timestamp"],
        }
    return None
```

## Testing

### Unit Tests

```bash
cd scenario-the-mirror
pytest tests/ -v
```

### Integration Tests

```bash
# Start test Kafka producer
python event-producer-sim.py --rate 1 --duration 60

# Verify agent consumes events
kubectl logs -f deployment/mirror-agent -n ctf | grep "Processing event"

# Check GitHub issues
gh issue list --repo hlipsig/capture-the-flag --label incident
```

### Manual Testing

Trigger a detection manually:

```bash
# Publish fake Suricata EVE event to Kafka
echo '{
  "event_type": "alert",
  "timestamp": "2024-06-15T03:14:07.000000+0000",
  "src_ip": "203.0.113.42",
  "dest_ip": "10.0.1.100",
  "alert": {
    "signature": "ET SCAN Nmap Scripting Engine User-Agent Detected",
    "category": "Attempted Information Leak"
  },
  "http": {
    "http_user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)"
  }
}' | kafka-console-producer --broker-list localhost:9092 --topic suricata-events
```

## Troubleshooting

### No GitHub issues created

1. Check GitHub token has `repo` scope:
   ```bash
   kubectl get secret mirror-integrations -n ctf -o jsonpath='{.data.GITHUB_TOKEN}' | base64 -d
   ```

2. Check agent logs for GitHub API errors:
   ```bash
   kubectl logs deployment/mirror-agent -n ctf | grep -i github
   ```

3. Verify network connectivity to GitHub API:
   ```bash
   kubectl exec deployment/mirror-agent -n ctf -- curl -I https://api.github.com
   ```

### Honeypot not receiving traffic

1. Check VirtualService was created:
   ```bash
   kubectl get virtualservice -n ctf
   ```

2. Verify Istio Gateway configuration:
   ```bash
   istioctl analyze -n ctf
   ```

3. Check honeypot pods are running:
   ```bash
   kubectl get pods -n ctf -l app=honeypot
   ```

## References

- [cyber-riposte](https://github.com/hlipsig/cyber-riposte) - Original concept and scenario
- [The Mirror TALK.md](scenario-the-mirror/TALK.md) - 5-minute presentation version
- [Phase Implementation Plan](scenario-the-mirror/PRODUCTION-OPENSHIFT-PLAN.md) - Full architecture
- [Jinja2 Templates](scenario-the-mirror/templates/) - Report templates used for GitHub issues

## License

MIT License - See LICENSE file

## Disclaimer

This is a **Capture The Flag game environment**. The techniques demonstrated here are for educational purposes only. Do not use these techniques against systems you do not own or have explicit permission to test.

The automated defensive responses in this scenario (traffic redirection, passive OSINT) should be reviewed by legal and compliance teams before production deployment.
