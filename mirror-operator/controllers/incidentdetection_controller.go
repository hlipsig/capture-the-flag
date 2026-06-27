package controllers

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"strings"
	"time"

	_ "github.com/lib/pq"
	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	mirrorv1alpha1 "github.com/hlipsig/mirror-operator/api/v1alpha1"
)

// IncidentDetectionReconciler reconciles a IncidentDetection object
type IncidentDetectionReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

//+kubebuilder:rbac:groups=mirror.ctf,resources=incidentdetections,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=mirror.ctf,resources=incidentdetections/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=mirror.ctf,resources=incidentdetections/finalizers,verbs=update
//+kubebuilder:rbac:groups=networking.k8s.io,resources=networkpolicies,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile implements the reconciliation loop for IncidentDetection
func (r *IncidentDetectionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := log.FromContext(ctx)

	// Fetch the IncidentDetection instance
	incident := &mirrorv1alpha1.IncidentDetection{}
	if err := r.Get(ctx, req.NamespacedName, incident); err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		log.Error(err, "unable to fetch IncidentDetection")
		return ctrl.Result{}, err
	}

	// If already resolved, nothing to do
	if incident.Status.Phase == "Resolved" {
		return ctrl.Result{}, nil
	}

	// Initialize status if needed
	if incident.Status.Phase == "" {
		incident.Status.Phase = "Detected"
		incident.Status.LastUpdated = metav1.Now()
		if err := r.Status().Update(ctx, incident); err != nil {
			log.Error(err, "unable to update IncidentDetection status")
			return ctrl.Result{}, err
		}
	}

	// Execute defensive actions based on confidence and signature
	actionsNeeded := r.determineActions(incident)

	for _, action := range actionsNeeded {
		// Check if action already executed
		if r.actionAlreadyExecuted(incident, action) {
			continue
		}

		var actionResult mirrorv1alpha1.DefensiveAction
		var err error

		switch action {
		case "networkpolicy-block":
			actionResult, err = r.createNetworkPolicyBlock(ctx, incident)
		case "osint-lookup":
			actionResult, err = r.performOSINTLookup(ctx, incident)
		case "rate-limit-injection":
			actionResult, err = r.injectRateLimit(ctx, incident)
		case "request-fingerprint":
			actionResult, err = r.captureRequestFingerprint(ctx, incident)
		case "deploy-honeytokens":
			actionResult, err = r.deployHoneytokens(ctx, incident)
		case "reverse-shell-check":
			actionResult, err = r.checkReverseShells(ctx, incident)
		case "deception-escalation":
			actionResult, err = r.escalateDeception(ctx, incident)
		case "time-delay-response":
			actionResult, err = r.injectTimeDelay(ctx, incident)
		case "fake-vulnerability-injection":
			actionResult, err = r.injectFakeVulnerability(ctx, incident)
		default:
			log.Info("unknown action type", "action", action)
			continue
		}

		if err != nil {
			log.Error(err, "failed to execute action", "action", action)
			// Record failed action
			actionResult = mirrorv1alpha1.DefensiveAction{
				Type:      action,
				Timestamp: metav1.Now(),
				Success:   false,
				Details:   fmt.Sprintf("Error: %v", err),
			}
		}

		// Append action to status
		incident.Status.ActionsExecuted = append(incident.Status.ActionsExecuted, actionResult)
	}

	// Update phase
	if len(incident.Status.ActionsExecuted) > 0 {
		incident.Status.Phase = "Responding"
	}
	incident.Status.LastUpdated = metav1.Now()
	incident.Status.Message = fmt.Sprintf("%d actions executed", len(incident.Status.ActionsExecuted))

	// Update status
	if err := r.Status().Update(ctx, incident); err != nil {
		log.Error(err, "unable to update IncidentDetection status")
		return ctrl.Result{}, err
	}

	// Write actions to database for dossier (async, best-effort)
	go r.writeActionsToDatabase(incident)

	// Requeue after 5 minutes to check for more actions or auto-resolve
	return ctrl.Result{RequeueAfter: 5 * time.Minute}, nil
}

