{{/*
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
*/}}

{{/*
Define the pulsar brroker service
*/}}
{{- define "pulsar.broker.service" -}}
{{ template "pulsar.fullname" . }}-{{ .Values.broker.component }}
{{- end }}

{{/*
Define the hostname
*/}}
{{- define "pulsar.broker.hostname" -}}
${HOSTNAME}.{{ template "pulsar.broker.service" . }}.{{ template "pulsar.namespace" . }}.svc.{{ .Values.clusterDomain }}
{{- end -}}

{{/*
Define the broker znode
*/}}
{{- define "pulsar.broker.znode" -}}
{{ .Values.metadataPrefix }}/loadbalance/brokers/{{ template "pulsar.broker.hostname" . }}:{{ .Values.broker.ports.http }}
{{- end }}

{{/*
Define broker zookeeper client tls settings
*/}}
{{- define "pulsar.broker.zookeeper.tls.settings" -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled }}
/pulsar/keytool/keytool.sh broker {{ template "pulsar.broker.hostname" . }} true;
{{- end }}
{{- end }}

{{/*
Define broker tls certs mounts
*/}}
{{- define "pulsar.broker.certs.volumeMounts" -}}
{{- if and .Values.tls.enabled (or .Values.tls.broker.enabled (or .Values.tls.bookie.enabled .Values.tls.zookeeper.enabled)) }}
- name: broker-certs
  mountPath: "/pulsar/certs/broker"
  readOnly: true
- name: ca
  mountPath: "/pulsar/certs/ca"
  readOnly: true
{{- if .Values.tls.zookeeper.enabled }}
- name: keytool
  mountPath: "/pulsar/keytool/keytool.sh"
  subPath: keytool.sh
{{- end }}
{{- end }}
{{- end }}

{{/*
Define broker tls certs volumes
*/}}
{{- define "pulsar.broker.certs.volumes" -}}
{{- if and .Values.tls.enabled (or .Values.tls.broker.enabled (or .Values.tls.bookie.enabled .Values.tls.zookeeper.enabled)) }}
- name: broker-certs
  secret:
    secretName: "{{ .Release.Name }}-{{ .Values.tls.broker.cert_name }}"
    items:
    - key: tls.crt
      path: tls.crt
    - key: tls.key
      path: tls.key
- name: ca
  secret:
    secretName: "{{ .Release.Name }}-{{ .Values.tls.ca_suffix }}"
    items:
    - key: ca.crt
      path: ca.crt
{{- if .Values.tls.zookeeper.enabled }}
- name: keytool
  configMap:
    name: "{{ template "pulsar.fullname" . }}-keytool-configmap"
    defaultMode: 0755
{{- end }}
{{- end }}
{{- end }}
