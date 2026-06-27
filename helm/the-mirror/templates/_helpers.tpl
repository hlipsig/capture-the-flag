{{/*
Expand the name of the chart.
*/}}
{{- define "the-mirror.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "the-mirror.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "the-mirror.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "the-mirror.labels" -}}
helm.sh/chart: {{ include "the-mirror.chart" . }}
{{ include "the-mirror.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.labels }}
{{ toYaml . }}
{{- end }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "the-mirror.selectorLabels" -}}
app.kubernetes.io/name: {{ include "the-mirror.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "the-mirror.serviceAccountName" -}}
{{- if .Values.rbac.serviceAccount.create }}
{{- default (include "the-mirror.fullname" .) .Values.rbac.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.rbac.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate namespace
*/}}
{{- define "the-mirror.namespace" -}}
{{- default .Release.Namespace .Values.global.namespace }}
{{- end }}

{{/*
Generate image registry prefix
*/}}
{{- define "the-mirror.imageRegistry" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/" .Values.global.imageRegistry }}
{{- end }}
{{- end }}

{{/*
Agent image
*/}}
{{- define "the-mirror.agent.image" -}}
{{- printf "%s%s:%s" (include "the-mirror.imageRegistry" .) .Values.agent.image.repository .Values.agent.image.tag }}
{{- end }}

{{/*
LLM server image
*/}}
{{- define "the-mirror.llm.image" -}}
{{- printf "%s%s:%s" (include "the-mirror.imageRegistry" .) .Values.llm.image.repository .Values.llm.image.tag }}
{{- end }}

{{/*
Postgres image
*/}}
{{- define "the-mirror.postgres.image" -}}
{{- printf "%s:%s" .Values.postgres.image.repository .Values.postgres.image.tag }}
{{- end }}

{{/*
Redis image
*/}}
{{- define "the-mirror.redis.image" -}}
{{- printf "%s:%s" .Values.redis.image.repository .Values.redis.image.tag }}
{{- end }}

{{/*
Honeypot image
*/}}
{{- define "the-mirror.honeypot.image" -}}
{{- printf "%s:%s" .Values.honeypot.image.repository .Values.honeypot.image.tag }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "the-mirror.databaseUrl" -}}
{{- if .Values.agent.secrets.databaseUrl }}
{{- .Values.agent.secrets.databaseUrl }}
{{- else }}
{{- printf "postgresql://%s:%s@postgres.%s.svc.cluster.local:5432/%s" .Values.postgres.credentials.user .Values.postgres.credentials.password (include "the-mirror.namespace" .) .Values.postgres.credentials.database }}
{{- end }}
{{- end }}

{{/*
LLM server URL
*/}}
{{- define "the-mirror.llmServerUrl" -}}
{{- printf "http://llm-server.%s.svc.cluster.local:8000" (include "the-mirror.namespace" .) }}
{{- end }}

{{/*
Redis URL
*/}}
{{- define "the-mirror.redisUrl" -}}
{{- printf "redis://redis.%s.svc.cluster.local:6379" (include "the-mirror.namespace" .) }}
{{- end }}

{{/*
Common annotations
*/}}
{{- define "the-mirror.annotations" -}}
{{- with .Values.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Security context for pods
*/}}
{{- define "the-mirror.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Container security context
*/}}
{{- define "the-mirror.containerSecurityContext" -}}
allowPrivilegeEscalation: false
runAsNonRoot: true
capabilities:
  drop:
    - ALL
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Mirror operator image
*/}}
{{- define "the-mirror.operator.image" -}}
{{- if .Values.operator.image.repository }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.operator.image.repository (.Values.operator.image.tag | default "latest") }}
{{- else }}
{{- printf "%s/cyber-riposte/mirror-operator:%s" .Values.global.imageRegistry (.Values.operator.image.tag | default "latest") }}
{{- end }}
{{- end }}
