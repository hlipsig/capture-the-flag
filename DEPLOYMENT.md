# Deployment Guide - The Mirror CTF

Complete deployment guide for The Mirror Capture The Flag environment with GitHub integration.

## Prerequisites

- OpenShift 4.x or Kubernetes 1.25+
- Istio service mesh installed
- `kubectl` or `oc` CLI configured
- GitHub personal access token
- (Optional) Slack incoming webhook URL

## Quick Start

```bash
# Clone repository
git clone https://github.com/hlipsig/capture-the-flag.git
cd capture-the-flag/scenario-the-mirror

# Create namespace
kubectl create namespace ctf

# Configure secrets
kubectl create secret generic mirror-integrations \
  --from-literal=GITHUB_TOKEN=ghp_your_token_here \
  --from-literal=GITHUB_REPO=hlipsig/capture-the-flag \
  --from-literal=DATABASE_URL=postgresql://mirror:password@postgres:5432/mirror \
  --from-literal=REDIS_URL=redis://redis:6379/0 \
  --from-literal=SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -n ctf

# Deploy infrastructure
kubectl apply -f k8s/ -n ctf

# Verify deployment
kubectl get pods -n ctf
```

## Detailed Setup

### 1. GitHub Personal Access Token

Create a GitHub token with `repo` scope:

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Name: `mirror-ctf-integration`
4. Scopes:
   - ✅ `repo` (Full control of private repositories)
5. Click **Generate token**
6. **Copy the token** (starts with `ghp_`)

### 2. Slack Webhook (Optional)

Create a Slack incoming webhook:

1. Go to https://api.slack.com/apps
2. Create a new app
3. Enable **Incoming Webhooks**
4. Add webhook to workspace
5. Select channel: `#ctf-incidents`
6. **Copy the webhook URL**

### 3. Configure Secrets

Edit `k8s/integrations-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mirror-integrations
  namespace: ctf
type: Opaque
stringData:
  GITHUB_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Your token
  GITHUB_REPO: "hlipsig/capture-the-flag"
  SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/xxx/yyy/zzz"
  DATABASE_URL: "postgresql://mirror:password@postgres:5432/mirror"
  REDIS_URL: "redis://redis:6379/0"
  SHODAN_API_KEY: "your_shodan_key"  # Optional
```

Apply the secret:

```bash
kubectl apply -f k8s/integrations-secret.yaml
```

### 4. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-pvc.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n ctf --timeout=120s

# Initialize database schema
kubectl apply -f k8s/postgres-init-job.yaml
```

### 5. Deploy Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
```

### 6. Deploy Kafka (Development)

For development, deploy standalone Kafka:

```bash
kubectl apply -f k8s/kafka-statefulset.yaml
kubectl apply -f k8s/kafka-service.yaml
```

For production, use **Red Hat AMQ Streams** operator.

### 7. Deploy Istio Components

```bash
# Deploy Istio Gateway
kubectl apply -f k8s/istio/gateway.yaml

# Deploy default VirtualService (will be modified by agent)
kubectl apply -f k8s/istio/virtualservice-default.yaml

# Create RBAC for agent to manage VirtualServices
kubectl apply -f k8s/agent-rbac-istio.yaml
```

### 8. Deploy Honeypots

```bash
# Cowrie SSH honeypot
kubectl apply -f k8s/honeypot-cowrie.yaml

# Glastopf HTTP honeypot
kubectl apply -f k8s/honeypot-glastopf.yaml

# Unified honeypot service
kubectl apply -f k8s/honeypot-service.yaml

# PCAP capture DaemonSet
kubectl apply -f k8s/pcap-capture.yaml
```

### 9. Deploy The Mirror Agent

```bash
# ConfigMaps for action pool and detection rules
kubectl apply -f k8s/agent-configmap.yaml

# Agent deployment
kubectl apply -f k8s/agent-deployment.yaml
kubectl apply -f k8s/agent-service.yaml
```

### 10. Deploy Observability Stack

