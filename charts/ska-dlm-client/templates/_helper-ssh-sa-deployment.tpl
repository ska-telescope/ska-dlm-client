{{/*
ssh storage access deployment
*/}}
{{- define "ska-dlm-client.ssh-storage-access.deployment" }}
apiVersion: apps/v1
kind: Deployment
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
                  name: {{ .deployment.secret.pub_name }}
                  key: {{ .deployment.secret.pub_name }}
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
