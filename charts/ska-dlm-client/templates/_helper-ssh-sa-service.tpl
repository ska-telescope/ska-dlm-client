{{/*
ssh storage access service
*/}}
{{- define "ska-dlm-client.ssh-storage-access.service" }}
apiVersion: v1
kind: Service
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
