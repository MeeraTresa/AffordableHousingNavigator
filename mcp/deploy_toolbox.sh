#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project)"
REGION=us-central1
SERVICE_NAME=sq7-mcp-toolbox
SA="530357188502-compute@developer.gserviceaccount.com"

echo "Deploying Cloud Run service ${SERVICE_NAME} in ${REGION} using project service account..."
gcloud run deploy "$SERVICE_NAME" \
  --source=mcp \
  --region="$REGION" \
  --service-account="$SA" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --args="--tools-file=/app/tools.yaml,--address=0.0.0.0,--port=8080" \
  --min-instances=1 \
  --no-allow-unauthenticated

URL="$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")"
echo "Deployed successfully to ${URL}"
