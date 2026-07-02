{{- define "kubepilot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "kubepilot.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "kubepilot.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