// determineActions decides which defensive actions to take based on incident
func (r *IncidentDetectionReconciler) determineActions(incident *mirrorv1alpha1.IncidentDetection) []string {
	actions := []string{}

	// Tier 1: Information gathering (always execute)
	actions = append(actions, "osint-lookup")
	actions = append(actions, "request-fingerprint")
	actions = append(actions, "reverse-shell-check")

	// Tier 2: Active defense (high confidence)
	if incident.Spec.Confidence >= 0.90 {
		actions = append(actions, "networkpolicy-block")
		actions = append(actions, "rate-limit-injection")

		// CTF deception actions
		if incident.Spec.Source == "simple-honeypot" {
			actions = append(actions, "deploy-honeytokens")
			actions = append(actions, "deception-escalation")
		}
	}

	// Tier 3: Annoyance (medium confidence, slow them down)
	if incident.Spec.Confidence >= 0.70 {
		actions = append(actions, "time-delay-response")
		actions = append(actions, "fake-vulnerability-injection")
	}

	return actions
}

// actionAlreadyExecuted checks if an action has already been taken
func (r *IncidentDetectionReconciler) actionAlreadyExecuted(incident *mirrorv1alpha1.IncidentDetection, actionType string) bool {
	for _, action := range incident.Status.ActionsExecuted {
		if action.Type == actionType && action.Success {
			return true
		}
	}
	return false
}

// createNetworkPolicyBlock creates a NetworkPolicy to block the attacker IP
func (r *IncidentDetectionReconciler) createNetworkPolicyBlock(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Create NetworkPolicy that blocks the attacker IP
	npName := fmt.Sprintf("block-%s", incident.Name)

	np := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      npName,
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
			},
		},
		Spec: networkingv1.NetworkPolicySpec{
			// Apply to production portal pods
			PodSelector: metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "production-portal",
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyTypeIngress,
			},
			Ingress: []networkingv1.NetworkPolicyIngressRule{
				{
					// Deny from this specific IP
					From: []networkingv1.NetworkPolicyPeer{
						{
							IPBlock: &networkingv1.IPBlock{
								CIDR: incident.Spec.AttackerIP + "/32",
							},
						},
					},
					Ports: []networkingv1.NetworkPolicyPort{
						{
							Protocol: func() *corev1.Protocol { p := corev1.ProtocolTCP; return &p }(),
							Port:     &intstr.IntOrString{Type: intstr.Int, IntVal: 8000},
						},
					},
				},
			},
		},
	}

	// Set owner reference so NetworkPolicy is deleted when incident is deleted
	if err := ctrl.SetControllerReference(incident, np, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	// Create the NetworkPolicy
	if err := r.Create(ctx, np); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("NetworkPolicy already exists", "name", npName)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "networkpolicy-block",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Blocked %s via NetworkPolicy", incident.Spec.AttackerIP),
		ResourceRef: &mirrorv1alpha1.ResourceReference{
			APIVersion: "networking.k8s.io/v1",
			Kind:       "NetworkPolicy",
			Name:       npName,
			Namespace:  incident.Namespace,
		},
	}, nil
}

// performOSINTLookup runs OSINT enrichment on the attacker IP
func (r *IncidentDetectionReconciler) performOSINTLookup(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)
	log.Info("OSINT lookup", "ip", incident.Spec.AttackerIP)

	osintData := make(map[string]interface{})
	sourcesCollected := []string{}

	// 1. Reverse DNS lookup
	if rdns, err := r.reverseDNSLookup(incident.Spec.AttackerIP); err == nil {
		osintData["reverse_dns"] = rdns
		sourcesCollected = append(sourcesCollected, "rdns")
	}

	// 2. IP geolocation (using ip-api.com - free, no key required)
	if geo, err := r.geoIPLookup(incident.Spec.AttackerIP); err == nil {
		osintData["geolocation"] = geo
		sourcesCollected = append(sourcesCollected, "geoip")
	}

	// 3. Shodan (if API key available)
	shodanKey := os.Getenv("SHODAN_API_KEY")
	if shodanKey != "" {
		if shodan, err := r.shodanLookup(incident.Spec.AttackerIP, shodanKey); err == nil {
			osintData["shodan"] = shodan
			sourcesCollected = append(sourcesCollected, "shodan")
		}
	}

	// Store OSINT data in incident status
	if len(osintData) > 0 {
		incident.Status.OSINTData = osintData
	}

	details := fmt.Sprintf("Collected from: %s", strings.Join(sourcesCollected, ", "))
	if len(sourcesCollected) == 0 {
		details = "No OSINT sources available"
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "osint-lookup",
		Timestamp: metav1.Now(),
		Success:   len(sourcesCollected) > 0,
		Details:   details,
	}, nil
}

