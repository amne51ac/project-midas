#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/midas_config.env"

ACR_USER=$(az acr credential show --name "$MIDAS_AZURE_ACR" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "$MIDAS_AZURE_ACR" --query "passwords[0].value" -o tsv)

az batch account login --name "$MIDAS_AZURE_BATCH" --resource-group "$MIDAS_AZURE_RG"

az batch pool delete --pool-id "$MIDAS_AZURE_POOL" --account-name "$MIDAS_AZURE_BATCH" --yes 2>/dev/null || true
sleep 3

POOL_JSON=$(mktemp)
trap 'rm -f "$POOL_JSON"' EXIT

export MIDAS_AZURE_POOL MIDAS_AZURE_IMAGE MIDAS_AZURE_ACR ACR_USER ACR_PASS POOL_JSON
python3 <<'PY'
import json, os
pool = {
    "id": os.environ["MIDAS_AZURE_POOL"],
    "vmSize": "Standard_D4s_v3",
    "virtualMachineConfiguration": {
        "imageReference": {
            "publisher": "microsoft-azure-batch",
            "offer": "ubuntu-server-container",
            "sku": "20-04-lts",
            "version": "latest",
        },
        "nodeAgentSKUId": "batch.node.ubuntu 20.04",
        "containerConfiguration": {
            "type": "dockerCompatible",
            "containerImageNames": [os.environ["MIDAS_AZURE_IMAGE"]],
            "containerRegistries": [{
                "registryServer": f"{os.environ['MIDAS_AZURE_ACR']}.azurecr.io",
                "username": os.environ["ACR_USER"],
                "password": os.environ["ACR_PASS"],
            }],
        },
    },
    "targetDedicatedNodes": 0,
    "targetLowPriorityNodes": 0,
    "taskSlotsPerNode": 2,
}
path = os.environ["POOL_JSON"]
with open(path, "w") as f:
    json.dump(pool, f)
PY

az batch pool create --json-file "$POOL_JSON" --account-name "$MIDAS_AZURE_BATCH"
echo "Pool $MIDAS_AZURE_POOL created (0 nodes until job submit)."