```bash
# ServiceMonitor for Prometheus
kubectl apply -f k8s/servicemonitor.yaml

# Import Grafana dashboard
# Upload dashboards/mirror-agent-grafana.json to Grafana
```

## Verification

### Check All Pods Running

```bash
kubectl get pods -n ctf

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# mirror-agent-xxxxx                1/1     Running   0          2m
# postgres-0                        1/1     Running   0          5m
# redis-xxxxx                       1/1     Running   0          4m
# kafka-0                           1/1     Running   0          4m
# honeypot-cowrie-xxxxx             1/1     Running   0          3m
# honeypot-glastopf-xxxxx           1/1     Running   0          3m
```

### Check Agent Logs

```bash
kubectl logs -f deployment/mirror-agent -n ctf

# Should see:
# INFO - GitHub integration initialized for hlipsig/capture-the-flag
# INFO - Slack integration initialized
# INFO - Starting Kafka consumer...
```

### Test GitHub Integration

Send a test event to Kafka:

```bash
kubectl exec -it kafka-0 -n ctf -- /bin/bash

# Inside Kafka pod:
echo '{
  "event_type": "alert",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%6N%z)'",
  "src_ip": "203.0.113.42",
  "dest_ip": "10.0.1.100",
  "alert": {
    "signature": "ET SCAN Nmap Scripting Engine User-Agent Detected",
    "category": "Attempted Information Leak"
  },
  "http": {
    "http_user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine)"
  }
}' | kafka-console-producer --broker-list localhost:9092 --topic suricata-events
```

Check GitHub for new issue:

```bash
gh issue list --repo hlipsig/capture-the-flag --label incident
```

### Test Slack Integration

Check your `#ctf-incidents` channel for notification.

### Test Honeypot Redirection

```bash
# Check VirtualService was created
kubectl get virtualservice -n ctf

# Should see:
# NAME                    GATEWAYS         HOSTS   AGE
# redirect-203-0-113-42   [istio-gateway]  [*]     1m
```

## CTF Participant Access

### DNS Configuration

Point `redteam.ctf.example.com` to your Istio Ingress Gateway:

```bash
# Get Ingress Gateway IP
kubectl get svc istio-ingressgateway -n istio-system

# Add DNS A record:
# redteam.ctf.example.com -> <INGRESS_IP>
```

### Firewall Rules

Allow inbound traffic on:
- TCP 80 (HTTP)
- TCP 443 (HTTPS)
- TCP 22 (SSH - honeypot)
- TCP 23 (Telnet - honeypot)

### SSL/TLS Certificate

Deploy cert-manager and request Let's Encrypt certificate:

```bash
kubectl apply -f k8s/istio/certificate.yaml
```

## Monitoring

### Grafana Dashboard

1. Access Grafana: `http://grafana.ctf.example.com`
2. Import dashboard: `dashboards/mirror-agent-grafana.json`
3. View metrics:
   - Event rate
   - Detection latency
   - Active incidents
   - OSINT cache hit rate

### Prometheus Metrics

Access Prometheus: `http://prometheus.ctf.example.com`

Query examples:
```promql
# Events processed per second
rate(mirror_events_total[1m])

# Active incidents
mirror_incidents_active

# OSINT cache hit rate
rate(mirror_osint_cache_hits_total[5m]) / rate(mirror_osint_cache_total[5m])
```

### Database Queries

Connect to PostgreSQL:

```bash
kubectl exec -it postgres-0 -n ctf -- psql -U mirror -d mirror

-- View recent incidents
SELECT * FROM incidents WHERE created_at > NOW() - INTERVAL '1 hour';

-- View action stats
SELECT action_name, COUNT(*) FROM audit_log GROUP BY action_name;

-- View active VirtualServices
SELECT * FROM virtualservices WHERE deleted_at IS NULL;
```

## Troubleshooting

### No GitHub Issues Created

1. **Check GitHub token**:
   ```bash
   kubectl get secret mirror-integrations -n ctf -o jsonpath='{.data.GITHUB_TOKEN}' | base64 -d
   ```

