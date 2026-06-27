# The Mirror Helm Chart

AI-powered active defense CTF scenario with autonomous threat intelligence.

## TL;DR

```bash
# Install with default values
helm install the-mirror ./the-mirror -n cyber-riposte --create-namespace

# Install with custom values
helm install the-mirror ./the-mirror -n cyber-riposte \
  --create-namespace \
  --set agent.secrets.shodanApiKey=YOUR_KEY \
  --set agent.secrets.githubToken=YOUR_TOKEN
```

## Introduction

This Helm chart deploys The Mirror CTF scenario on Kubernetes/OpenShift. It includes:

- **Mirror Agent**: AI orchestrator with autonomous decision-making
- **PostgreSQL**: Audit log and incident database
- **Honeypot**: HTTP decoy service (nginx)
- **LLM Server**: Local AI inference (TinyLlama-1.1B)
- **Redis**: OSINT result caching

## Prerequisites

- Kubernetes 1.24+ / OpenShift 4.12+
- Helm 3.12+
- PV provisioner support for persistent volumes
- OpenShift: Route support for external access

## Installing the Chart

### Basic Installation

```bash
helm install the-mirror ./the-mirror \
  -n cyber-riposte \
  --create-namespace
```

### Production Installation

```bash
helm install the-mirror ./the-mirror \
  -n cyber-riposte \
  --create-namespace \
  -f values-production.yaml \
  --set-file agent.secrets.shodanApiKey=secrets/shodan-key.txt \
  --set-file agent.secrets.githubToken=secrets/github-token.txt \
  --set postgres.credentials.password=$(openssl rand -base64 32)
```

### Development Installation

```bash
# Minimal deployment (no LLM, smaller resources)
helm install the-mirror ./the-mirror \
  -n cyber-riposte-dev \
  --create-namespace \
  --set llm.enabled=false \
  --set redis.enabled=false \
  --set postgres.persistence.size=10Gi
```

## Uninstalling the Chart

```bash
# Uninstall the release
helm uninstall the-mirror -n cyber-riposte

# Clean up namespace (if desired)
kubectl delete namespace cyber-riposte
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `agent.replicaCount` | Number of agent replicas | `1` |
| `agent.secrets.shodanApiKey` | Shodan API key for OSINT | `""` |
| `agent.secrets.githubToken` | GitHub token for incident reports | `""` |
| `agent.secrets.dossierPassword` | CTF dossier password | `"i_would_prefer_not_to"` |
| `postgres.enabled` | Enable PostgreSQL database | `true` |
| `postgres.credentials.password` | Database password | `"changeme"` ⚠️  |
| `postgres.persistence.size` | Database volume size | `50Gi` |
| `llm.enabled` | Enable local LLM server | `true` |
| `redis.enabled` | Enable Redis caching | `true` |
| `honeypot.enabled` | Enable honeypot service | `true` |
| `monitoring.enabled` | Enable Prometheus monitoring | `false` |

### Component Configuration

#### Mirror Agent

```yaml
agent:
  replicaCount: 3  # Scale for HA
  eventSource: stdin  # or "kafka"
  
  resources:
    requests:
      memory: "512Mi"
      cpu: "200m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  
  secrets:
    shodanApiKey: "YOUR_SHODAN_KEY"
    githubToken: "ghp_YOUR_TOKEN"
    githubRepo: "your-org/your-repo"
```

#### PostgreSQL

```yaml
postgres:
  credentials:
    password: "SECURE_PASSWORD"  # Change this!
  
  persistence:
    size: 100Gi  # Production size
    storageClass: "fast-ssd"
  
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
```

#### LLM Server

```yaml
llm:
  enabled: true
  model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  
  resources:
    requests:
      memory: "3Gi"  # Model needs RAM
      cpu: "1000m"
    limits:
      memory: "6Gi"
      cpu: "4000m"
