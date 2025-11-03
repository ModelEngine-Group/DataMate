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
Define the pulsar autorecovery service
*/}}
{{- define "pulsar.autorecovery.service" -}}
{{ template "pulsar.fullname" . }}-{{ .Values.autorecovery.component }}
{{- end }}

{{/*
Define the autorecovery hostname
*/}}
{{- define "pulsar.autorecovery.hostname" -}}
${HOSTNAME}.{{ template "pulsar.autorecovery.service" . }}.{{ template "pulsar.namespace" . }}.svc.{{ .Values.clusterDomain }}
{{- end -}}

{{/*
Define autorecovery zookeeper client tls settings
*/}}
{{- define "pulsar.autorecovery.zookeeper.tls.settings" -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled }}
/pulsar/keytool/keytool.sh autorecovery {{ template "pulsar.autorecovery.hostname" . }} true;
{{- end }}
{{- end }}

{{/*
Define autorecovery tls certs mounts
*/}}
{{- define "pulsar.autorecovery.certs.volumeMounts" -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled }}
- name: autorecovery-certs
  mountPath: "/pulsar/certs/autorecovery"
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
Define autorecovery tls certs volumes
*/}}
{{- define "pulsar.autorecovery.certs.volumes" -}}
{{- if and .Values.tls.enabled .Values.tls.zookeeper.enabled }}
- name: autorecovery-certs
  secret:
    secretName: "{{ .Release.Name }}-{{ .Values.tls.autorecovery.cert_name }}"
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

{{/*
Define autorecovery init container : verify cluster id
*/}}
{{- define "pulsar.autorecovery.init.verify_cluster_id" -}}
bin/apply-config-from-env.py conf/bookkeeper.conf;
{{- include "pulsar.autorecovery.zookeeper.tls.settings" . -}}
until bin/bookkeeper shell whatisinstanceid; do
  sleep 3;
done;
{{- end }}
