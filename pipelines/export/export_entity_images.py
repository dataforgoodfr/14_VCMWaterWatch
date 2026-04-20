"""
Generic Prefect workflow to mirror NocoDB entity images to a shared directory.

Entity images in NocoDB are stored as S3 attachments with short-lived signed
URLs.  This flow downloads each entity's first image, names it with a content
hash for cache-busting, and writes a ``manifest.json`` that maps entity keys
to stable local filenames.  The webapp reads the manifest at runtime and serves
the images from a stable, cache-friendly URL.

The output directory is controlled by the ``EXPORT_IMAGES_DIR`` environment
variable (default: ``data/export/images`` locally, ``/public/images`` in
production).  Each entity is stored in a subdirectory:

    <EXPORT_IMAGES_DIR>/
        country/
            FR.a1b2c3d4.jpg
            manifest.json   ← { "FR": "FR.a1b2c3d4.jpg", … }
        team/
            gaspard-lemaire.9f8e7d6c.jpg
            manifest.json   ← { "gaspard-lemaire": "gaspard-lemaire.9f8e7d6c.jpg", … }

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
        # mimetypes can return `.jpe` or `.jpeg` for JPEG on some platforms
        if ext in (".jpe", ".jpeg"):
            ext = ".jpg"
        if ext:
            return ext
    return ".bin"


def _slugify(value: str) -> str:
    """Convert *value* to a URL-safe slug.

    Steps:
    1. Unicode normalise to ASCII (NFD → ASCII-fold).
    2. Lowercase.
    3. Replace non-alphanumeric characters with ``-``.
    4. Collapse repeated ``-``.
    5. Strip leading/trailing ``-``.

    .. important::
        This function **must** produce identical output to ``slugify()`` in
        ``webapp/lib/fetchTeam.ts`` because the result is used as a manifest
        key that the webapp looks up at runtime.  If the two implementations
        diverge, image look-ups will silently return ``null``.

        Equivalence note: Python uses ``encode("ascii", "ignore")`` after NFD
        decomposition, which drops all non-ASCII bytes.  TypeScript strips only
        U+0300\u2013U+036F (Combining Diacritical Marks block).  These are
        identical for Latin/Greek/Cyrillic names but could theoretically differ
        for characters with combining marks outside that range (e.g. some
        Vietnamese or Semitic names).  Add a cross-language fixture test if
        such names are introduced.
    """
    # Decompose accented characters and drop the combining marks
    normalised = unicodedata.normalize("NFD", value)
    ascii_value = normalised.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    # Replace any run of non-alphanumeric characters with a single hyphen
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")


@task(name="export_entity_images_task", cache_policy=NO_CACHE)
def export_entity_images_task(
    table_name: str,
    key_field: str,
    entity_name: str,
    fields: list[str],
    output_dir: Path,
    slugify: bool = False,
) -> dict[str, str]:
    """Download entity images from NocoDB and return a key → filename mapping.

    Args:
        table_name:  NocoDB table to load (e.g. ``"Country"`` or ``"Team"``).
        key_field:   Field whose value becomes the filename key (e.g. ``"Code"``
                     or ``"Name"``).
        entity_name: Human-readable name used in log messages.
        fields:      List of fields to fetch from the table.
        output_dir:  Temporary staging directory where image files are written.
        slugify:     When ``True``, the key value is slugified before being used
                     as the filename prefix (e.g. ``"Gaspard Lemaire"`` →
                     ``"gaspard-lemaire"``).

    Returns:
        A dict mapping the (possibly slugified) key to the filename written
        inside *output_dir*.
    """
    logger = get_run_logger()
    db_helper = services.db_helper()

    records = db_helper.load_all_records(table_name=table_name, fields=fields)
    logger.info(f"Loaded {len(records)} {entity_name} records from NocoDB")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    # Track slugs used this run to detect collisions.
    seen_slugs: dict[str, int] = {}

    for row in records:
        raw_key = row.get(key_field)
        if not raw_key:
            logger.warning(
                f"{entity_name} record id={row.get('Id')} has no {key_field}, skipping"
            )
            continue

        key = _slugify(str(raw_key)) if slugify else str(raw_key)

        # Collision detection for slugified keys.
        # The first occurrence keeps the bare slug; subsequent occurrences with
        # the same slug get a numeric suffix starting at -2 (i.e. `key`,
        # `key-2`, `key-3`, …).  There is intentionally no `key-1` variant.
        if key in seen_slugs:
            seen_slugs[key] += 1
            suffixed = f"{key}-{seen_slugs[key]}"
            logger.warning(
                f"{entity_name} '{raw_key}': slug collision, using '{suffixed}'"
            )
            key = suffixed
        else:
            seen_slugs[key] = 1

        images = row.get("Image")
        if not images:
            logger.debug(f"{entity_name} '{raw_key}': no Image attachment, skipping")
            continue

        # Use only the first attachment
        attachment = images[0] if isinstance(images, list) else images
        signed_url = attachment.get("signedUrl")
        if not signed_url:
            logger.warning(
                f"{entity_name} '{raw_key}': attachment has no signedUrl, skipping"
            )
            continue

        # Download image bytes
        try:
            response = httpx.get(signed_url, follow_redirects=True, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            logger.error(f"{entity_name} '{raw_key}': failed to download image — {exc}")
            continue

        image_bytes = response.content
        content_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        # Prefer the NocoDB mimetype field; fall back to HTTP Content-Type.
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        mime = attachment.get("mimetype") or content_type
        ext = _ext_from_mimetype(mime)

        filename = f"{key}.{content_hash}{ext}"
        dest = output_dir / filename
        dest.write_bytes(image_bytes)
        manifest[key] = filename
        logger.info(
            f"{entity_name} '{raw_key}': wrote {filename} ({len(image_bytes)} bytes)"
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
    """Mirror entity images from NocoDB to the shared images directory.

    Downloads each entity's first image, names it ``{key}.{hash}.{ext}``, and
    writes a ``manifest.json`` mapping keys to filenames.  Uses an atomic swap
    so the directory is never left in a torn state: images are staged in a temp
    subdirectory first, then moved into place, with the manifest written last.

    The destination is ``<EXPORT_IMAGES_DIR>/<entity_name>/``.  Existing
    entries whose files are still on disk are preserved when a download fails
    transiently (merge logic).

    Args:
        entity_name: Short identifier used as the subdirectory name (e.g.
                     ``"country"`` or ``"team"``).
        table_name:  NocoDB table name (e.g. ``"Country"`` or ``"Team"``).
        key_field:   Field to use as the manifest key (e.g. ``"Code"`` or
                     ``"Name"``).
        fields:      Fields to request from NocoDB.
        slugify:     Whether to slugify the key value for the filename.
    """
    logger = get_run_logger()

    base_dir = Path(os.environ.get("EXPORT_IMAGES_DIR", "data/export/images"))
    destination = base_dir / entity_name
    destination.mkdir(parents=True, exist_ok=True)

    # Stage new images in a subdirectory of destination (same filesystem) so
    # os.replace is atomic.
    with tempfile.TemporaryDirectory(
        dir=destination, prefix=f".{entity_name}-images-staging-"
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

        # Merge with the existing manifest to preserve entries whose downloads
        # failed transiently this run.  Only entries whose image file is still
        # on disk are kept, so keys genuinely removed from NocoDB are eventually
        # cleaned up.
        existing_manifest_path = destination / "manifest.json"
        if existing_manifest_path.exists():
            try:
                existing = json.loads(
                    existing_manifest_path.read_text(encoding="utf-8")
                )
                for key, filename in existing.items():
                    if key not in manifest and (destination / filename).exists():
                        manifest[key] = filename
                        logger.debug(
                            f"{entity_name} '{key}': keeping previous image {filename} "
                            "(download failed this run)"
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
        for existing in list(destination.iterdir()):
            if existing.name == "manifest.json":
                continue
            if existing.name.startswith("."):
                continue
            if existing.name not in new_filenames:
                existing.unlink()
                logger.info(f"Removed stale file: {existing.name}")
