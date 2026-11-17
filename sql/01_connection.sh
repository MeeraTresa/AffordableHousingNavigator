#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="$(gcloud config get-value project)"
bq mk --connection --location=US --project_id="${PROJECT_ID}" \
  --connection_type=CLOUD_RESOURCE a4i-vertex || echo "connection exists"

SA="$(bq show --format=json --connection "${PROJECT_ID}.us.a4i-vertex" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["cloudResource"]["serviceAccountId"])')"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA}" --role="roles/aiplatform.user" --condition=None
echo "Waiting 60s for IAM propagation..."; sleep 60
