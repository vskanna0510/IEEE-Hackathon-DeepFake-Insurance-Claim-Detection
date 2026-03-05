from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image
from scipy import fftpack


def _pil_to_cv2(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def compute_ela(image: Image.Image, quality: int = 95) -> Tuple[Image.Image, float]:
    """
    Perform Error Level Analysis (ELA) on the given image.

    Returns:
        ela_image: PIL Image representing error levels as intensities.
        ela_score: normalized mean ELA intensity in [0, 1].
    """
    # Save to JPEG and reload to introduce compression artifacts
    import io

    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    ela_array = np.abs(np.asarray(image, dtype=np.float32) - np.asarray(recompressed, dtype=np.float32))
    # Normalize and enhance for visualization
    scale = 255.0 / max(ela_array.max(), 1.0)
    ela_array = np.clip(ela_array * scale, 0, 255).astype(np.uint8)
    ela_image = Image.fromarray(ela_array)

    # ELA score as normalized mean intensity
    ela_gray = cv2.cvtColor(ela_array, cv2.COLOR_RGB2GRAY)
    mean_intensity = float(np.mean(ela_gray))
    ela_score = mean_intensity / 255.0

    return ela_image, ela_score


def compute_noise_variance(image: Image.Image) -> float:
    """
    Estimate global noise variance using a Laplacian-based metric.
    Returns a value in [0, 1] (heuristically clipped).
    """
    img_cv = _pil_to_cv2(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    var = lap.var()

    # Normalize using a soft saturation (assuming 0-5000 typical range)
    norm = var / 5000.0
    return float(max(0.0, min(1.0, norm)))


def compute_copy_move_score(
    image: Image.Image,
    block_size: int = 16,
    step: int = 8,
    max_blocks: int = 2000,
) -> float:
    """
    Naive DCT-based copy-move forgery detection.

    Strategy:
    - Extract overlapping blocks.
    - Compute 2D DCT of each block and keep low-frequency coefficients.
    - Compare blocks by cosine similarity of DCT descriptors.
    - High number of highly similar non-overlapping blocks indicates potential copy-move.

    Returns a score in [0, 1] where higher means more likely copy-move artifacts.
    """
    img_cv = _pil_to_cv2(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    descriptors: list[np.ndarray] = []
    locations: list[tuple[int, int]] = []

    for y in range(0, h - block_size + 1, step):
        for x in range(0, w - block_size + 1, step):
            block = gray[y : y + block_size, x : x + block_size].astype(np.float32)
            dct = fftpack.dct(fftpack.dct(block.T, norm="ortho").T, norm="ortho")
            # Take top-left 8x8 low-frequency coefficients and flatten
            desc = dct[:8, :8].flatten()
            desc /= np.linalg.norm(desc) + 1e-6
            descriptors.append(desc)
            locations.append((y, x))

    num_blocks = len(descriptors)
    if num_blocks < 2:
        return 0.0

    # To avoid huge memory usage on large images, subsample blocks if necessary.
    if num_blocks > max_blocks:
        rng = np.random.default_rng(42)
        indices = rng.choice(num_blocks, size=max_blocks, replace=False)
        descriptors = [descriptors[i] for i in indices]
        locations = [locations[i] for i in indices]
        num_blocks = max_blocks

    descriptors_arr = np.vstack(descriptors).astype(np.float32)
    # Compute cosine similarity matrix efficiently for the reduced set
    sim_matrix = descriptors_arr @ descriptors_arr.T
    # Ignore self-similarity
    np.fill_diagonal(sim_matrix, 0.0)

    # Consider only pairs that are not overlapping (distance greater than block_size)
    suspicious_pairs = 0
    total_pairs = 0
    threshold = 0.98

    n = len(locations)
    for i in range(n):
        y1, x1 = locations[i]
        for j in range(i + 1, n):
            y2, x2 = locations[j]
            if abs(y1 - y2) < block_size and abs(x1 - x2) < block_size:
                continue
            total_pairs += 1
            if sim_matrix[i, j] > threshold:
                suspicious_pairs += 1

    if total_pairs == 0:
        return 0.0

    # Normalize suspicious pair ratio to [0, 1]
    ratio = suspicious_pairs / total_pairs
    ratio = max(0.0, min(1.0, ratio * 10.0))  # amplify modest signals
    return float(ratio)


def compute_ela_features(image: Image.Image) -> Dict[str, float]:
    """
    Convenience helper returning all ELA-related scores.
    """
    _, ela_score = compute_ela(image)
    noise_var = compute_noise_variance(image)
    copy_move = compute_copy_move_score(image)
    # Aggregate a simple region-independent ELA score
    combined = (ela_score * 0.5) + (noise_var * 0.3) + (copy_move * 0.2)
    return {
        "ela_score": float(max(0.0, min(1.0, combined))),
        "global_ela_intensity": float(ela_score),
        "noise_variance": float(noise_var),
        "copy_move_score": float(copy_move),
    }


__all__ = [
    "compute_ela",
    "compute_noise_variance",
    "compute_copy_move_score",
    "compute_ela_features",
]

