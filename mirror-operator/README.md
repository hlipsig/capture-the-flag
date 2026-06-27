# Mirror Operator

Kubernetes operator for The Mirror CTF active defense system.

## Architecture

### Why an Operator?

**Previous Python approach issues:**
- Fragile imports and path issues  
- Required NET_ADMIN capabilities for nftables
- Custom dict structures instead of standards
- Thread safety concerns

**Operator benefits:**
- ✅ Native Kubernetes reconciliation patterns
- ✅ CloudEvents-compatible event format
- ✅ NetworkPolicy for blocking (no nftables hacks)
- ✅ Standard CRD-based API
- ✅ Controller-runtime testing framework
- ✅ Go performance and reliability

### Flow

```
┌─────────────────────┐
│ Detection Pod       │
│ (Python)            │
│ - Watches logs      │
│ - Detects patterns  │
└──────┬──────────────┘
       │ creates
       ↓
┌─────────────────────────────────┐
│ IncidentDetection CRD           │
│ apiVersion: mirror.ctf/v1alpha1 │
│ kind: IncidentDetection         │
│ spec:                           │
│   attackerIP: 10.131.0.16       │
│   detectionSignature: "Nikto"   │
│   confidence: 0.98              │
└──────┬──────────────────────────┘
       │ watches
       ↓
┌─────────────────────┐
│ Mirror Operator     │
│ (Go)                │
│ - Reconciles CRDs   │
│ - Executes actions  │
└──────┬──────────────┘
       │ creates
       ├──→ NetworkPolicy (blocks IP)
       ├──→ OSINT enrichment (async)
       └──→ Updates .status

Dossier reads:
  IncidentDetection.status.actionsExecuted
```

## CRD Schema

### IncidentDetection

```yaml
apiVersion: mirror.ctf/v1alpha1
kind: IncidentDetection
metadata:
  name: inc-20260627-123456-10-131-0-16
  namespace: cyber-riposte
spec:
  attackerIP: "10.131.0.16"
  detectionSignature: "ET SCAN Nikto Web Scanner"
  confidence: 0.98
  source: "production-portal"
  evidence:
    userAgent: "Nikto/2.1.5"
    path: "/admin"
    method: "GET"
status:
  phase: "Responding"
  message: "2 actions executed"
  lastUpdated: "2026-06-27T08:00:00Z"
  actionsExecuted:
    - type: "networkpolicy-block"
      timestamp: "2026-06-27T08:00:01Z"
      success: true
      details: "Blocked 10.131.0.16 via NetworkPolicy"
      resourceRef:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: block-inc-20260627-123456
        namespace: cyber-riposte
    - type: "osint-lookup"
      timestamp: "2026-06-27T08:00:02Z"
      success: true
      details: "OSINT data collected"
```

## Defensive Actions

The operator automatically executes actions based on incident characteristics:

### 1. NetworkPolicy Block (`networkpolicy-block`)

**When**: Confidence >= 0.90

Creates a Kubernetes NetworkPolicy that denies ingress from the attacker IP to production pods.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-inc-XXXXXX
spec:
  podSelector:
    matchLabels:
      app: production-portal
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.131.0.16/32  # DENY this IP
    ports:
    - protocol: TCP
      port: 8000
```

### 2. OSINT Lookup (`osint-lookup`)

**When**: Always

Enriches incident with:
- Shodan data (if API key available)
- Whois information
- Reverse DNS
- Geo-location

Results stored in `.status.osintData`

### 3. Traffic Redirect (`redirect` - future)

**When**: High-value targets

Would use Istio VirtualService or Envoy to redirect attacker traffic to honeypot.

## Building & Deploying

### Prerequisites

```bash
# Install Go 1.21+
go version

# Access to Kubernetes cluster
kubectl cluster-info
```

### Build

```bash
cd mirror-operator

# Download dependencies
go mod download

# Build binary
go build -o bin/manager main.go

# Build Docker image
docker build -t mirror-operator:latest .
```

### Deploy to OpenShift

```bash
# Install CRD
kubectl apply -f config/crd/bases/mirror.ctf_incidentdetections.yaml

