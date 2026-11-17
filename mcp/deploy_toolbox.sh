#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="$(gcloud config get-value project)"; REGION=us-central1
gcloud iam service-accounts create toolbox-sa --display-name "MCP Toolbox" || true
SA="toolbox-sa@${PROJECT_ID}.iam.gserviceaccount.com"
for ROLE in roles/bigquery.dataViewer roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA" --role="$ROLE" --condition=None
done
gcloud secrets create toolbox-tools --data-file=mcp/tools.yaml 2>/dev/null || \
  gcloud secrets versions add toolbox-tools --data-file=mcp/tools.yaml
gcloud secrets add-iam-policy-binding toolbox-tools --member="serviceAccount:$SA" --role=roles/secretmanager.secretAccessor

gcloud run deploy mcp-toolbox \
  --image=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --region="$REGION" --service-account="$SA" \
  --set-secrets="/app/tools.yaml=toolbox-tools:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --args="--tools-file=/app/tools.yaml,--address=0.0.0.0,--port=8080" \
  --min-instances=1 --no-allow-unauthenticated
