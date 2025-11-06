{{/*
Define the pulsar zookeeper
*/}}
{{- define "pulsar.zookeeper.service" -}}
{{ template "pulsar.fullname" . }}-{{ .Values.zookeeper.component }}
{{- end }}

{{/*
Define the pulsar zookeeper
*/}}
{{- define "pulsar.zookeeper.connect" -}}
{{$zk:=.Values.pulsar_metadata.userProvidedZookeepers}}
{{- if and (not .Values.components.zookeeper) $zk }}
{{- $zk -}}
{{ else }}
{{- if not (and .Values.tls.enabled .Values.tls.zookeeper.enabled) -}}
{{ template "pulsar.zookeeper.service" . }}:{{ .Values.zookeeper.ports.client }}
{{- end -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled -}}
{{ template "pulsar.zookeeper.service" . }}:{{ .Values.zookeeper.ports.clientTls }}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Define the zookeeper hostname
*/}}
{{- define "pulsar.zookeeper.hostname" -}}
${HOSTNAME}.{{ template "pulsar.zookeeper.service" . }}.{{ template "pulsar.namespace" . }}.svc.{{ .Values.clusterDomain }}
{{- end -}}

{{/*
Define zookeeper tls settings
*/}}
{{- define "pulsar.zookeeper.tls.settings" -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled }}
/pulsar/keytool/keytool.sh zookeeper {{ template "pulsar.zookeeper.hostname" . }} false;
{{- end }}
{{- end }}
