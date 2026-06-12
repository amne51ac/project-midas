FROM python:3.12-slim-bookworm

WORKDIR /app/research

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY midas ./midas
COPY scripts ./scripts
COPY azure/worker.py ./azure/worker.py
COPY data/processed/t0_join_ir.csv ./data/processed/t0_join_ir.csv
COPY data/processed/m34_join_ir.csv ./data/processed/m34_join_ir.csv
COPY data/processed/malofeeva_tid ./data/processed/malofeeva_tid
COPY data/benchmarks ./data/benchmarks
COPY data/processed/t0/literature ./data/processed/t0/literature

RUN mkdir -p data/processed/azure_results data/processed/t0/literature \
    && touch data/processed/t0/literature/hyades_gold_probe_unavailable.marker \
    && chmod -R a+rwX data

ENV PYTHONPATH=/app/research
ENV MIDAS_AZURE=1

WORKDIR /app/research
CMD ["python", "azure/worker.py"]
