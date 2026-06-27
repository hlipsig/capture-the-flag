# Mirror Scenario - OpenShift Deployment Summary

**Date:** 2026-06-09  
**Cluster:** https://api.uu7a1hfd.eastus.aroapp.io:6443  
**Namespace:** cyber-riposte

## Deployment Status

### ✅ Successfully Deployed

1. **Namespace**: `cyber-riposte` 
   - Created and active

2. **ConfigMaps**:
   - `mirror-agent-config` - Action pool and suspicious user-agent signatures
   - `redis-config` - Redis configuration
   - `postgres-init` - PostgreSQL initialization
   - `postgres-schema` - Database schema
   - `cowrie-config` - Cowrie SSH honeypot config
   - `glastopf-config` - Glastopf web honeypot config

3. **Secrets**:
   - `mirror-agent-secrets` - Contains:
     - `SHODAN_API_KEY`: placeholder-update-me
     - `DATABASE_URL`: postgresql://mirror_agent:changeme@postgres.cyber-riposte.svc.cluster.local:5432/mirror_audit
     - `GITHUB_TOKEN`: placeholder-update-me
     - `SLACK_WEBHOOK_URL`: https://hooks.slack.com/services/placeholder
   - `postgres-credentials` - PostgreSQL credentials

4. **RBAC Resources**:
   - ServiceAccount: `mirror-agent`
   - Role: `mirror-agent`
   - RoleBinding: `mirror-agent`

5. **PostgreSQL Database** ✅:
   - StatefulSet: `postgres` (1/1 READY)
   - Service: `postgres` (ClusterIP None - Headless)
   - Image: `docker.io/postgres:15-alpine`
   - Storage: 50Gi PVC
   - Status: **Running and Ready**

6. **Redis Cache** ✅:
   - Deployment: `redis` (1/1 READY)
   - Service: `redis` (ClusterIP)
   - Image: `redis:7-alpine`
   - Max Memory: 256MB with LRU eviction
   - Status: **Running and Ready**

7. **Honeypot Services**:
   - Service: `cowrie` (SSH honeypot - ports 2222, 2223)
   - Service: `glastopf` (Web honeypot - port 8080)
   - Service: `honeypot-service` (Combined service - ports 8080, 22, 23)

### ⚠️ Partially Deployed / Issues

1. **Honeypot Pods** (cowrie, glastopf):
   - StatefulSets created but pods not running
   - **Issue**: OpenShift Security Context Constraints (SCC) blocking pod creation
   - **Reason**: Honeypot images require specific user IDs (uid 1000) which conflict with OpenShift's restricted SCC policy
   - **Fix Needed**: Either:
     - Grant `anyuid` SCC to service accounts
     - Rebuild honeypot images to work with arbitrary UIDs
     - Use init containers to adjust permissions

2. **PostgreSQL Init Job**:
   - Job running but pod in ImagePullBackOff
   - Not critical - schema can be applied manually if needed

### ❌ Not Yet Deployed

1. **Mirror Agent**:
   - Deployment manifest exists: `agent-deployment.yaml`
   - **Blocker**: Container image not built/pushed yet
   - **Next Steps**:
     - Build container image from `scenario-the-mirror/Dockerfile`
     - Push to accessible registry (quay.io, docker.io, or OpenShift internal registry)
     - Update image reference in deployment manifest
     - Deploy with `oc apply -f scenario-the-mirror/k8s/agent-deployment.yaml`

## Network Topology

```
cyber-riposte namespace
├── PostgreSQL (postgres.cyber-riposte.svc.cluster.local:5432)
│   └── Database: mirror_audit
├── Redis (redis.cyber-riposte.svc.cluster.local:6379)
│   └── OSINT result caching
├── Honeypot Service (honeypot-service.cyber-riposte.svc.cluster.local)
│   ├── HTTP: 8080
│   ├── SSH: 22
│   └── Telnet: 23
└── Mirror Agent (not deployed yet)
    └── Will connect to all above services
```

## Next Steps

### 1. Update Secrets (High Priority)

Replace placeholder values with actual credentials:

```bash
# Update Shodan API key
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"SHODAN_API_KEY":"your-actual-key"}}'

# Update GitHub token
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"GITHUB_TOKEN":"ghp_your-actual-token"}}'

# Update Slack webhook
oc patch secret mirror-agent-secrets -n cyber-riposte \
  -p '{"stringData":{"SLACK_WEBHOOK_URL":"https://hooks.slack.com/services/YOUR/WEBHOOK"}}'
```

### 2. Build and Deploy Mirror Agent

```bash
# From the scenario-the-mirror directory
cd /Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror

# Option A: Build and push to external registry (e.g., quay.io)
docker build -t quay.io/YOUR_USERNAME/mirror-agent:latest .
docker push quay.io/YOUR_USERNAME/mirror-agent:latest

# Update the image in agent-deployment.yaml
# Then deploy:
oc apply -f k8s/agent-deployment.yaml
oc apply -f k8s/agent-service.yaml

# Option B: Use OpenShift internal registry
oc new-build --binary --name=mirror-agent -n cyber-riposte
oc start-build mirror-agent --from-dir=. --follow -n cyber-riposte
# Update image to: image-registry.openshift-image-registry.svc:5000/cyber-riposte/mirror-agent:latest
```

