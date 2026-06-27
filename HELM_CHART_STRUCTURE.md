# Helm Chart Structure for The Mirror

## Proposed Directory Structure

```
helm/
└── the-mirror/
    ├── Chart.yaml                      # Chart metadata
    ├── values.yaml                     # Default configuration values
    ├── values-production.yaml          # Production overrides
    ├── values-development.yaml         # Development overrides
    ├── README.md                       # Chart documentation
    ├── .helmignore                     # Files to ignore
    │
    ├── templates/
    │   ├── NOTES.txt                   # Post-install instructions
    │   ├── _helpers.tpl                # Template helpers
    │   │
    │   ├── namespace.yaml              # Namespace creation
    │   │
    │   ├── configmaps/
    │   │   ├── agent-config.yaml       # Agent configuration (action-pool, user-agents)
    │   │   ├── postgres-init.yaml      # Database initialization scripts
    │   │   ├── redis-config.yaml       # Redis configuration
    │   │   └── honeypot-content.yaml   # Honeypot web content
    │   │
    │   ├── secrets/
    │   │   ├── agent-secrets.yaml      # API keys, database URL, GitHub token
    │   │   └── postgres-credentials.yaml # Database credentials
    │   │
    │   ├── deployments/
    │   │   ├── agent-deployment.yaml   # Main Mirror agent
    │   │   ├── llm-server.yaml         # Local LLM inference server
    │   │   ├── honeypot.yaml           # Simple HTTP honeypot
    │   │   └── redis.yaml              # OSINT cache
    │   │
    │   ├── statefulsets/
    │   │   └── postgres.yaml           # PostgreSQL database
    │   │
    │   ├── services/
    │   │   ├── agent-service.yaml      # Agent health & dossier endpoints
    │   │   ├── llm-service.yaml        # LLM server service
    │   │   ├── honeypot-service.yaml   # Honeypot service
    │   │   ├── postgres-service.yaml   # Database service
    │   │   └── redis-service.yaml      # Redis service
    │   │
    │   ├── routes/
    │   │   ├── honeypot-route.yaml     # OpenShift route for honeypot
    │   │   └── dossier-route.yaml      # OpenShift route for dossier web app
    │   │
    │   ├── rbac/
    │   │   ├── serviceaccount.yaml     # Service account for agent
    │   │   ├── role.yaml               # Role for agent permissions
    │   │   └── rolebinding.yaml        # Role binding
    │   │
    │   ├── storage/
    │   │   ├── agent-pvc.yaml          # Persistent storage for audit logs
    │   │   └── postgres-pvc.yaml       # PostgreSQL data volume (in StatefulSet)
    │   │
    │   ├── monitoring/
    │   │   └── servicemonitor.yaml     # Prometheus ServiceMonitor (optional)
    │   │
    │   └── jobs/
    │       └── postgres-init-job.yaml  # Database schema initialization
    │
    ├── charts/                         # Subchart dependencies (if any)
    │
    └── tests/
        └── test-connection.yaml        # Helm test resources

```

## Chart Components Breakdown

### Core Services (Always Deployed)

1. **mirror-agent** - Main AI orchestrator
   - Deployment with configurable replicas
   - ConfigMap for action-pool.yaml and suspicious-user-agents.yaml
   - Secret for API keys (Shodan, GitHub, Slack)
   - PVC for audit logs
   - Health/readiness probes
   - RBAC (ServiceAccount, Role, RoleBinding)

2. **postgres** - Audit log database
   - StatefulSet with persistent volume
   - Secret for credentials
   - ConfigMap for init scripts
   - Service (headless for StatefulSet)

3. **honeypot** - HTTP decoy service
   - Deployment (nginx)
   - ConfigMap with web content
   - Service
   - OpenShift Route (external access)

### Optional Services (Controlled by values.yaml)

4. **llm-server** - Local LLM inference (optional)
   - Deployment (TinyLlama-1.1B)
   - Service
   - Enabled via `llm.enabled: true`

5. **redis** - OSINT caching (optional)
   - Deployment
   - ConfigMap for redis.conf
   - Service
   - Enabled via `redis.enabled: true`

6. **kafka** - Event streaming (future, optional)
   - Not included in initial chart
   - Can be added via subchart dependency

### OpenShift-Specific Resources

- **Routes** - External access (honeypot, dossier web app)
- **SecurityContextConstraints** - If needed for privileged operations

## Key Values Structure (values.yaml)

