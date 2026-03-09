"""
Handwriting style analyzer — extracts visual characteristics from sample images.

Given 1-3 photos of handwriting, this module computes a **style profile** dict:
    {
        "ink_color":        (R, G, B),      # dominant ink colour
        "stroke_thickness": float,           # avg stroke width in px (at ref 800w)
        "slant_deg":        float,           # average slant in degrees (0 = upright)
        "char_spacing":     float,           # multiplier for inter-char gap (1.0 = normal)
        "word_spacing":     float,           # multiplier for inter-word gap (1.0 = normal)
        "size_factor":      float,           # multiplier for font size (1.0 = default)
        "baseline_jitter":  float,           # std-dev of y-offset (naturalness)
        "x_jitter":         float,           # std-dev of x-offset
        "rotation_jitter":  float,           # std-dev of rotation in radians
    }

All values are normalized so the renderer can apply them regardless of template
resolution.
"""

import io
import math
import statistics
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, ImageStat

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_samples(sample_bytes_list: list[bytes]) -> dict[str, Any]:
    """
    Analyze one or more handwriting sample images and return a style profile.
    """
    profiles = [_analyze_single(b) for b in sample_bytes_list]
    return _merge_profiles(profiles)


# ---------------------------------------------------------------------------
# Single-image analysis
# ---------------------------------------------------------------------------

def _analyze_single(raw: bytes) -> dict[str, Any]:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.array(img)

    ink_color = _extract_ink_color(arr)
    thickness = _estimate_stroke_thickness(img)
    slant = _estimate_slant(img)
    size_factor, spacing = _estimate_size_and_spacing(img)

    return {
        "ink_color": ink_color,
        "stroke_thickness": thickness,
        "slant_deg": slant,
        "char_spacing": spacing,
        "word_spacing": spacing * 1.1,
        "size_factor": size_factor,
        "baseline_jitter": max(0.3, thickness * 0.15),
        "x_jitter": max(0.2, thickness * 0.10),
        "rotation_jitter": min(0.04, abs(slant) * 0.002 + 0.01),
    }


# ---------------------------------------------------------------------------
# Feature extractors
# ---------------------------------------------------------------------------

def _extract_ink_color(arr: np.ndarray) -> tuple[int, int, int]:
    """
    Find the dominant dark color (the ink) by looking at the darkest 15%
    of pixels.
    """
    # Luminance
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    threshold = np.percentile(lum, 15)
    mask = lum <= threshold

    if mask.sum() < 10:
        return (26, 26, 46)  # fallback dark navy

    dark_pixels = arr[mask]
    r = int(np.median(dark_pixels[:, 0]))
    g = int(np.median(dark_pixels[:, 1]))
    b = int(np.median(dark_pixels[:, 2]))
    return (r, g, b)


def _to_binary(img: Image.Image, threshold: int = 128) -> np.ndarray:
    """Convert to a binary mask (True = ink)."""
    gray = np.array(img.convert("L"))
    return gray < threshold


def _estimate_stroke_thickness(img: Image.Image) -> float:
    """
    Estimate average stroke width by measuring distance-transform peak on
    the ink mask, normalized to an 800px-wide reference.
    """
    # Resize to reference width for consistency
    ref_w = 800
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    if mask.sum() < 50:
        return 2.0  # fallback

    # Simple approach: count ink-rows and ink-cols to estimate average run length
    row_runs = []
    for row in mask:
        in_run = False
        run_len = 0
        for px in row:
            if px:
                in_run = True
                run_len += 1
            else:
                if in_run and run_len > 1:
                    row_runs.append(run_len)
                in_run = False
                run_len = 0

    if not row_runs:
        return 2.0
    return float(np.median(row_runs))


def _estimate_slant(img: Image.Image) -> float:
    """
    Estimate overall slant by looking at vertical ink-column center shifts.
    Returns degrees (positive = leans right).
    """
    ref_w = 400
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    # For each row with ink, compute the centroid x
    centroids = []
    for y in range(mask.shape[0]):
        row = mask[y]
        xs = np.where(row)[0]
        if len(xs) > 5:
            centroids.append((y, float(np.mean(xs))))

    if len(centroids) < 10:
        return 0.0

    # Fit a line through (y, centroid_x) to get slope
    ys = np.array([c[0] for c in centroids], dtype=float)
    xs = np.array([c[1] for c in centroids], dtype=float)
    # Linear regression
    n = len(ys)
    slope = (n * np.sum(xs * ys) - np.sum(xs) * np.sum(ys)) / (
        n * np.sum(ys ** 2) - np.sum(ys) ** 2 + 1e-9
    )
    angle_deg = math.degrees(math.atan(slope))
    # Clamp to reasonable range
    return max(-15.0, min(15.0, angle_deg))


def _estimate_size_and_spacing(img: Image.Image) -> tuple[float, float]:
    """
    Estimate relative letter size and spacing by looking at ink density
    and horizontal gap distribution.
    """
    ref_w = 800
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    ink_ratio = mask.sum() / mask.size if mask.size > 0 else 0.05

    # More ink → bigger / tighter writing, less ink → smaller / spacious
    # Map ink_ratio (typically 0.02–0.15) to size_factor (0.8–1.4)
    size_factor = 0.8 + (ink_ratio - 0.02) / 0.13 * 0.6
    size_factor = max(0.7, min(1.5, size_factor))

    # Estimate horizontal spacing from gap runs
    mid_y = mask.shape[0] // 2
    band = mask[max(0, mid_y - 20): mid_y + 20, :]
    col_has_ink = band.any(axis=0)

    gap_runs = []
    run = 0
    for v in col_has_ink:
        if not v:
            run += 1
        else:
            if run > 2:
                gap_runs.append(run)
            run = 0

    if gap_runs:
        avg_gap = float(np.mean(gap_runs))
        # Normalize: typical gap ~15px at 800w → spacing 1.0
        spacing = avg_gap / 15.0
        spacing = max(0.6, min(1.8, spacing))
    else:
        spacing = 1.0

    return size_factor, spacing


# ---------------------------------------------------------------------------
# Merge multiple profiles
# ---------------------------------------------------------------------------

def _merge_profiles(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    if not profiles:
        return default_profile()
    if len(profiles) == 1:
        return profiles[0]

    # Average numeric fields, median for color
    merged: dict[str, Any] = {}
    r = int(statistics.median(p["ink_color"][0] for p in profiles))
    g = int(statistics.median(p["ink_color"][1] for p in profiles))
    b = int(statistics.median(p["ink_color"][2] for p in profiles))
    merged["ink_color"] = (r, g, b)

    for key in [
        "stroke_thickness", "slant_deg", "char_spacing", "word_spacing",
        "size_factor", "baseline_jitter", "x_jitter", "rotation_jitter",
    ]:
        merged[key] = statistics.mean(p[key] for p in profiles)

    return merged


def default_profile() -> dict[str, Any]:
    """Fallback profile when no samples are provided."""
    return {
        "ink_color": (26, 26, 46),
        "stroke_thickness": 2.0,
        "slant_deg": 0.0,
        "char_spacing": 1.0,
        "word_spacing": 1.0,
        "size_factor": 1.0,
        "baseline_jitter": 0.5,
        "x_jitter": 0.3,
        "rotation_jitter": 0.015,
    }
