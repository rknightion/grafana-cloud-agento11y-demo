{{/*
Prefix for every object this chart creates. Deliberately independent of .Release.Name: Terraform
sets nameOverride to var.regulatory_name and every other lane's frozen names (IAM, Pod Identity, Secrets)
are built from that same var.regulatory_name, not from whatever Helm release name the installer picks.
*/}}
{{- define "regulatory.prefix" -}}
{{- .Values.nameOverride | default .Chart.Name -}}
{{- end -}}

{{/*
"<prefix>-<suffix>" object name, e.g. regulatory-orchestrator.
*/}}
{{- define "regulatory.objectName" -}}
{{- printf "%s-%s" (include "regulatory.prefix" .context) .suffix -}}
{{- end -}}

{{/*
Full image reference for one of this repo's images: "<registry>/<namePrefix><name>:<tag>".
Call as (include "regulatory.image" (dict "root" $root "name" "regulatory")).
*/}}
{{- define "regulatory.image" -}}
{{- $ref := printf "%s/%s%s:%s" .root.Values.images.registry .root.Values.images.namePrefix .name .root.Values.images.tag -}}
{{- with (get (.root.Values.images.digests | default dict) .name) -}}
{{- $ref = printf "%s@%s" $ref . -}}
{{- end -}}
{{- $ref -}}
{{- end -}}

{{/*
Common labels for every object.
*/}}
{{- define "regulatory.labels" -}}
app.kubernetes.io/part-of: {{ include "regulatory.prefix" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/*
Selector labels for a named component (Deployment/Service/CronJob must agree on these).
*/}}
{{- define "regulatory.selectorLabels" -}}
app.kubernetes.io/name: {{ . }}
{{- end -}}

{{/*
Full OTEL_RESOURCE_ATTRIBUTES value for a given service name.
*/}}
{{- define "regulatory.resourceAttributes" -}}
{{- printf "service.namespace=%s,deployment.environment=%s" .root.Values.namespace .root.Values.deploymentEnvironment -}}
{{- end -}}

{{/*
AGENTO11Y_CONTENT_CAPTURE_MODE value from the contentCapture bool.
*/}}
{{- define "regulatory.contentCaptureMode" -}}
{{- if .Values.contentCapture -}}full{{- else -}}none{{- end -}}
{{- end -}}