```yaml
# Global settings
global:
  namespace: cyber-riposte
  imageRegistry: image-registry.openshift-image-registry.svc:5000

# Mirror Agent configuration
agent:
  replicaCount: 1
  image:
    repository: cyber-riposte/mirror-agent
    tag: latest
    pullPolicy: Always
  
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m
  
  # Configuration
  eventSource: stdin  # or "kafka"
  logLevel: INFO
  logFormat: json
  
  # Integrations (secrets)
  secrets:
    shodanApiKey: ""
    githubToken: ""
    githubRepo: "hlipsig/capture-the-flag"
    slackWebhookUrl: ""
    databaseUrl: "postgresql://mirror_agent:changeme@postgres:5432/mirror_audit"
    dossierPassword: "i_would_prefer_not_to"

# PostgreSQL database
postgres:
  enabled: true
  image:
    repository: postgres
    tag: 15-alpine
  
  credentials:
    user: mirror_agent
    password: changeme
    database: mirror_audit
  
  persistence:
    size: 50Gi
    storageClass: ""  # Use default
  
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 2Gi
      cpu: 1000m

# LLM Server (optional)
llm:
  enabled: true
  image:
    repository: cyber-riposte/llm-server
    tag: latest
  
  model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  
  resources:
    requests:
      memory: 2Gi
      cpu: 500m
    limits:
      memory: 4Gi
      cpu: 2000m

# Redis cache (optional)
redis:
  enabled: true
  image:
    repository: redis
    tag: 7-alpine
  
  maxMemory: 256mb
  
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m

# Honeypot
honeypot:
  enabled: true
  image:
    repository: nginxinc/nginx-unprivileged
    tag: alpine
  
  content:
    # Customizable web content for CTF
    indexHtml: |
      <!DOCTYPE html>...
  
  route:
    enabled: true
    host: ""  # Auto-generated if empty
    tls:
      enabled: true
      termination: edge

# Dossier web app
dossier:
  route:
    enabled: true
    host: ""  # Auto-generated if empty
    tls:
      enabled: true
      termination: edge

# Monitoring (optional)
monitoring:
  enabled: false
  serviceMonitor:
    enabled: false
    interval: 30s

# RBAC
rbac:
  create: true
  serviceAccount:
    create: true
    name: mirror-agent

# Storage
persistence:
  enabled: true
  storageClass: ""
  size: 10Gi
  accessMode: ReadWriteOnce
```

## Installation Commands

```bash
# Install with default values
helm install the-mirror ./helm/the-mirror -n cyber-riposte --create-namespace

# Install with custom values
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --create-namespace \
  -f custom-values.yaml

# Install with overrides
helm install the-mirror ./helm/the-mirror \
  -n cyber-riposte \
  --create-namespace \
  --set agent.replicaCount=3 \
  --set llm.enabled=false \
  --set postgres.persistence.size=100Gi

# Upgrade
helm upgrade the-mirror ./helm/the-mirror -n cyber-riposte

# Uninstall
helm uninstall the-mirror -n cyber-riposte
```

## Benefits of Helm Chart

1. **Single Command Deployment**: Deploy entire stack with one command
2. **Parameterization**: Easy configuration via values.yaml
3. **Environment-Specific Configs**: Different values files for dev/prod
4. **Version Management**: Track deployment versions
5. **Rollback Support**: Easy rollback to previous versions
6. **Template Reuse**: DRY principle with helpers and conditionals
7. **Dependencies**: Manage subchart dependencies
8. **Lifecycle Hooks**: Pre/post install/upgrade hooks
9. **Testing**: Built-in test framework
10. **Documentation**: NOTES.txt provides post-install instructions

## Testing Strategy

```bash
# Lint the chart
helm lint ./helm/the-mirror

# Dry run (see rendered manifests)
helm install the-mirror ./helm/the-mirror --dry-run --debug

# Template (render without installing)
helm template the-mirror ./helm/the-mirror

# Run Helm tests
helm test the-mirror -n cyber-riposte

# Verify deployment
kubectl get all -n cyber-riposte
```

## Next Steps

1. Create base Chart.yaml and values.yaml
2. Convert existing k8s manifests to Helm templates
3. Add template helpers (_helpers.tpl)
4. Create values-production.yaml and values-development.yaml
5. Write NOTES.txt with post-install instructions
6. Add Helm tests
7. Test deployment on OpenShift cluster
8. Document in README.md
