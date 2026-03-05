"""
Metadata Service — wraps ingestion.py with a clean async interface.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from ingestion import compute_metadata_score, extract_exif, load_image
from PIL import Image


async def run(file_bytes: bytes) -> Dict[str, Any]:
    """Extract EXIF and compute metadata fraud score."""
    loop = asyncio.get_event_loop()
    exif = await loop.run_in_executor(None, extract_exif, file_bytes)
    metadata_score, metadata_details = await loop.run_in_executor(
        None, compute_metadata_score, exif
    )
    return {
        "exif": exif,
        "metadata_score": float(metadata_score),
        "metadata_details": metadata_details,
    }


__all__ = ["run"]
