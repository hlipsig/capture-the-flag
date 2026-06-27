package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// IncidentDetectionSpec defines the desired state of IncidentDetection
// Compatible with CloudEvents specification
type IncidentDetectionSpec struct {
	// AttackerIP is the source IP address of the attack
	AttackerIP string `json:"attackerIP"`

	// DetectionSignature identifies the type of attack detected
	// Examples: "ET SCAN Nikto Web Scanner", "SQL Injection Attempt"
	DetectionSignature string `json:"detectionSignature"`

	// Confidence score of the detection (0.0 - 1.0)
	Confidence float64 `json:"confidence"`

	// Source identifies which component detected the threat
	// Examples: "production-portal", "honeypot", "suricata"
	Source string `json:"source"`

	// CloudEvent contains the full CloudEvents-compliant event data
	// +optional
	CloudEvent *CloudEventData `json:"cloudEvent,omitempty"`

	// Evidence contains supporting data for the detection
	// +optional
	Evidence map[string]string `json:"evidence,omitempty"`
}

// CloudEventData represents CloudEvents v1.0 compatible event data
type CloudEventData struct {
	// SpecVersion of CloudEvents (1.0)
	SpecVersion string `json:"specversion"`

	// Type of event (e.g., "com.mirror.detection.scanner")
	Type string `json:"type"`

	// Source of the event
	Source string `json:"source"`

	// ID unique to this event
	ID string `json:"id"`

	// Time when the event occurred
	Time metav1.Time `json:"time"`

	// DataContentType of the data (e.g., "application/json")
	// +optional
	DataContentType string `json:"datacontenttype,omitempty"`

	// Data contains the event payload
	// +optional
	Data map[string]interface{} `json:"data,omitempty"`
}

// DefensiveAction represents an action taken in response to the incident
type DefensiveAction struct {
	// Type of action (e.g., "networkpolicy-block", "osint-lookup", "redirect")
	Type string `json:"type"`

	// Timestamp when action was executed
	Timestamp metav1.Time `json:"timestamp"`

	// Success indicates if the action completed successfully
	Success bool `json:"success"`

	// Details provides additional information about the action
	// +optional
	Details string `json:"details,omitempty"`

	// ResourceRef points to the K8s resource created (e.g., NetworkPolicy)
	// +optional
	ResourceRef *ResourceReference `json:"resourceRef,omitempty"`
}

// ResourceReference points to a Kubernetes resource
type ResourceReference struct {
	APIVersion string `json:"apiVersion"`
	Kind       string `json:"kind"`
	Name       string `json:"name"`
	Namespace  string `json:"namespace"`
}

// IncidentDetectionStatus defines the observed state of IncidentDetection
type IncidentDetectionStatus struct {
	// Phase represents the current state of the incident
	// Possible values: Detected, Analyzing, Responding, Resolved
	Phase string `json:"phase,omitempty"`

	// ActionsExecuted lists all defensive actions taken
	// +optional
	ActionsExecuted []DefensiveAction `json:"actionsExecuted,omitempty"`

	// Message provides human-readable status information
	// +optional
	Message string `json:"message,omitempty"`

	// LastUpdated timestamp
	// +optional
	LastUpdated metav1.Time `json:"lastUpdated,omitempty"`

	// OSINTData contains enrichment data about the attacker
	// +optional
	OSINTData map[string]interface{} `json:"osintData,omitempty"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status
//+kubebuilder:resource:shortName=incident;incidents
//+kubebuilder:printcolumn:name="AttackerIP",type=string,JSONPath=`.spec.attackerIP`
//+kubebuilder:printcolumn:name="Signature",type=string,JSONPath=`.spec.detectionSignature`
//+kubebuilder:printcolumn:name="Confidence",type=string,JSONPath=`.spec.confidence`
//+kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
//+kubebuilder:printcolumn:name="Age",type="date",JSONPath=".metadata.creationTimestamp"

// IncidentDetection is the Schema for the incidentdetections API
type IncidentDetection struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   IncidentDetectionSpec   `json:"spec,omitempty"`
	Status IncidentDetectionStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// IncidentDetectionList contains a list of IncidentDetection
type IncidentDetectionList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []IncidentDetection `json:"items"`
}

func init() {
	SchemeBuilder.Register(&IncidentDetection{}, &IncidentDetectionList{})
}
