#!/usr/bin/env bash
# Scale midas Batch pool to zero after jobs complete (stops VM charges).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/midas_config.env"

az batch account login --name "$MIDAS_AZURE_BATCH" --resource-group "$MIDAS_AZURE_RG"
az batch pool resize --pool-id "$MIDAS_AZURE_POOL" \
  --target-dedicated-nodes 0 --target-low-priority-nodes 0 \
  --account-name "$MIDAS_AZURE_BATCH"
echo "Pool $MIDAS_AZURE_POOL scaled to 0 nodes."