```

## Accessing the Application

### Get Routes (OpenShift)

```bash
# Honeypot (CTF entry point)
oc get route honeypot -n cyber-riposte -o jsonpath='{.spec.host}'

# Dossier web app
oc get route dossier -n cyber-riposte -o jsonpath='{.spec.host}'
```

### Get Services (Kubernetes)

```bash
# Port-forward to access locally
kubectl port-forward -n cyber-riposte svc/simple-honeypot 8080:8080
kubectl port-forward -n cyber-riposte svc/mirror-agent 8081:8081
```

## Upgrading

### Upgrade with New Values

```bash
helm upgrade the-mirror ./the-mirror \
  -n cyber-riposte \
  --set agent.replicaCount=3
```

### Rollback

```bash
# List releases
helm list -n cyber-riposte

# Rollback to previous version
helm rollback the-mirror -n cyber-riposte

# Rollback to specific revision
helm rollback the-mirror 2 -n cyber-riposte
```

## Validation

### Lint the Chart

```bash
helm lint ./the-mirror
```

### Dry Run

```bash
helm install the-mirror ./the-mirror \
  -n cyber-riposte \
  --dry-run --debug
```

### Template Rendering

```bash
# Render all templates
helm template the-mirror ./the-mirror

# Render specific templates
helm template the-mirror ./the-mirror \
  --show-only templates/deployments/agent-deployment.yaml
```

## Monitoring

### Check Pod Status

```bash
kubectl get pods -n cyber-riposte -w
```

### View Logs

```bash
# Agent logs
kubectl logs -f deployment/mirror-agent -n cyber-riposte

# Database logs
kubectl logs -f statefulset/postgres -n cyber-riposte

# LLM server logs
kubectl logs -f deployment/llm-server -n cyber-riposte
```

### Database Verification

```bash
# Connect to database
kubectl exec -it statefulset/postgres -n cyber-riposte -- \
  psql -U mirror_agent -d mirror_audit

# List tables
\dt

# Check incidents
SELECT COUNT(*) FROM incidents;
```

## Troubleshooting

### Agent Not Starting

```bash
# Check pod events
kubectl describe pod -l app=mirror-agent -n cyber-riposte

# Check logs
kubectl logs deployment/mirror-agent -n cyber-riposte --previous

# Verify secrets
kubectl get secret mirror-agent-secrets -n cyber-riposte -o yaml
```

### Database Connection Issues

```bash
# Test database connectivity from agent
kubectl exec deployment/mirror-agent -n cyber-riposte -- \
  nc -zv postgres 5432

# Check database password
kubectl get secret postgres-credentials -n cyber-riposte \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

### LLM Server Timeout

```bash
# LLM model loading can take 2-3 minutes
kubectl logs -f deployment/llm-server -n cyber-riposte

# Check startup probe status
kubectl describe pod -l app=llm-server -n cyber-riposte
```

## Values Files

### Production (`values-production.yaml`)

```yaml
agent:
  replicaCount: 3
  resources:
    requests:
      memory: "512Mi"
      cpu: "200m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

postgres:
  persistence:
    size: 100Gi
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "8Gi"
      cpu: "4000m"

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

### Development (`values-development.yaml`)

```yaml
agent:
  replicaCount: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"

llm:
  enabled: false  # Skip LLM in dev

redis:
  enabled: false  # Skip cache in dev

postgres:
  persistence:
    size: 10Gi
```

## Security Notes

⚠️ **IMPORTANT**: Change default passwords before production deployment!

```bash
# Generate secure password
POSTGRES_PASS=$(openssl rand -base64 32)

# Install with secure password
helm install the-mirror ./the-mirror \
  --set postgres.credentials.password="$POSTGRES_PASS"
```

## Support

- **Documentation**: https://github.com/hlipsig/capture-the-flag
- **Issues**: https://github.com/hlipsig/capture-the-flag/issues
- **Game Master Guide**: `docs/reference/GAMEMASTER.md`

## License

MIT License - see LICENSE file for details
