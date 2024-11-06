{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "ska-dlm-client.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ska-dlm.fullname" -}}
{{- "ska-dlm" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ska-dlm-client.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ska-dlm-client.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
see https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
*/}}
{{- define "ska-dlm-client.labels" }}
{{- if .Values.global.labels}}
app.kubernetes.io/name: {{ coalesce .Values.global.labels.app "ska-dlm-client.name" }}
{{- else }}
app.kubernetes.io/name: {{ include "ska-dlm-client.name" . }}
{{- end }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ include "ska-dlm-client.chart" . }}
system: {{ .Values.system }}
{{- end }}

{{/*
Ingest labels
*/}}
{{- define "ska-dlm-client.directory-watcher.labels" }}
{{- include "ska-dlm-client.labels" . }}
component: {{ .Values.directory_watcher.component }}
subsystem: {{ .Values.directory_watcher.subsystem }}
intent: production
{{- end }}
