#!/bin/sh
# Auto-import DROPIFY n8n workflows on first start.
# Waits for n8n to be ready, then imports all dropify-*.json files.

set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"
WORKFLOW_DIR="/home/node/.n8n/workflows"

echo "[n8n-setup] Waiting for n8n to be ready..."
until curl -sf "${N8N_URL}/healthz" > /dev/null 2>&1; do
  sleep 2
done
echo "[n8n-setup] n8n is ready."

# Import workflows if not already present
for f in /workflows/dropify-*.json; do
  [ -f "$f" ] || continue
  NAME=$(grep -o '"name": *"[^"]*"' "$f" | head -1 | cut -d'"' -f4)
  echo "[n8n-setup] Importing: ${NAME} (${f})"

  AUTH_HEADER=""
  if [ -n "$N8N_API_KEY" ]; then
    AUTH_HEADER="-H X-N8N-API-KEY:${N8N_API_KEY}"
  fi

  # Try to import via n8n REST API
  RESP=$(curl -sf -X POST "${N8N_URL}/api/v1/workflows" \
    -H "Content-Type: application/json" \
    ${AUTH_HEADER} \
    -d @"$f" 2>&1) || true

  if echo "$RESP" | grep -q '"id"'; then
    WF_ID=$(echo "$RESP" | grep -o '"id": *"[^"]*"' | head -1 | cut -d'"' -f4)
    # Activate the workflow
    curl -sf -X PATCH "${N8N_URL}/api/v1/workflows/${WF_ID}" \
      -H "Content-Type: application/json" \
      ${AUTH_HEADER} \
      -d '{"active":true}' > /dev/null 2>&1 || true
    echo "[n8n-setup] Activated: ${NAME} (id=${WF_ID})"
  else
    echo "[n8n-setup] Skipped (already exists or import failed): ${NAME}"
  fi
done

echo "[n8n-setup] Done."