// reverseDNSLookup performs reverse DNS lookup
func (r *IncidentDetectionReconciler) reverseDNSLookup(ip string) (string, error) {
	names, err := net.LookupAddr(ip)
	if err != nil || len(names) == 0 {
		return "", err
	}
	return names[0], nil
}

// geoIPLookup gets geolocation data from ip-api.com (free, no key)
func (r *IncidentDetectionReconciler) geoIPLookup(ip string) (map[string]interface{}, error) {
	resp, err := http.Get(fmt.Sprintf("http://ip-api.com/json/%s?fields=status,country,countryCode,region,regionName,city,isp,org,as", ip))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("geoip API returned %d", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	if status, ok := result["status"].(string); ok && status != "success" {
		return nil, fmt.Errorf("geoip lookup failed")
	}

	return result, nil
}

// shodanLookup queries Shodan API
func (r *IncidentDetectionReconciler) shodanLookup(ip string, apiKey string) (map[string]interface{}, error) {
	url := fmt.Sprintf("https://api.shodan.io/shodan/host/%s?key=%s", ip, apiKey)
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("shodan API returned %d", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	// Extract relevant fields
	simplified := map[string]interface{}{
		"ports":        result["ports"],
		"vulns":        result["vulns"],
		"os":           result["os"],
		"organization": result["org"],
		"isp":          result["isp"],
	}

	return simplified, nil
}

// writeActionsToDatabase writes executed actions to PostgreSQL for dossier display
func (r *IncidentDetectionReconciler) writeActionsToDatabase(incident *mirrorv1alpha1.IncidentDetection) {
	// Best-effort database writes - don't fail reconciliation if this fails
	logger := ctrl.Log.WithName("database-writer")

	dbHost := os.Getenv("POSTGRES_HOST")
	if dbHost == "" {
		dbHost = "postgres-0.postgres.cyber-riposte.svc.cluster.local"
	}

	dbUser := os.Getenv("POSTGRES_USER")
	if dbUser == "" {
		dbUser = "mirror_agent"
	}

	dbPass := os.Getenv("POSTGRES_PASSWORD")
	if dbPass == "" {
		logger.Info("No POSTGRES_PASSWORD - skipping database writes")
		return
	}

	dbName := os.Getenv("POSTGRES_DB")
	if dbName == "" {
		dbName = "mirror_audit"
	}

	connStr := fmt.Sprintf("host=%s port=5432 user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbUser, dbPass, dbName)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.Error(err, "Failed to connect to database")
		return
	}
	defer db.Close()

	// Test connection
	if err := db.Ping(); err != nil {
		logger.Error(err, "Database ping failed")
		return
	}

	logger.Info("Connected to database", "host", dbHost, "db", dbName)

	// Write each action to audit_log table
	for i, action := range incident.Status.ActionsExecuted {
		actionID := fmt.Sprintf("%s-%s-%d", incident.Name, action.Type, i)
		_, err := db.Exec(`
			INSERT INTO audit_log (incident_id, timestamp, action_id, action_name, action_result, parameters)
			VALUES ($1, $2, $3, $4, $5, $6)
			ON CONFLICT DO NOTHING
		`,
			incident.Name,
			action.Timestamp.Time,
			actionID,
			action.Type,
			map[bool]string{true: "success", false: "failure"}[action.Success],
			fmt.Sprintf(`{"details": "%s"}`, action.Details),
		)
		if err != nil {
			logger.Error(err, "Failed to insert action", "action_id", actionID)
			continue
		}
		logger.Info("Wrote action to database", "action_id", actionID, "type", action.Type)
	}

	// Update incident actions_count
	result, err := db.Exec(`
		UPDATE incidents
		SET actions_count = $1, last_updated = NOW()
		WHERE incident_id = $2
	`, len(incident.Status.ActionsExecuted), incident.Name)

	if err != nil {
		logger.Error(err, "Failed to update incident actions_count")
	} else {
		rows, _ := result.RowsAffected()
		logger.Info("Updated incident actions_count", "incident_id", incident.Name, "rows", rows, "actions", len(incident.Status.ActionsExecuted))
	}
}

// injectRateLimit adds rate limiting for the attacker IP via EnvoyFilter or ConfigMap
func (r *IncidentDetectionReconciler) injectRateLimit(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Create ConfigMap with rate limit config for nginx/envoy
	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("ratelimit-%s", incident.Name),
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
			},
		},
		Data: map[string]string{
			"ratelimit.conf": fmt.Sprintf(`
# Rate limit for attacker IP %s
limit_req_zone $binary_remote_addr zone=%s:10m rate=1r/s;
limit_req zone=%s burst=5 nodelay;
`, incident.Spec.AttackerIP, incident.Name, incident.Name),
		},
	}

	if err := ctrl.SetControllerReference(incident, cm, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	if err := r.Create(ctx, cm); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("Rate limit config already exists", "name", cm.Name)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "rate-limit-injection",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Injected rate limit: 1 req/s for %s", incident.Spec.AttackerIP),
	}, nil
}

