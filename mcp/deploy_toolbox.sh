#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project)"
REGION=us-central1

echo "Creating service account sq7-toolbox-sa if not existing..."
gcloud iam service-accounts create sq7-toolbox-sa --display-name "MCP Toolbox" 2>/dev/null || true
SA="sq7-toolbox-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Binding IAM roles to ${SA}..."
for ROLE in roles/bigquery.dataViewer roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="$ROLE" \
    --condition=None
done

echo "Setting up secret sq7-toolbox-tools..."
gcloud secrets create sq7-toolbox-tools --data-file=mcp/tools.yaml 2>/dev/null || \
  gcloud secrets versions add sq7-toolbox-tools --data-file=mcp/tools.yaml

gcloud secrets add-iam-policy-binding sq7-toolbox-tools \
  --member="serviceAccount:$SA" \
  --role=roles/secretmanager.secretAccessor

echo "Deploying Cloud Run service sq7-mcp-toolbox..."
gcloud run deploy sq7-mcp-toolbox \
  --image=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --region="$REGION" \
  --service-account="$SA" \
  --set-secrets="/app/tools.yaml=sq7-toolbox-tools:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --args="--tools-file=/app/tools.yaml,--address=0.0.0.0,--port=8080" \
  --min-instances=1 \
  --no-allow-unauthenticated
