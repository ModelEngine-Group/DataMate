{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "ray-cluster.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ray-cluster.fullname" -}}
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
{{- define "ray-cluster.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "ray-cluster.labels" -}}
helm.sh/chart: {{ include "ray-cluster.chart" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "ray-cluster.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "ray-cluster.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Name of image
*/}}
{{- define "ray-cluster.image" -}}
{{- $name := default .Values.image.repository .Values.global.image.runtime.name }}
{{- $tag := default .Values.image.tag .Values.global.image.runtime.tag }}
{{- if .Values.global.image.repository }}
{{- .Values.global.image.repository | trimSuffix "/" }}/{{ $name }}:{{ $tag }}
{{- else }}
{{- $name }}:{{ $tag }}
{{- end }}
{{- end }}

{{/*
Name of sidecar image
*/}}
{{- define "ray-cluster-sidecar.image" -}}
{{- $name := default (printf "%s:%s" .Values.image.repository .Values.image.tag) .Values.head.sidecarContainers.image }}
{{- if .Values.global.image.repository }}
{{- .Values.global.image.repository | trimSuffix "/" }}/{{ $name }}
{{- else }}
{{- $name }}
{{- end }}
{{- end }}