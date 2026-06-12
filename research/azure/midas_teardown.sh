#!/usr/bin/env bash
# Delete ALL midas-credence Azure resources. Destructive — removes RG and everything in it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/midas_config.env"

echo "WARNING: This deletes resource group $MIDAS_AZURE_RG and ALL resources inside."
echo "Resources: storage $MIDAS_AZURE_STORAGE, acr $MIDAS_AZURE_ACR, batch $MIDAS_AZURE_BATCH"
read -r -p "Type 'midas-teardown' to confirm: " confirm
if [[ "$confirm" != "midas-teardown" ]]; then
  echo "Aborted."
  exit 1
fi

# Scale pool to zero first (ignore errors if pool missing)
az batch pool resize --pool-id "$MIDAS_AZURE_POOL" --target-dedicated-nodes 0 \
  --target-low-priority-nodes 0 --account-name "$MIDAS_AZURE_BATCH" 2>/dev/null || true

az group delete --name "$MIDAS_AZURE_RG" --yes --no-wait
echo "Delete initiated for $MIDAS_AZURE_RG (async). Check: az group show -n $MIDAS_AZURE_RG"
