from __future__ import annotations

import base64
import io
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

from ela import compute_ela


def _encode_image_to_base64_png(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def create_ela_heatmap_overlay(original: Image.Image) -> Tuple[Image.Image, Image.Image]:
    """
    Create ELA heatmap and an overlay of that heatmap on the original image.
    """
    ela_img, _ = compute_ela(original)

    ela_arr = np.array(ela_img)
    gray = cv2.cvtColor(ela_arr, cv2.COLOR_RGB2GRAY)
    heatmap = cv2.applyColorMap(cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype("uint8"), cv2.COLORMAP_JET)

    orig_arr = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)
    overlay = cv2.addWeighted(orig_arr, 0.6, heatmap, 0.4, 0)

    heatmap_pil = Image.fromarray(cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB))
    overlay_pil = Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
    return heatmap_pil, overlay_pil


def overlay_sam2_mask(original: Image.Image, mask: np.ndarray | None) -> Image.Image:
    """
    Overlay a SAM2 segmentation mask (boolean array) on top of the original image.
    """
    orig_arr = np.array(original)
    h, w, _ = orig_arr.shape

    if mask is None:
        return Image.fromarray(orig_arr)

    mask_resized = mask
    if mask.shape[:2] != (h, w):
        mask_resized = cv2.resize(mask.astype("uint8"), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)

    colored = orig_arr.copy()
    # Red mask with transparency
    red_layer = np.zeros_like(colored)
    red_layer[..., 0] = 255  # Red channel

    alpha = 0.4
    colored[mask_resized] = (
        alpha * red_layer[mask_resized] + (1 - alpha) * colored[mask_resized]
    ).astype("uint8")

    return Image.fromarray(colored)


def build_explainability_payload(
    original: Image.Image,
    sam2_mask: np.ndarray | None,
    fraud_reasons: List[str],
) -> Dict:
    """
    Build a JSON-serializable explainability payload containing:
    - Base64-encoded ELA heatmap
    - Base64-encoded ELA overlay
    - Base64-encoded SAM2 overlay
    - Human-readable fraud reasons
    """
    ela_heatmap, ela_overlay = create_ela_heatmap_overlay(original)
    sam2_overlay = overlay_sam2_mask(original, sam2_mask)

    return {
        "heatmaps": {
            "ela_heatmap_png_base64": _encode_image_to_base64_png(ela_heatmap),
            "ela_overlay_png_base64": _encode_image_to_base64_png(ela_overlay),
            "sam2_overlay_png_base64": _encode_image_to_base64_png(sam2_overlay),
        },
        "fraud_reasons": fraud_reasons,
    }


__all__ = [
    "create_ela_heatmap_overlay",
    "overlay_sam2_mask",
    "build_explainability_payload",
]

