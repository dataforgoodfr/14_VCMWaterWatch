"""
Prefect workflow to mirror NocoDB country profile images to a shared directory.

Country images in NocoDB are stored as S3 attachments with short-lived signed
URLs.  This flow downloads each country's first image, names it with a content
hash for cache-busting, and writes a ``manifest.json`` that maps country codes
to stable local filenames.  The webapp reads the manifest at runtime and serves
the images from a stable, cache-friendly URL.

The output directory is controlled by the ``COUNTRY_IMAGES_DIR`` environment
variable (default: ``data/export/country-images`` locally,
``/public/country-images`` in production).

Output layout::

    <COUNTRY_IMAGES_DIR>/
        FR.a1b2c3d4.jpg
        IT.9f8e7d6c.png
        manifest.json   ← { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }

The manifest is written last so readers always see a consistent state.
"""

import hashlib
import json
import mimetypes
import os
import tempfile
from pathlib import Path

import httpx
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services

COUNTRY_FIELDS = ["Id", "Code", "Image"]


def _ext_from_mimetype(mime: str | None) -> str:
    """Return a file extension (with dot) for *mime*, falling back to ``.bin``."""
    if mime:
        ext = mimetypes.guess_extension(mime)
        # mimetypes can return `.jpe` for JPEG on some platforms
        if ext in (".jpe", ".jpeg"):
            ext = ".jpg"
        if ext:
            return ext
    return ".bin"


@task(name="download_country_images", cache_policy=NO_CACHE)
def download_country_images_task(output_dir: Path) -> dict[str, str]:
    """Download country images and return a code → filename mapping.

    Args:
        output_dir: Temporary staging directory where image files are written.

    Returns:
        A dict mapping country code (e.g. ``"FR"``) to the filename written
        inside *output_dir* (e.g. ``"FR.a1b2c3d4.jpg"``).
    """
    logger = get_run_logger()
    db_helper = services.db_helper()

    records = db_helper.load_all_records(
        table_name="Country", fields=COUNTRY_FIELDS
    )
    logger.info(f"Loaded {len(records)} Country records from NocoDB")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}

    for row in records:
        code = row.get("Code")
        if not code:
            logger.warning(f"Country record id={row.get('Id')} has no Code, skipping")
            continue

        images = row.get("Image")
        if not images:
            logger.debug(f"Country {code}: no Image attachment, skipping")
            continue

        # Use only the first attachment (mirrors what the UI does)
        attachment = images[0] if isinstance(images, list) else images
        signed_url = attachment.get("signedUrl")
        if not signed_url:
            logger.warning(f"Country {code}: attachment has no signedUrl, skipping")
            continue

        # Download image bytes
        try:
            response = httpx.get(signed_url, follow_redirects=True, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            logger.error(f"Country {code}: failed to download image — {exc}")
            continue

        image_bytes = response.content
        content_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        # Determine extension: prefer the NocoDB mimetype field (set at
        # upload time and stable), fall back to the HTTP Content-Type
        # header (can be 'application/octet-stream' for S3 presigned URLs).
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        mime = attachment.get("mimetype") or content_type
        ext = _ext_from_mimetype(mime)

        filename = f"{code}.{content_hash}{ext}"
        dest = output_dir / filename
        dest.write_bytes(image_bytes)
        manifest[code] = filename
        logger.info(f"Country {code}: wrote {filename} ({len(image_bytes)} bytes)")

    return manifest


@flow(name="export_country_images", persist_result=False)
def export_country_images_flow(destination: Path) -> None:
    """Mirror country profile images from NocoDB to *destination*.

    Downloads each country's first image, names it ``{code}.{hash}.{ext}``,
    and writes a ``manifest.json`` mapping codes to filenames.  Uses an atomic
    swap so the directory is never left in a torn state: images are staged to a
    temp directory first, then moved into place, with the manifest written last.

    Args:
        destination: Directory where images and ``manifest.json`` are written.
    """
    logger = get_run_logger()
    destination.mkdir(parents=True, exist_ok=True)

    # Stage new images in a subdirectory of destination (same filesystem) so
    # os.replace is atomic. Using destination.parent can cross a mount point
    # in production (e.g. /public vs /public/country-images bind mount) and
    # raise "Invalid cross-device link" (EXDEV).
    with tempfile.TemporaryDirectory(
        dir=destination, prefix=".country-images-staging-"
    ) as tmp_str:
        tmp_dir = Path(tmp_str)
        manifest = download_country_images_task(output_dir=tmp_dir)

        if not manifest:
            logger.warning("No images downloaded; skipping destination update")
            return

        # Merge with the existing manifest to preserve entries for countries
        # whose downloads failed transiently this run (network glitch, temporary
        # 5xx).  Only entries whose image file is still on disk are kept, so
        # codes genuinely removed from NocoDB are eventually cleaned up.
        existing_manifest_path = destination / "manifest.json"
        if existing_manifest_path.exists():
            try:
                existing = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
                for code, filename in existing.items():
                    if code not in manifest and (destination / filename).exists():
                        manifest[code] = filename
                        logger.debug(
                            f"Country {code}: keeping previous image {filename} "
                            "(download failed this run)"
                        )
            except Exception as exc:
                logger.warning(f"Could not read existing manifest for merging: {exc}")

        # Write manifest into staging dir (moved last, acts as commit point)
        manifest_tmp = tmp_dir / "manifest.json"
        manifest_tmp.write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

        # Move new image files into destination atomically
        new_filenames = set(manifest.values())
        for src in tmp_dir.iterdir():
            if src.name == "manifest.json":
                continue
            dest = destination / src.name
            os.replace(src, dest)
            logger.debug(f"Moved {src.name} → {dest}")

        # Atomically replace manifest last (readers see complete new state)
        os.replace(manifest_tmp, destination / "manifest.json")
        logger.info(f"manifest.json updated with {len(manifest)} entries")

        # Remove stale files (old hashes / codes no longer in NocoDB).
        # Skip the manifest and any hidden staging directories that live in
        # the destination (including our own, still open as tmp_dir).
        for existing in list(destination.iterdir()):
            if existing.name == "manifest.json":
                continue
            if existing.name.startswith("."):
                continue
            if existing.name not in new_filenames:
                existing.unlink()
                logger.info(f"Removed stale file: {existing.name}")


if __name__ == "__main__":
    dest = Path(
        os.environ.get("COUNTRY_IMAGES_DIR", "data/export/country-images")
    )
    export_country_images_flow(destination=dest)
