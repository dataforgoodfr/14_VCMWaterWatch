"""
Generic Prefect workflow to mirror NocoDB entity images to a shared directory.

Entity images in NocoDB are stored as S3 attachments with short-lived signed
URLs.  This flow downloads each entity's first image, names it with a
content hash for cache-busting, and writes a ``manifest.json`` that maps
entity keys to stable local filenames.  The webapp reads the manifest at
runtime and serves the images from a stable, cache-friendly URL.

The output directory is controlled by the ``EXPORT_IMAGES_DIR`` environment
variable (default: ``data/export/images`` locally, ``/public/images`` in
production).  Each entity is written to a subdirectory:
``<EXPORT_IMAGES_DIR>/<entity>/``.

Output layout::

    <EXPORT_IMAGES_DIR>/
        country/
            FR.a1b2c3d4.jpg
            IT.9f8e7d6c.png
            manifest.json   ← { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
        team/
            gaspard-lemaire.a1b2c3d4.jpg
            manifest.json   ← { "gaspard-lemaire": "gaspard-lemaire.a1b2c3d4.jpg" }

The manifest is written last so readers always see a consistent state.
"""

import hashlib
import json
import mimetypes
import os
import re
import tempfile
import unicodedata
from pathlib import Path

import httpx
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services


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


def _slugify(value: str) -> str:
    """Convert a string to a URL-safe slug.

    Steps:
    1. Unicode-normalise to NFD, then ASCII-fold (drop combining chars).
    2. Lower-case.
    3. Replace any non-alphanumeric character with ``-``.
    4. Collapse repeated ``-``.
    5. Strip leading/trailing ``-``.

    Examples::

        "Gaspard Lemaire" → "gaspard-lemaire"
        "Ève Müller"      → "eve-muller"
        "John  O'Brien"   → "john-o-brien"
    """
    # NFD decompose, keep only ASCII chars
    normalized = unicodedata.normalize("NFD", value)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    lower = ascii_str.lower()
    # Replace non-alphanumeric with dash
    dashed = re.sub(r"[^a-z0-9]+", "-", lower)
    return dashed.strip("-")


