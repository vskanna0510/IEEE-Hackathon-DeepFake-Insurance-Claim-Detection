import io
from typing import Any, Dict, Tuple

import piexif
from PIL import Image, ImageOps


def load_image(file_bytes: bytes) -> Image.Image:
    """
    Load an image from raw bytes and normalize orientation.
    """
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    # Normalize orientation using EXIF if present
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        # If anything goes wrong, fall back to the original image
        pass
    return image


def extract_exif(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract EXIF metadata from the provided image bytes.

    Returns a nested dictionary with human-readable EXIF tags where possible.
    """
    try:
        exif_dict = piexif.load(file_bytes)
    except Exception:
        return {}

    parsed: Dict[str, Any] = {}
    for ifd_name, ifd_data in exif_dict.items():
        if not isinstance(ifd_data, dict):
            continue
        section: Dict[str, Any] = {}
        for tag_id, value in ifd_data.items():
            try:
                tag_name = piexif.TAGS[ifd_name][tag_id]["name"]
            except Exception:
                tag_name = str(tag_id)

            # Decode bytes where possible for readability
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="ignore")
                except Exception:
                    value = repr(value)
            section[tag_name] = value
        if section:
            parsed[ifd_name] = section
    return parsed


def compute_metadata_score(exif_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Compute a heuristic EXIF-based fraud score in range [0, 1].

    The score represents how *consistent* the metadata looks; higher is less suspicious.

    Heuristics:
    - Presence of core fields (DateTimeOriginal, Make, Model, Orientation)
    - Absence of signs of editing software
    - Reasonable DateTimeOriginal
    """
    if not exif_data:
        # Missing EXIF is mildly suspicious but not definitive
        return 0.4, {"reason": "No EXIF metadata found"}

    flat: Dict[str, Any] = {}
    for section in exif_data.values():
        flat.update(section)

    score_components = []
    reasons = []

    # Core camera fields
    core_fields = ["DateTimeOriginal", "Make", "Model", "Orientation"]
    present_core = sum(1 for f in core_fields if f in flat)
    core_score = present_core / len(core_fields)
    score_components.append(core_score * 0.4)
    if present_core < len(core_fields) // 2:
        reasons.append("Missing core camera metadata fields")

    # Editing software indicators
    software = str(flat.get("Software", "")).lower()
    processing_software = str(flat.get("ProcessingSoftware", "")).lower()
    editor_keywords = ["photoshop", "gimp", "lightroom", "snapseed", "pixlr", "canva"]
    edited_flag = any(k in software or k in processing_software for k in editor_keywords)

    if edited_flag:
        score_components.append(-0.2)
        reasons.append("Image appears to have been edited (Software tag present)")
    else:
        score_components.append(0.1)

    # DateTime sanity (very naive; just presence)
    if "DateTimeOriginal" in flat or "DateTimeDigitized" in flat:
        score_components.append(0.2)
    else:
        reasons.append("No original capture timestamp in EXIF")

    # Clamp and normalize to [0, 1]
    raw_score = sum(score_components)
    raw_score = max(0.0, min(1.0, raw_score))

    details = {
        "core_fields_present": present_core,
        "total_core_fields": len(core_fields),
        "edited_software_detected": edited_flag,
        "reasons": reasons,
    }
    return raw_score, details


__all__ = ["load_image", "extract_exif", "compute_metadata_score"]

