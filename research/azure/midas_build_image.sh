#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/midas_config.env"

echo "=== Building midas-credence Docker image (ACR cloud build — no local Docker) ==="
az acr build --registry "$MIDAS_AZURE_ACR" \
  --image midas-credence:latest \
  --file "$SCRIPT_DIR/Dockerfile" \
  "$RESEARCH"
echo "Built $MIDAS_AZURE_IMAGE"
