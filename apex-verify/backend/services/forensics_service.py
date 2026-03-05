"""
Forensics Service — wraps ELA, noise analysis, copy-move, and region ELA.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import numpy as np
from PIL import Image

from ela import compute_ela_features
from region_ela import compute_region_ela_score


async def run(image: Image.Image, mask: np.ndarray | None = None) -> Dict[str, Any]:
    """Run global ELA + region ELA analysis concurrently."""
    loop = asyncio.get_event_loop()

    ela_res = await loop.run_in_executor(None, compute_ela_features, image)
    region_res = await loop.run_in_executor(None, compute_region_ela_score, image, mask)

    return {
        "ela": ela_res,
        "region_ela": region_res,
        "ela_score": float(ela_res["ela_score"]),
        "region_ela_score": float(region_res["region_ela_score"]),
    }


__all__ = ["run"]
