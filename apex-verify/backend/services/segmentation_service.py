"""
Segmentation Service — wraps RT-DETR + SAM2 detection pipeline.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from PIL import Image
from detection import get_detection_pipeline


async def run(image: Image.Image) -> Dict[str, Any]:
    """Run object detection and SAM2 segmentation."""
    loop = asyncio.get_event_loop()
    pipeline = get_detection_pipeline()
    result = await loop.run_in_executor(None, pipeline.run, image)
    return {
        "detections": result.get("detections", []),
        "sam2_confidence": float(result.get("sam2_confidence", 0.0)),
        "combined_mask": result.get("combined_mask"),  # numpy array — not JSON-serializable
    }


__all__ = ["run"]