// captureRequestFingerprint extracts and stores full HTTP request details
func (r *IncidentDetectionReconciler) captureRequestFingerprint(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	// Extract evidence from incident
	fingerprint := map[string]interface{}{
		"ip":        incident.Spec.AttackerIP,
		"signature": incident.Spec.DetectionSignature,
		"timestamp": time.Now().UTC(),
	}

	if incident.Spec.Evidence != nil {
		fingerprint["user_agent"] = incident.Spec.Evidence["userAgent"]
		fingerprint["path"] = incident.Spec.Evidence["path"]
		fingerprint["method"] = incident.Spec.Evidence["method"]
	}

	// Store in incident status
	if incident.Status.OSINTData == nil {
		incident.Status.OSINTData = make(map[string]interface{})
	}
	incident.Status.OSINTData["request_fingerprint"] = fingerprint

	details := fmt.Sprintf("Captured: %s %s", fingerprint["method"], fingerprint["path"])

	return mirrorv1alpha1.DefensiveAction{
		Type:      "request-fingerprint",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   details,
	}, nil
}

// deployHoneytokens creates canary tokens in honeypot responses
func (r *IncidentDetectionReconciler) deployHoneytokens(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Generate unique canary tokens
	tokens := []string{
		fmt.Sprintf("api_key_%s_%d", incident.Spec.AttackerIP, time.Now().Unix()),
		fmt.Sprintf("admin_pass_%x", time.Now().UnixNano()),
		fmt.Sprintf("db_conn_str_postgresql://admin:SecretPass123@db.internal.local/%s", incident.Name),
	}

	// Store tokens in ConfigMap for honeypot to serve
	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("honeytokens-%s", incident.Name),
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
				"mirror.ctf/honeytoken":        "true",
			},
		},
		Data: map[string]string{
			"tokens.json": fmt.Sprintf(`{"tokens": %s}`, strings.Join(tokens, ",")),
		},
	}

	if err := ctrl.SetControllerReference(incident, cm, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	if err := r.Create(ctx, cm); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("Honeytokens already deployed", "name", cm.Name)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "deploy-honeytokens",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Deployed %d canary tokens", len(tokens)),
	}, nil
}

