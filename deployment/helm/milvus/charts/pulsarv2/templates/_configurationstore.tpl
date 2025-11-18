{{/*
Define configuration store endpoint
*/}}
{{- define "pulsar.configurationStore.service" -}}
{{- if .Values.pulsar_metadata.configurationStore }}
{{- .Values.pulsar_metadata.configurationStore }}
{{- else -}}
{{ template "pulsar.zookeeper.service" . }}
{{- end -}}
{{- end -}}

{{/*
Define configuration store connection string
*/}}
{{- define "pulsar.configurationStore.connect" -}}
{{- if .Values.pulsar_metadata.configurationStore }}
{{- template "pulsar.configurationStore.service" . }}:{{ .Values.pulsar_metadata.configurationStorePort }}
{{- end -}}
{{- end -}}

