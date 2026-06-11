#!/bin/bash
set -e

echo "=================================="
echo "The Mirror CTF - Quick Setup"
echo "=================================="
echo ""

# Check prerequisites
if ! command -v oc &> /dev/null; then
    echo "❌ Error: 'oc' command not found. Please install OpenShift CLI."
    exit 1
fi

# Create namespace
echo "📦 Creating namespace..."
oc new-project cyber-riposte 2>/dev/null || oc project cyber-riposte

# Deploy infrastructure
echo "🗄️  Deploying PostgreSQL..."
oc apply -f k8s/postgres-deployment.yaml

echo "💾 Deploying Redis..."
oc apply -f k8s/redis-deployment.yaml

echo "📁 Creating storage..."
oc apply -f k8s/agent-pvc.yaml

# Create secrets
echo "🔐 Creating secrets..."
oc create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=mirror_agent \
  --from-literal=POSTGRES_PASSWORD=changeme \
  --from-literal=POSTGRES_DB=mirror_audit \
  --dry-run=client -o yaml | oc apply -f -

# Prompt for Shodan key (optional)
read -p "🔑 Enter Shodan API key (or press Enter to skip): " SHODAN_KEY
SHODAN_KEY=${SHODAN_KEY:-dummy_key}
oc create secret generic shodan-api-key \
  --from-literal=SHODAN_API_KEY=$SHODAN_KEY \
  --dry-run=client -o yaml | oc apply -f -

# Deploy RBAC
echo "👤 Setting up permissions..."
oc apply -f k8s/agent-rbac.yaml

# Create config
echo "⚙️  Creating configuration..."
oc create configmap mirror-config \
  --from-file=action-pool.yaml \
  --dry-run=client -o yaml | oc apply -f -

# Build agent
echo "🔨 Building agent (this may take 10-15 minutes)..."
oc start-build mirror-agent --from-dir=. --follow

# Deploy agent
echo "🚀 Deploying agent..."
oc apply -f k8s/agent-deployment.yaml

# Deploy honeypot
echo "🍯 Deploying honeypot..."
oc apply -f k8s/simple-honeypot.yaml
oc apply -f k8s/honeypot-routes.yaml

# Deploy dossier web
echo "📊 Deploying dossier web interface..."
oc apply -f k8s/dossier-service.yaml

# Wait for pods
echo "⏳ Waiting for pods to be ready..."
sleep 10
oc wait --for=condition=ready pod -l app=simple-honeypot --timeout=120s
oc wait --for=condition=ready pod -l app=mirror-agent --timeout=120s

# Seed database
echo "🌱 Seeding database..."
sleep 5
oc exec postgres-0 -- psql -U mirror_agent -d mirror_audit << 'SQL'
-- Add decoy incidents
INSERT INTO incidents (incident_id, attacker_ip, first_seen, last_updated, status, detection_signature, detection_confidence, actions_count, ai_narrative)
VALUES 
  ('INC-2026-06-09-143022', '45.127.83.229', NOW() - interval '2 days', NOW() - interval '2 days', 
   'active', 'ET SCAN WPScan WordPress Security Scanner', 0.92, 0, 
   'WordPress vulnerability scanner detected. Automated reconnaissance of CMS infrastructure.'),
  ('INC-2026-06-10-092145', '185.234.67.142', NOW() - interval '1 day', NOW() - interval '1 day',
   'active', 'ET WEB_SERVER SQL Injection Attempt', 0.88, 0,
   'SQL injection attempt targeting database layer. Manual exploitation effort detected.'),
  ('INC-2026-06-10-183017', '92.185.34.78', NOW() - interval '1 day', NOW() - interval '1 day',
   'active', 'High Request Rate Detected', 0.75, 0,
   'Abnormal traffic volume from single source. Possible DDoS reconnaissance.'),
  ('INC-2026-06-11-010834', '203.115.42.91', NOW() - interval '12 hours', NOW() - interval '12 hours',
   'active', 'ET SCAN Directory Brute Force (gobuster)', 0.94, 0,
   'Directory enumeration tool detected. Systematic endpoint discovery in progress.'),
  ('INC-2026-06-11-034556', '172.98.12.34', NOW() - interval '8 hours', NOW() - interval '8 hours',
   'active', 'ET SCAN Nikto Web Scanner', 0.91, 0,
   'Nikto vulnerability scanner identified. Comprehensive web application testing.'),
  ('INC-2026-06-11-041203', '194.45.26.78', NOW() - interval '6 hours', NOW() - interval '6 hours',
   'active', 'ET SCAN Burp Suite Scanner', 0.89, 0,
   'Professional penetration testing tool detected. Advanced exploitation framework in use.')
ON CONFLICT (incident_id) DO NOTHING;
SQL

# Get URLs
echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
echo ""
HONEYPOT_URL=$(oc get route redteam -o jsonpath='{.spec.host}' 2>/dev/null || echo "NOT FOUND")
DOSSIER_URL=$(oc get route dossier-web -o jsonpath='{.spec.host}' 2>/dev/null || echo "NOT FOUND")

echo "🎯 Honeypot (attack target): https://$HONEYPOT_URL"
echo "📊 Dossier System: https://$DOSSIER_URL"
echo ""
echo "🔑 Dossier Credentials:"
echo "   Username: ctf"
echo "   Password: i_would_prefer_not_to"
echo ""
echo "=================================="
echo "Next Steps:"
echo "1. Give players only the honeypot URL"
echo "2. Monitor: oc logs -f -l app=simple-honeypot"
echo "3. Create incidents: See PLAYBOOK.md"
echo "=================================="
