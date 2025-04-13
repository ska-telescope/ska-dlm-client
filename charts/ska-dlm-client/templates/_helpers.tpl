{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "ska-dlm-client.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ska-dlm-client.fullname" -}}
{{- if not ( eq .Values.fullnameOverride "" ) -}}
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
Directory watcher labels
*/}}
{{- define "ska-dlm-client.directory-watcher.labels" }}
{{- include "ska-dlm-client.labels" . }}
component: {{ .Values.directory_watcher.component }}
subsystem: {{ .Values.directory_watcher.subsystem }}
intent: production
{{- end }}

{{/*
Kafka watcher labels
*/}}
{{- define "ska-dlm-client.kafka-watcher.labels" }}
{{- include "ska-dlm-client.labels" . }}
component: {{ .Values.kafka_watcher.component }}
subsystem: {{ .Values.kafka_watcher.subsystem }}
intent: production
{{- end }}

{{/*
Storage location labels
*/}}
{{- define "ska-dlm-client.setup-storage-location.labels" }}
{{- include "ska-dlm-client.labels" . }}
{{- end }}

{{/*
ssh storage access
*/}}
{{- define "ska-dlm-client.ssh-storage-access.labels" }}
{{- include "ska-dlm-client.labels" . }}
component: ssh-storage-access
subsystem: {{ .Values.ssh_storage_access.subsystem }}
intent: production
{{- end }}

{{- define "ska-dlm-client.ssh-storage-access.service" }}
metadata:
  name: {{ include "ska-dlm-client.fullname" .root }}-{{ .svc_name }}
  namespace: {{ .root.Release.Namespace }}
  labels:
    {{ include "ska-dlm-client.ssh-storage-access.labels" .root | indent 4 }}
spec:
  type: ClusterIP
  ports:
    - name: tcp-pst-ssh
      port: 22
      targetPort: 2222
      protocol: TCP
  selector:
    component: {{ .root.Values.ssh_storage_access.component }}
    subsystem: {{ .root.Values.ssh_storage_access.subsystem }}
{{- end }}

{{/*
ssh storage access deployment
*/}}
{{- define "ska-dlm-client.ssh-storage-access.deployment" }}
metadata:
  name: {{ include "ska-dlm-client.fullname" .root }}-{{ .deployment.deployment_name }}
  namespace: {{ .root.Release.Namespace }}
  labels:
    {{- include "ska-dlm-client.ssh-storage-access.labels" .root | indent 4 }}
spec:
  replicas: {{ .root.Values.ssh_storage_access.replicas }}
  selector:
    matchLabels:
      component: {{ .root.Values.ssh_storage_access.component }}
      subsystem: {{ .root.Values.ssh_storage_access.subsystem }}
  template:
    metadata:
      labels:
        {{- include "ska-dlm-client.ssh-storage-access.labels" .root | indent 8 }}
    spec:
      {{- if .root.Values.ska_dlm_client.securityContext }}
      securityContext:
        {{- .root.Values.ska_dlm_client.securityContext | toYaml | nindent 8 }}
      {{- end }}
      containers:
        - name: {{ .deployment.deployment_name }}
          image: linuxserver/openssh-server
          ports:
            - containerPort: 2222
          env:
            - name: PUID
              value: "{{ .root.Values.ssh_storage_access.ssh_uid }}"
            - name: PGID
              value: "{{ .root.Values.ssh_storage_access.ssh_gid }}"
            - name: USER_NAME
              value: "{{ .root.Values.ssh_storage_access.ssh_user_name }}"
            - name: PUBLIC_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .deployment.secrets.pub_name }}
                  key: {{ .deployment.secrets.pub_name }}
          volumeMounts:
            - name: ssh-config
              mountPath: /config
            - name: data-product-storage
              mountPath: /data
          {{- if eq $.deployment.pvc.read_only true }}
              readOnly: true
          {{- end }}
      volumes:
        - name: ssh-config
          emptyDir: {}
        - name: data-product-storage
          persistentVolumeClaim:
            claimName: "{{ $.deployment.pvc.name }}"
{{- end -}}