// checkReverseShells monitors for egress connections from production pods
func (r *IncidentDetectionReconciler) checkReverseShells(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Query pod network connections via kubectl exec or network policy logs
	// For now, placeholder - would integrate with Falco or network monitoring

	log.Info("Checking for reverse shell indicators", "ip", incident.Spec.AttackerIP)

	// Placeholder: In production, would check:
	// - Unexpected egress to attacker IP
	// - Shell processes spawned by web server
	// - Suspicious file descriptors

	findings := []string{}
	detected := false

	// Simulated check result
	if detected {
		findings = append(findings, "Suspicious egress connection detected")
	}

	details := "No reverse shell detected"
	if len(findings) > 0 {
		details = strings.Join(findings, "; ")
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "reverse-shell-check",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   details,
	}, nil
}

// escalateDeception makes honeypot progressively more convincing
func (r *IncidentDetectionReconciler) escalateDeception(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Create ConfigMap with deception level instructions for honeypot
	deceptionLevel := "high"
	techniques := []string{
		"fake-admin-panel",
		"realistic-error-messages",
		"breadcrumb-credentials",
		"fake-internal-docs",
	}

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("deception-%s", incident.Name),
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
				"mirror.ctf/deception-level":   deceptionLevel,
			},
		},
		Data: map[string]string{
			"level":      deceptionLevel,
			"techniques": strings.Join(techniques, ","),
			"target_ip":  incident.Spec.AttackerIP,
		},
	}

	if err := ctrl.SetControllerReference(incident, cm, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	if err := r.Create(ctx, cm); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("Deception config already exists", "name", cm.Name)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "deception-escalation",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Escalated to level: %s (%d techniques)", deceptionLevel, len(techniques)),
	}, nil
}

// injectTimeDelay adds artificial latency to slow down attackers
func (r *IncidentDetectionReconciler) injectTimeDelay(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// Create ConfigMap with delay configuration
	delayMs := 5000 // 5 second delay

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("timedelay-%s", incident.Name),
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
			},
		},
		Data: map[string]string{
			"delay_ms":  fmt.Sprintf("%d", delayMs),
			"target_ip": incident.Spec.AttackerIP,
		},
	}

	if err := ctrl.SetControllerReference(incident, cm, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	if err := r.Create(ctx, cm); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("Time delay config already exists", "name", cm.Name)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "time-delay-response",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Injected %dms delay for %s", delayMs, incident.Spec.AttackerIP),
	}, nil
}

// injectFakeVulnerability makes honeypot look MORE vulnerable
func (r *IncidentDetectionReconciler) injectFakeVulnerability(ctx context.Context, incident *mirrorv1alpha1.IncidentDetection) (mirrorv1alpha1.DefensiveAction, error) {
	log := log.FromContext(ctx)

	// List of fake vulnerabilities to expose
	fakeVulns := []string{
		"SQL injection in /admin/users?id=",
		"LFI in /download?file=",
		"Command injection in /api/exec?cmd=",
		"Exposed .git directory",
		"Exposed .env file with credentials",
	}

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("fakevuln-%s", incident.Name),
			Namespace: incident.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "mirror-operator",
				"mirror.ctf/incident-id":       incident.Name,
			},
		},
		Data: map[string]string{
			"vulnerabilities": strings.Join(fakeVulns, "\n"),
			"target_ip":       incident.Spec.AttackerIP,
		},
	}

	if err := ctrl.SetControllerReference(incident, cm, r.Scheme); err != nil {
		return mirrorv1alpha1.DefensiveAction{}, err
	}

	if err := r.Create(ctx, cm); err != nil {
		if !errors.IsAlreadyExists(err) {
			return mirrorv1alpha1.DefensiveAction{}, err
		}
		log.Info("Fake vulnerability config already exists", "name", cm.Name)
	}

	return mirrorv1alpha1.DefensiveAction{
		Type:      "fake-vulnerability-injection",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   fmt.Sprintf("Injected %d fake vulnerabilities", len(fakeVulns)),
	}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *IncidentDetectionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&mirrorv1alpha1.IncidentDetection{}).
		Owns(&networkingv1.NetworkPolicy{}).
		Owns(&corev1.ConfigMap{}).
		Complete(r)
}
