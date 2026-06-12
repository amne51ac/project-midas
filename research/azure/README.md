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

Results upload to Blob (`midas-results/results/<job-id>/…`) automatically. **Do not scale the pool down before collecting** if you rely on Batch stdout (nodes lose task files on deallocate).

```bash
python azure/midas_collect_results.py --job-id midas-seed-XXXXXXXX
python scripts/aggregate_seed_sweep.py --input data/processed/azure_results
```

**Local replay** (no Azure charges):

```bash
python scripts/run_seed_sweep.py --seeds 20
python scripts/aggregate_seed_sweep.py
```

## T1 ingest (Track C)

```bash
# 1. Build registry from Cantat-Gaudin table1 (~2k clusters)
python scripts/bootstrap_t1_registry.py --pilot 50

# 2. Local pilot (keep --workers low for Gaia TAP)
python scripts/run_t1_ingest.py --registry data/registry/t1_pilot.csv --limit 10 --workers 2

# 3. QC
python scripts/qc_t1_ingest.py

# 4. Azure Batch (rebuild image first — includes registry CSV)
./midas_build_image.sh
python azure/midas_submit_t1_ingest.py --registry data/registry/t1_pilot.csv --limit 50
python scripts/qc_t1_ingest.py --blob-prefix processed/t1/members/midas-t1-XXXX/
```

Output: `data/processed/t1/members/{cluster_id}.parquet` (+ Blob mirror).

Full registry: `data/registry/t1_clusters.csv` (~1,900 clusters with ≥30 CG members).

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
