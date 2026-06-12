# Midas Credence — Azure lab

All resources use the **`midas-`** prefix so you can identify what this project created.

## Resources

| Resource | Name |
|----------|------|
| Resource group | `midas-credence-rg` |
| Storage | `midascredencest` |
| Container registry | `midascredenceacr` |
| Batch account | `midascredencebatch` |
| Batch pool | `midas-credence-pool` |
| Blob container | `midas-results` |
| Docker image | `midascredenceacr.azurecr.io/midas-credence:latest` |

## Setup (once)

```bash
cd research/azure
chmod +x midas_*.sh
./midas_provision.sh
./midas_build_image.sh
./midas_create_pool.sh
```

## Run seed sweep

```bash
cd research
. .venv/bin/activate
python azure/midas_submit_seed_sweep.py --seeds 20
```

## Cleanup (important)

**After jobs finish**, scale the pool to zero (stops compute charges):

```bash
./midas_scale_down.sh
```

**Full teardown** (deletes everything in the RG):

```bash
./midas_teardown.sh   # type: midas-teardown
```

Storage (~$1/mo per 50 GB) and ACR Basic (~$5/mo) bill until teardown.

**Note:** This subscription has a **6-core Batch quota** — pool uses `Standard_D4s_v3` (4 cores). Request a quota increase in Azure Portal → Batch account → Quotas for larger parallel sweeps.