# Create operator deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mirror-operator
  namespace: cyber-riposte
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mirror-operator
  template:
    metadata:
      labels:
        app: mirror-operator
    spec:
      serviceAccountName: mirror-operator
      containers:
      - name: manager
        image: mirror-operator:latest
        command:
        - /manager
        args:
        - --leader-elect
        ports:
        - containerPort: 8080
          name: metrics
        - containerPort: 8081
          name: health
EOF
```

### RBAC

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mirror-operator
  namespace: cyber-riposte
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mirror-operator
rules:
- apiGroups: ["mirror.ctf"]
  resources: ["incidentdetections"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["mirror.ctf"]
  resources: ["incidentdetections/status"]
  verbs: ["get", "update", "patch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mirror-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mirror-operator
subjects:
- kind: ServiceAccount
  name: mirror-operator
  namespace: cyber-riposte
EOF
```

## Testing

```bash
# Create a test incident
kubectl apply -f - <<EOF
apiVersion: mirror.ctf/v1alpha1
kind: IncidentDetection
metadata:
  name: test-incident
  namespace: cyber-riposte
spec:
  attackerIP: "192.168.1.100"
  detectionSignature: "Test Attack"
  confidence: 0.95
  source: "manual-test"
EOF

# Watch the operator reconcile
kubectl logs -f deployment/mirror-operator -n cyber-riposte

# Check the incident status
kubectl get incident test-incident -n cyber-riposte -o yaml

# Verify NetworkPolicy was created
kubectl get networkpolicy -n cyber-riposte | grep test-incident
```

## CloudEvents Compatibility

The IncidentDetection CRD is designed to be compatible with CloudEvents v1.0 spec.

```json
{
  "specversion": "1.0",
  "type": "com.mirror.detection.scanner",
  "source": "production-portal",
  "id": "inc-20260627-123456",
  "time": "2026-06-27T08:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "attackerIP": "10.131.0.16",
    "detectionSignature": "ET SCAN Nikto Web Scanner",
    "confidence": 0.98,
    "userAgent": "Nikto/2.1.5"
  }
}
```

## Migration from Python

### Python Log Watcher Changes

Instead of executing actions directly:

```python
# OLD (broken)
from agent.actions import execute_redirect

# NEW (operator-based)
from kubernetes import client
from kubernetes.client.rest import ApiException

def create_incident_detection(attacker_ip, detection_data):
    """Create IncidentDetection CR instead of direct action"""
    incident = {
        "apiVersion": "mirror.ctf/v1alpha1",
        "kind": "IncidentDetection",
        "metadata": {
            "name": f"inc-{timestamp}-{ip_sanitized}",
            "namespace": "cyber-riposte"
        },
        "spec": {
            "attackerIP": attacker_ip,
            "detectionSignature": detection_data['signature'],
            "confidence": detection_data['confidence'],
            "source": "production-portal",
            "evidence": detection_data.get('evidence', {})
        }
    }
    
    custom_api = client.CustomObjectsApi()
    custom_api.create_namespaced_custom_object(
        group="mirror.ctf",
        version="v1alpha1",
        namespace="cyber-riposte",
        plural="incidentdetections",
        body=incident
    )
```

### Dossier Changes

Read from CRD instead of database:

```python
def get_incident_actions(incident_id):
    """Read actions from IncidentDetection CR"""
    custom_api = client.CustomObjectsApi()
    incident = custom_api.get_namespaced_custom_object(
        group="mirror.ctf",
        version="v1alpha1",
        namespace="cyber-riposte",
        plural="incidentdetections",
        name=incident_id
    )
    return incident['status'].get('actionsExecuted', [])
```

## Next Steps

1. ✅ Operator scaffolding complete
2. ⏳ Build and test operator
3. ⏳ Update Python watchers to create CRs
4. ⏳ Update dossier to read from CRs
5. ⏳ Add OSINT implementation
6. ⏳ Add Istio/Envoy redirect support
7. ⏳ Metrics and observability

## References

- [Kubernetes Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [controller-runtime](https://github.com/kubernetes-sigs/controller-runtime)
- [CloudEvents spec](https://cloudevents.io/)
- [NetworkPolicy docs](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