2. **Check agent logs**:
   ```bash
   kubectl logs deployment/mirror-agent -n ctf | grep -i github
   ```

3. **Test GitHub API connectivity**:
   ```bash
   kubectl exec deployment/mirror-agent -n ctf -- curl -H "Authorization: token ghp_xxx" https://api.github.com/user
   ```

### No Slack Notifications

1. **Check webhook URL**:
   ```bash
   kubectl get secret mirror-integrations -n ctf -o jsonpath='{.data.SLACK_WEBHOOK_URL}' | base64 -d
   ```

2. **Test webhook**:
   ```bash
   kubectl exec deployment/mirror-agent -n ctf -- curl -X POST \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test from The Mirror"}' \
     <WEBHOOK_URL>
   ```

### Honeypot Not Receiving Traffic

1. **Check VirtualService exists**:
   ```bash
   kubectl get virtualservice -n ctf
   ```

2. **Check Istio configuration**:
   ```bash
   istioctl analyze -n ctf
   ```

3. **Check honeypot pods**:
   ```bash
   kubectl get pods -l app=honeypot -n ctf
   kubectl logs deployment/honeypot-cowrie -n ctf
   ```

### Agent Not Consuming Kafka Events

1. **Check Kafka connectivity**:
   ```bash
   kubectl exec deployment/mirror-agent -n ctf -- nc -zv kafka 9092
   ```

2. **Check Kafka topic exists**:
   ```bash
   kubectl exec -it kafka-0 -n ctf -- kafka-topics --list --bootstrap-server localhost:9092
   ```

3. **Check consumer group**:
   ```bash
   kubectl exec -it kafka-0 -n ctf -- kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group mirror-agent \
     --describe
   ```

## Scaling

### Horizontal Scaling

Scale agent replicas:

```bash
kubectl scale deployment mirror-agent --replicas=3 -n ctf
```

Kafka consumer group ensures no duplicate processing.

### Database Connection Pooling

Increase connection pool size in agent configuration:

```yaml
env:
  - name: DB_POOL_SIZE
    value: "20"
  - name: DB_MAX_OVERFLOW
    value: "10"
```

### OSINT Cache TTL

Adjust Redis cache TTL (default 7 days):

```yaml
env:
  - name: OSINT_CACHE_TTL
    value: "604800"  # seconds
```

## Backup and Recovery

### Database Backup

```bash
kubectl exec postgres-0 -n ctf -- pg_dump -U mirror mirror > mirror-backup.sql
```

### Database Restore

```bash
kubectl exec -i postgres-0 -n ctf -- psql -U mirror -d mirror < mirror-backup.sql
```

### Export GitHub Issues

```bash
gh issue list --repo hlipsig/capture-the-flag \
  --label incident \
  --state all \
  --json number,title,body,labels,createdAt \
  --jq '.' > incidents-backup.json
```

## Security Considerations

1. **Rotate GitHub Token** every 90 days
2. **Rotate Slack Webhook** if compromised
3. **Database Encryption** at rest and in transit
4. **Network Policies** to restrict pod-to-pod traffic
5. **RBAC** - agent has minimal required permissions
6. **Secret Management** - use external secrets operator for production

## Production Checklist

- [ ] GitHub token has `repo` scope only (not full `admin`)
- [ ] Slack webhook is channel-specific
- [ ] Database credentials are strong (not default password)
- [ ] TLS enabled on all external endpoints
- [ ] Resource limits set on all pods
- [ ] Horizontal Pod Autoscaler configured
- [ ] PersistentVolumes have backup retention policy
- [ ] Network Policies restrict pod communication
- [ ] Pod Security Standards enforced (baseline or restricted)
- [ ] Monitoring alerts configured (PagerDuty, OpsGenie)
- [ ] Runbooks documented for common issues
- [ ] Incident response procedures defined
- [ ] Legal review completed for honeypot deployment

## License

MIT License

## Support

For issues or questions:
- GitHub: https://github.com/hlipsig/capture-the-flag/issues
- Documentation: https://github.com/hlipsig/cyber-riposte
