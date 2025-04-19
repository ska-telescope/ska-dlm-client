{{/*
ssh storage access service
*/}}
{{- define "ska-dlm-client.readiness-probe" }}
- "--readiness-probe-file"
- {{ .Values.ska_dlm_client.readiness_file }}
readinessProbe:
  exec:
    command:
      - cat
      - /tmp/dlm-client-ready
{{- end }}
