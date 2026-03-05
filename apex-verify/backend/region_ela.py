from typing import Dict

import cv2
import numpy as np
from PIL import Image

from ela import compute_ela


def compute_region_ela_score(
    image: Image.Image,
    mask: np.ndarray | None,
    num_regions: int = 4,
) -> Dict[str, float]:
    """
    Compute a region-focused ELA score.

    If a binary mask is provided (e.g., from SAM2 segmentation), we restrict ELA
    statistics to that region. Otherwise, we compute ELA across a grid of regions
    and use the most anomalous area as the region score.

    Returns:
        {
          "region_ela_score": float in [0,1],
          "max_region_intensity": float,
          "mean_region_intensity": float
        }
    """
    ela_image, _ = compute_ela(image)
    ela_array = np.array(ela_image)
    ela_gray = cv2.cvtColor(ela_array, cv2.COLOR_RGB2GRAY).astype("float32")

    h, w = ela_gray.shape

    if mask is not None:
        # Ensure mask is boolean for indexing
        mask_bool = mask.astype(bool)
        if mask_bool.shape != ela_gray.shape:
            mask_bool = cv2.resize(mask_bool.astype("uint8"), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
        region_vals = ela_gray[mask_bool]
        if region_vals.size == 0:
            region_intensity = 0.0
        else:
            region_intensity = float(region_vals.mean())
        max_region_intensity = region_intensity
        mean_region_intensity = region_intensity
    else:
        # Split into grid and measure intensities
        region_heights = np.linspace(0, h, num_regions + 1, dtype=int)
        region_widths = np.linspace(0, w, num_regions + 1, dtype=int)
        region_intensities = []
        for i in range(num_regions):
            for j in range(num_regions):
                y0, y1 = region_heights[i], region_heights[i + 1]
                x0, x1 = region_widths[j], region_widths[j + 1]
                region = ela_gray[y0:y1, x0:x1]
                if region.size == 0:
                    continue
                region_intensities.append(float(region.mean()))

        if not region_intensities:
            max_region_intensity = 0.0
            mean_region_intensity = 0.0
        else:
            max_region_intensity = max(region_intensities)
            mean_region_intensity = sum(region_intensities) / len(region_intensities)

    # Normalize to [0, 1] using 0-255 intensity
    region_ela_score = max_region_intensity / 255.0 if max_region_intensity > 0 else 0.0
    region_ela_score = float(max(0.0, min(1.0, region_ela_score)))

    return {
        "region_ela_score": region_ela_score,
        "max_region_intensity": float(max_region_intensity),
        "mean_region_intensity": float(mean_region_intensity),
    }


__all__ = ["compute_region_ela_score"]

