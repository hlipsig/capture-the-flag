package controllers

import (
	"context"
	"database/sql"
	"fmt"
	"os"
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

	// High confidence detections get immediate blocking
	if incident.Spec.Confidence >= 0.90 {
		actions = append(actions, "networkpolicy-block")
	}

	// Always run OSINT for context
	actions = append(actions, "osint-lookup")

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
	// In production, this would call Shodan, VirusTotal, etc.
	// For now, just log and mark as success

	log := log.FromContext(ctx)
	log.Info("OSINT lookup", "ip", incident.Spec.AttackerIP)

	// Placeholder - in real implementation, would populate incident.Status.OSINTData

	return mirrorv1alpha1.DefensiveAction{
		Type:      "osint-lookup",
		Timestamp: metav1.Now(),
		Success:   true,
		Details:   "OSINT data collected (placeholder)",
	}, nil
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

// SetupWithManager sets up the controller with the Manager.
func (r *IncidentDetectionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&mirrorv1alpha1.IncidentDetection{}).
		Owns(&networkingv1.NetworkPolicy{}).
		Complete(r)
}