### 3. Fix Honeypot Deployments

**Option A: Grant anyuid SCC (easier, less secure)**

```bash
oc adm policy add-scc-to-user anyuid -z default -n cyber-riposte
oc rollout restart statefulset/cowrie -n cyber-riposte
oc rollout restart statefulset/glastopf -n cyber-riposte
```

**Option B: Fix security contexts (more secure, recommended)**

Edit the honeypot YAML files to remove `runAsUser` specifications and add proper `seccompProfile`:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
    - ALL
```

### 4. Optional: Deploy Kafka (for Phase 2)

If you want event streaming instead of stdin:

```bash
oc apply -f k8s/kafka-deployment.yaml
oc apply -f k8s/agent-deployment-kafka.yaml
```

### 5. Optional: Deploy Observability Stack

```bash
# Prometheus metrics
oc apply -f k8s/servicemonitor.yaml

# PCAP capture
oc apply -f k8s/pcap-capture.yaml

# Evidence collector
oc apply -f k8s/evidence-collector.yaml
```

## Verification Commands

```bash
# Check all resources
oc get all -n cyber-riposte

# Check pod logs
oc logs -f statefulset/postgres -n cyber-riposte
oc logs -f deployment/redis -n cyber-riposte

# Test PostgreSQL connection
oc exec -it postgres-0 -n cyber-riposte -- psql -U mirror_agent -d mirror_audit

# Test Redis connection
oc exec -it deployment/redis -n cyber-riposte -- redis-cli ping

# Check events
oc get events -n cyber-riposte --sort-by='.lastTimestamp'
```

## Troubleshooting

### Issue: Session timeout
**Solution**: Re-login with `oc login`

### Issue: Pods not starting due to SCC violations
**Solution**: See "Fix Honeypot Deployments" section above

### Issue: Image pull errors
**Solution**: 
- Check image name and tag
- Verify registry authentication
- For Red Hat registry images, use public alternatives (e.g., `postgres:15-alpine` instead of `registry.redhat.io/rhel9/postgresql-15`)

## Configuration Files Modified

The following files were updated to work with OpenShift:

1. `/Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror/k8s/postgres-deployment.yaml`
   - Changed image from `registry.redhat.io/rhel9/postgresql-15:latest` to `docker.io/postgres:15-alpine`
   - Updated environment variable names (POSTGRESQL_* → POSTGRES_*)
   - Fixed volume mount paths for standard PostgreSQL image
   - Added PGDATA environment variable

2. `/Users/hlipsig/REPOS/cyber-riposte/scenario-the-mirror/k8s/redis-deployment.yaml`
   - Removed hardcoded `runAsUser: 999`
   - Added `seccompProfile` for OpenShift compliance
   - Fixed inline comment in Redis config that was causing parse errors

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenShift Cluster                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              cyber-riposte namespace                  │  │
│  │                                                       │  │
│  │  ┌──────────────┐        ┌──────────────┐           │  │
│  │  │  PostgreSQL  │        │    Redis     │           │  │
│  │  │ (StatefulSet)│        │ (Deployment) │           │  │
│  │  │   ✅ Ready   │        │   ✅ Ready   │           │  │
│  │  └──────┬───────┘        └──────┬───────┘           │  │
│  │         │                       │                    │  │
│  │         │                       │                    │  │
│  │  ┌──────┴───────────────────────┴───────┐           │  │
│  │  │         Mirror Agent                 │           │  │
│  │  │        (Not Deployed)                │           │  │
│  │  │    Needs: Container Image            │           │  │
│  │  └──────────────┬───────────────────────┘           │  │
│  │                 │                                    │  │
│  │                 ▼                                    │  │
│  │  ┌────────────────────────────────────────┐         │  │
│  │  │       Honeypot Services                │         │  │
│  │  │  ┌────────────┐  ┌────────────────┐   │         │  │
│  │  │  │   Cowrie   │  │   Glastopf     │   │         │  │
│  │  │  │(StatefulSet)│  │ (StatefulSet)  │   │         │  │
│  │  │  │ ⚠️  Blocked │  │  ⚠️  Blocked   │   │         │  │
│  │  │  │  by SCC    │  │   by SCC       │   │         │  │
│  │  │  └────────────┘  └────────────────┘   │         │  │
│  │  └────────────────────────────────────────┘         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Summary

**Working Services:**
- ✅ PostgreSQL database (ready for audit log storage)
- ✅ Redis cache (ready for OSINT result caching)
- ✅ All services, configmaps, and secrets created

**Requires Action:**
- 🔨 Build and push Mirror Agent container image
- 🔨 Deploy Mirror Agent
- 🔐 Update secret placeholders with real API keys
- 🔧 Fix honeypot SCC issues (optional, for advanced testing)

**Namespace is ready** for Mirror Agent deployment once the container image is available!
