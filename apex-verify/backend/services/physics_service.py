"""
Physics Consistency Service

Performs physics-based visual validation to detect:
- Shadow direction inconsistency across image regions
- Lighting/illumination mismatch between regions
- Unrealistic noise patterns (per-region noise std variance)
- Specular highlight inconsistency

Returns physics_consistency_score [0,1] and a list of flagged issues.
Higher score = more physically consistent = less suspicious.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import asyncio
import cv2
import numpy as np
from PIL import Image


def _pil_to_cv2(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _analyze_shadow_consistency(gray: np.ndarray) -> Tuple[float, str]:
    """
    Analyze shadow direction consistency using gradient orientation histograms.

    Strategy:
    - Compute Sobel gradients
    - Divide image into 4 quadrants
    - Compare dominant gradient direction in each quadrant
    - Large circular variance in dominant directions → inconsistent shadows

    Returns (score [0,1], flag message or empty string).
    """
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    angle = np.arctan2(sobely, sobelx)  # radians, [-pi, pi]

    h, w = gray.shape
    quadrants = [
        angle[:h//2, :w//2],
        angle[:h//2, w//2:],
        angle[h//2:, :w//2],
        angle[h//2:, w//2:],
    ]
    mag_quads = [
        magnitude[:h//2, :w//2],
        magnitude[:h//2, w//2:],
        magnitude[h//2:, :w//2],
        magnitude[h//2:, w//2:],
    ]

    dominant_angles = []
    for q_angle, q_mag in zip(quadrants, mag_quads):
        total_mag = q_mag.sum()
        if total_mag < 1.0:
            continue
        # Weighted circular mean
        sin_mean = (np.sin(q_angle) * q_mag).sum() / total_mag
        cos_mean = (np.cos(q_angle) * q_mag).sum() / total_mag
        dominant_angle = np.arctan2(sin_mean, cos_mean)
        dominant_angles.append(dominant_angle)

    if len(dominant_angles) < 2:
        return 0.6, ""  # Not enough data

    # Circular variance: 1 - R where R = mean resultant length
    sin_vals = [np.sin(a) for a in dominant_angles]
    cos_vals = [np.cos(a) for a in dominant_angles]
    R = np.sqrt(np.mean(sin_vals)**2 + np.mean(cos_vals)**2)
    circular_variance = 1.0 - R  # 0 = all aligned, 1 = completely random

    # Low circular variance = consistent shadows
    score = float(max(0.0, min(1.0, 1.0 - circular_variance * 1.5)))
    flag = "Shadow direction inconsistency detected across image regions" if circular_variance > 0.45 else ""
    return score, flag


def _analyze_lighting_consistency(hsv: np.ndarray) -> Tuple[float, str]:
    """
    Compare illumination (V channel) across image regions.

    Significant variance in mean brightness between spatially separated regions
    that are expected to share similar lighting suggests composite imagery.
    """
    v_channel = hsv[:, :, 2].astype(np.float32)
    h, w = v_channel.shape

    regions = [
        v_channel[:h//3, :w//3],
        v_channel[:h//3, w//3:2*w//3],
        v_channel[:h//3, 2*w//3:],
        v_channel[h//3:2*h//3, :w//3],
        v_channel[h//3:2*h//3, 2*w//3:],
        v_channel[2*h//3:, :w//3],
        v_channel[2*h//3:, w//3:2*w//3],
        v_channel[2*h//3:, 2*w//3:],
    ]

    means = [r.mean() for r in regions if r.size > 0]
    if len(means) < 2:
        return 0.6, ""

    std_of_means = float(np.std(means))
    # Very high std of regional brightness means indicates lighting mismatch
    # Typical natural std range: 0-60; above 60 is suspicious
    normalized_std = std_of_means / 80.0
    score = float(max(0.0, min(1.0, 1.0 - normalized_std)))
    flag = "Lighting/illumination inconsistency detected between image regions" if std_of_means > 50.0 else ""
    return score, flag


def _analyze_noise_consistency(gray: np.ndarray) -> Tuple[float, str]:
    """
    Analyze whether noise level is uniform across image patches.

    Significant variance in per-patch noise std suggests composite/manipulated imagery.
    """
    h, w = gray.shape
    patch_size = max(32, min(h, w) // 8)

    noise_stds = []
    for y in range(0, h - patch_size, patch_size):
        for x in range(0, w - patch_size, patch_size):
            patch = gray[y:y+patch_size, x:x+patch_size].astype(np.float32)
            # Estimate noise using the median absolute deviation of high-pass filter
            blurred = cv2.GaussianBlur(patch, (5, 5), 0)
            residual = patch - blurred
            noise_stds.append(float(np.std(residual)))

    if len(noise_stds) < 4:
        return 0.6, ""

    variance_of_noise = float(np.std(noise_stds))
    normalized = variance_of_noise / 20.0
    score = float(max(0.0, min(1.0, 1.0 - normalized)))
    flag = "Inconsistent noise pattern across image patches — possible splicing" if variance_of_noise > 12.0 else ""
    return score, flag


def _analyze_specular_highlights(hsv: np.ndarray) -> Tuple[float, str]:
    """
    Detect specular highlight (bright spot) distribution consistency.

    In natural images, specular highlights come from a coherent light source.
    Multiple disparate bright spots with inconsistent distribution can indicate compositing.
    """
    v = hsv[:, :, 2]
    s = hsv[:, :, 1]
    # Specular highlights: high V, low S
    highlight_mask = (v > 240) & (s < 30)
    highlight_count = int(highlight_mask.sum())

    total_pixels = v.size
    highlight_ratio = highlight_count / total_pixels

    # Use connected components to count distinct specular regions
    highlight_uint8 = highlight_mask.astype(np.uint8) * 255
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(highlight_uint8)
    num_specular_regions = max(0, num_labels - 1)

    # Suspicious if many isolated specular regions (> 6 distinct ones with sizable area)
    large_regions = sum(1 for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] > 50) if num_labels > 1 else 0

    if large_regions > 8:
        score = 0.30
        flag = f"Multiple ({large_regions}) specular highlight regions detected — possible compositing"
    elif large_regions > 4:
        score = 0.55
        flag = ""
    else:
        score = 0.80
        flag = ""

    return score, flag


async def run(image: Image.Image) -> Dict[str, Any]:
    """Run all physics consistency checks and return aggregated report."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_sync, image)
    return result


def _run_sync(image: Image.Image) -> Dict[str, Any]:
    img_cv = _pil_to_cv2(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

    shadow_score, shadow_flag = _analyze_shadow_consistency(gray)
    lighting_score, lighting_flag = _analyze_lighting_consistency(hsv)
    noise_score, noise_flag = _analyze_noise_consistency(gray)
    specular_score, specular_flag = _analyze_specular_highlights(hsv)

    flags = [f for f in [shadow_flag, lighting_flag, noise_flag, specular_flag] if f]

    # Weighted aggregate
    composite = (
        shadow_score * 0.30
        + lighting_score * 0.35
        + noise_score * 0.25
        + specular_score * 0.10
    )

    return {
        "physics_consistency_score": round(float(max(0.0, min(1.0, composite))), 3),
        "sub_scores": {
            "shadow_consistency": round(shadow_score, 3),
            "lighting_consistency": round(lighting_score, 3),
            "noise_homogeneity": round(noise_score, 3),
            "specular_consistency": round(specular_score, 3),
        },
        "physics_flags": flags,
    }


__all__ = ["run"]
