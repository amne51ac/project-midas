"""Upload/download JSON to midas Blob storage."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _client():
    from azure.storage.blob import BlobServiceClient

    account = os.environ.get("MIDAS_AZURE_STORAGE", "midascredencest")
    key = os.environ.get("MIDAS_STORAGE_KEY", "")
    if not key:
        raise RuntimeError("MIDAS_STORAGE_KEY not set")
    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=key,
    )


def upload_json(blob_name: str, payload: dict) -> None:
    container = os.environ.get("MIDAS_BLOB_CONTAINER", "midas-results")
    data = json.dumps(payload, indent=2).encode("utf-8")
    client = _client()
    client.get_blob_client(container=container, blob=blob_name).upload_blob(
        data, overwrite=True, content_type="application/json"
    )


def upload_file(
    local_path: str | Path,
    blob_name: str,
    *,
    content_type: str = "application/octet-stream",
) -> None:
    container = os.environ.get("MIDAS_BLOB_CONTAINER", "midas-results")
    path = Path(local_path)
    client = _client()
    with open(path, "rb") as f:
        client.get_blob_client(container=container, blob=blob_name).upload_blob(
            f, overwrite=True, content_type=content_type
        )


def download_json(blob_name: str) -> dict:
    container = os.environ.get("MIDAS_BLOB_CONTAINER", "midas-results")
    client = _client()
    raw = client.get_blob_client(container=container, blob=blob_name).download_blob().readall()
    return json.loads(raw.decode())
