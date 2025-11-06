{{/*
Expand the name of the chart.
*/}}
{{- define "backend-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "backend-python.fullname" -}}
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
{{- define "backend-python.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Common labels
*/}}
{{- define "backend-python.labels" -}}
helm.sh/chart: {{ include "backend-python.chart" . }}
{{ include "backend-python.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "backend-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "backend-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "backend-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "backend-python.fullname" .) .Values.serviceAccount.name -}}
{{- else }}
{{- default "default" .Values.serviceAccount.name -}}
{{- end }}
{{- end }}

{{/*
Name of image
*/}}
{{- define "backend-python.image" -}}
{{- $name := default .Values.image.repository .Values.global.image.backendPython.name }}
{{- $tag := default .Values.image.tag .Values.global.image.backendPython.tag }}
{{- if .Values.global.image.repository }}
{{- .Values.global.image.repository | trimSuffix "/" }}/{{ $name }}:{{ $tag }}
{{- else }}
{{- $name }}:{{ $tag }}
{{- end }}
{{- end }}