@task(name="download_entity_images", cache_policy=NO_CACHE)
def export_entity_images_task(
    table_name: str,
    key_field: str,
    entity_name: str,
    fields: list[str],
    output_dir: Path,
    slugify: bool = False,
) -> dict[str, str]:
    """Download entity images and return a key → filename mapping.

    Args:
        table_name:  NocoDB table to query (e.g. ``"Country"`` or ``"Team"``).
        key_field:   Field to use as the image key (e.g. ``"Code"`` or
                     ``"Name"``).
        entity_name: Human-readable name for logging (e.g. ``"country"``).
        fields:      Field names to fetch from NocoDB.
        output_dir:  Temporary staging directory where image files are
                     written.
        slugify:     If ``True``, the key value is slugified before being
                     used in the filename (e.g. ``"Gaspard Lemaire"`` →
                     ``"gaspard-lemaire"``).  On slug collision within a
                     run, a ``-2``, ``-3``, … suffix is appended and a
                     warning is logged.

    Returns:
        A dict mapping the key (or slug) to the filename written inside
        *output_dir*.
    """
    logger = get_run_logger()
    db_helper = services.db_helper()

    records = db_helper.load_all_records(table_name=table_name, fields=fields)
    logger.info(f"Loaded {len(records)} {entity_name} records from NocoDB")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    # Track used slugs within this run to detect collisions
    used_slugs: set[str] = set()

    for row in records:
        raw_key = row.get(key_field)
        if not raw_key:
            logger.warning(
                f"{entity_name.capitalize()} record id={row.get('Id')} "
                f"has no {key_field}, skipping"
            )
            continue

        if slugify:
            base_slug = _slugify(str(raw_key))
            if not base_slug:
                logger.warning(
                    f"{entity_name.capitalize()} record id={row.get('Id')}: "
                    f"slugified key is empty for {raw_key!r}, skipping"
                )
                continue
            # Resolve slug collision
            slug = base_slug
            counter = 2
            while slug in used_slugs:
                logger.warning(
                    f"{entity_name.capitalize()}: slug collision for "
                    f"{raw_key!r} → {slug!r}, using {base_slug}-{counter}"
                )
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_slugs.add(slug)
            key = slug
        else:
            key = str(raw_key)

        images = row.get("Image")
        if not images:
            logger.debug(
                f"{entity_name.capitalize()} {raw_key!r}: no Image attachment, skipping"
            )
            continue

        # Use only the first attachment (mirrors what the UI does)
        attachment = images[0] if isinstance(images, list) else images
        signed_url = attachment.get("signedUrl")
        if not signed_url:
            logger.warning(
                f"{entity_name.capitalize()} {raw_key!r}: attachment has no signedUrl, skipping"
            )
            continue

        # Download image bytes
        try:
            response = httpx.get(signed_url, follow_redirects=True, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            logger.error(
                f"{entity_name.capitalize()} {raw_key!r}: failed to download image — {exc}"
            )
            continue

        image_bytes = response.content
        content_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        # Determine extension: prefer the NocoDB mimetype field (set at
        # upload time and stable), fall back to the HTTP Content-Type header.
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        mime = attachment.get("mimetype") or content_type
        ext = _ext_from_mimetype(mime)

        filename = f"{key}.{content_hash}{ext}"
        dest = output_dir / filename
        dest.write_bytes(image_bytes)
        manifest[key] = filename
        logger.info(
            f"{entity_name.capitalize()} {raw_key!r}: wrote {filename} "
            f"({len(image_bytes)} bytes)"
        )

    return manifest


@flow(name="export_entity_images", persist_result=False)
def export_entity_images_flow(
    entity_name: str,
    table_name: str,
    key_field: str,
    fields: list[str],
    slugify: bool = False,
) -> None:
    """Mirror entity images from NocoDB to ``<EXPORT_IMAGES_DIR>/<entity_name>/``.

    Downloads each entity's first image, names it ``{key}.{hash}.{ext}``,
    and writes a ``manifest.json`` mapping keys to filenames.  Uses an atomic
    swap so the directory is never left in a torn state: images are staged to a
    temp directory first, then moved into place, with the manifest written last.

    Merges with any existing manifest to preserve entries for entities whose
    downloads failed transiently this run.

    Args:
        entity_name:  Subdirectory name under ``EXPORT_IMAGES_DIR`` (e.g.
                      ``"country"`` or ``"team"``).
        table_name:   NocoDB table to query (e.g. ``"Country"``).
        key_field:    Field to use as the image key (e.g. ``"Code"``).
        fields:       Field names to fetch from NocoDB.
        slugify:      Whether to slugify the key value for filenames.
    """
    logger = get_run_logger()

    images_dir = Path(
        os.environ.get("EXPORT_IMAGES_DIR", "data/export/images")
    )
    destination = images_dir / entity_name
    destination.mkdir(parents=True, exist_ok=True)

    # Stage new images in a subdirectory of destination (same filesystem) so
    # os.replace is atomic.
    with tempfile.TemporaryDirectory(
        dir=destination, prefix=f".{entity_name}-staging-"
    ) as tmp_str:
        tmp_dir = Path(tmp_str)
        manifest = export_entity_images_task(
            table_name=table_name,
            key_field=key_field,
            entity_name=entity_name,
            fields=fields,
            output_dir=tmp_dir,
            slugify=slugify,
        )

        if not manifest:
            logger.warning(
                f"No images downloaded for {entity_name}; skipping destination update"
            )
            return

        # Merge with the existing manifest to preserve entries for entities
        # whose downloads failed transiently this run.
        existing_manifest_path = destination / "manifest.json"
        if existing_manifest_path.exists():
            try:
                existing = json.loads(
                    existing_manifest_path.read_text(encoding="utf-8")
                )
                for k, filename in existing.items():
                    if k not in manifest and (destination / filename).exists():
                        manifest[k] = filename
                        logger.debug(
                            f"{entity_name.capitalize()} {k!r}: keeping previous "
                            f"image {filename} (download failed this run)"
                        )
            except Exception as exc:
                logger.warning(
                    f"Could not read existing manifest for merging: {exc}"
                )

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
        logger.info(
            f"manifest.json updated with {len(manifest)} entries for {entity_name}"
        )

        # Remove stale files (old hashes / keys no longer in NocoDB).
        for existing_file in list(destination.iterdir()):
            if existing_file.name == "manifest.json":
                continue
            if existing_file.name.startswith("."):
                continue
            if existing_file.name not in new_filenames:
                existing_file.unlink()
                logger.info(
                    f"Removed stale {entity_name} file: {existing_file.name}"
                )
