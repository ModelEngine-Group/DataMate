{{/*
Expand the name of the chart.
*/}}
{{- define "runtime.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "runtime.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "runtime.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Common labels
*/}}
{{- define "runtime.labels" -}}
helm.sh/chart: {{ include "runtime.chart" . }}
app: {{ .Release.Name }}
{{ include "runtime.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "runtime.selectorLabels" -}}
app.kubernetes.io/name: {{ include "runtime.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "runtime.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "runtime.fullname" .) .Values.serviceAccount.name -}}
{{- else }}
{{- default "default" .Values.serviceAccount.name -}}
{{- end }}
{{- end }}

{{/*
Name of image
*/}}
{{- define "runtime.image" -}}
{{- $name := default .Values.image.repository .Values.global.image.runtime.name }}
{{- $tag := default .Values.image.tag .Values.global.image.runtime.tag }}
{{- if .Values.global.image.repository }}
{{- .Values.global.image.repository | trimSuffix "/" }}/{{ $name }}:{{ $tag }}
{{- else }}
{{- $name }}:{{ $tag }}
{{- end }}
{{- end }}
