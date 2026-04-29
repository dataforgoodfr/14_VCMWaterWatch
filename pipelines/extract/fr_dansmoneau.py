"""
Prefect workflow for downloading the dansmoneau DuckDB database.

Downloads the pre-built DuckDB from data.gouv.fr (Eau et Captages dataset) to
``data/raw/fr_dansmoneau.duckdb``.  The download is skipped when the file
already exists **and** its size matches the remote ``Content-Length``.
"""

from pathlib import Path

import httpx
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

DANSMONEAU_URL = (
    "https://pollution-eau-s3.s3.fr-par.scw.cloud/prod/database/data.duckdb"
)


@task(name="extract_fr_dansmoneau_download", cache_policy=NO_CACHE)
def download_duckdb(data_directory: Path) -> Path:
    """Download the dansmoneau DuckDB file, skipping if already up-to-date."""
    logger = get_run_logger()
    dest = data_directory / "raw" / "fr_dansmoneau.duckdb"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check remote size
    head = httpx.head(DANSMONEAU_URL, follow_redirects=True, timeout=30.0)
    head.raise_for_status()
    remote_size = int(head.headers.get("content-length", -1))

    if dest.exists() and remote_size > 0 and dest.stat().st_size == remote_size:
        logger.info(
            f"fr_dansmoneau.duckdb already present and size matches ({remote_size} bytes), skipping download"
        )
        return dest

    logger.info(
        f"Downloading dansmoneau DuckDB ({remote_size / 1e9:.2f} GB) → {dest}"
    )
    with httpx.stream("GET", DANSMONEAU_URL, follow_redirects=True, timeout=None) as resp:
        resp.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in resp.iter_bytes(chunk_size=1 << 20):
                fh.write(chunk)

    logger.info(f"Download complete: {dest.stat().st_size} bytes")
    return dest


@flow(name="extract_fr_dansmoneau", persist_result=False)
def extract_fr_dansmoneau(data_directory: Path = Path("data")) -> Path:
    """Download the dansmoneau DuckDB to the raw data directory."""
    return download_duckdb(data_directory)


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    extract_fr_dansmoneau(data_directory)
