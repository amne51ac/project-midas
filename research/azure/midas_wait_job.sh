#!/usr/bin/env bash
# Wait for a Batch job to finish, then scale pool to 0 (stops VM charges).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/midas_config.env"

JOB_ID="${1:?Usage: midas_wait_job.sh <job-id>}"
az batch account login --name "$MIDAS_AZURE_BATCH" --resource-group "$MIDAS_AZURE_RG"

echo "Waiting for job $JOB_ID..."
while true; do
  stats=$(az batch job show --job-id "$JOB_ID" --account-name "$MIDAS_AZURE_BATCH" \
    --query "{active:executionInfo.activeTaskCount,succeeded:executionInfo.succeededTaskCount,failed:executionInfo.failedTaskCount}" -o json)
  active=$(echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['active'])")
  ok=$(echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['succeeded'])")
  bad=$(echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['failed'])")
  echo "  active=$active succeeded=$ok failed=$bad"
  if [ "$active" -eq 0 ]; then
    break
  fi
  sleep 30
done

"$SCRIPT_DIR/midas_scale_down.sh"
echo "Job $JOB_ID complete. Pool scaled to 0."
echo "Collect: python azure/midas_collect_results.py --job-id $JOB_ID"
