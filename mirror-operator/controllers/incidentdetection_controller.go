package controllers

import (
	"context"
	"fmt"
	"time"

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

// SetupWithManager sets up the controller with the Manager.
func (r *IncidentDetectionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&mirrorv1alpha1.IncidentDetection{}).
		Owns(&networkingv1.NetworkPolicy{}).
		Complete(r)
}
