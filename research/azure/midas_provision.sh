#!/usr/bin/env bash
# Provision midas-* Credence Azure lab (idempotent where possible).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=midas_config.env
source "$SCRIPT_DIR/midas_config.env"

echo "=== midas-credence Azure provision (RG=$MIDAS_AZURE_RG) ==="

az group create --name "$MIDAS_AZURE_RG" --location "$MIDAS_AZURE_LOCATION" \
  --tags project=midas-credence managed-by=midas-provision >/dev/null

az storage account create --name "$MIDAS_AZURE_STORAGE" --resource-group "$MIDAS_AZURE_RG" \
  --location "$MIDAS_AZURE_LOCATION" --sku Standard_LRS \
  --tags project=midas-credence managed-by=midas-provision 2>/dev/null || true

az storage container create --account-name "$MIDAS_AZURE_STORAGE" --name midas-results \
  --auth-mode login 2>/dev/null || true

az acr create --name "$MIDAS_AZURE_ACR" --resource-group "$MIDAS_AZURE_RG" \
  --location "$MIDAS_AZURE_LOCATION" --sku Basic \
  --tags project=midas-credence managed-by=midas-provision 2>/dev/null || true

az acr update --name "$MIDAS_AZURE_ACR" --admin-enabled true >/dev/null

az provider register --namespace Microsoft.Batch --wait 2>/dev/null || true

az batch account create --name "$MIDAS_AZURE_BATCH" --resource-group "$MIDAS_AZURE_RG" \
  --location "$MIDAS_AZURE_LOCATION" --storage-account "$MIDAS_AZURE_STORAGE" \
  --tags project=midas-credence managed-by=midas-provision 2>/dev/null || true

echo "Provisioned. Run midas_build_image.sh then midas_create_pool.sh"
