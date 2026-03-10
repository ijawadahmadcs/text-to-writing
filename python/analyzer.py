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

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

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
    pen_type = _extract_pen_type(arr)
    slant_consistency = _extract_slant_consistency(img)
    connectivity = _extract_letter_connectivity(img)
    size_variance = _extract_word_size_variance(img)

    # OpenCV-based analysis if available
    cv_data = {}
    if HAS_OPENCV:
        cv_data = _analyze_with_opencv(raw)

    true_stroke = cv_data.get('true_stroke_width', thickness)
    height_variance = cv_data.get('height_variance', 2.0)

    # Derive jitter params from analysis
    baseline_jitter = max(0.5, min(4.0, height_variance * 0.4 + thickness * 0.1))
    x_jitter = max(0.2, thickness * 0.10)
    rotation_jitter = min(0.06, slant_consistency * 0.5 + 0.01)
    pressure_variance = 0.05 if pen_type == 'ballpoint' else (0.10 if pen_type == 'gel' else 0.15)
    size_jitter_val = min(0.15, size_variance * 0.05)

    return {
        "ink_color": ink_color,
        "stroke_thickness": thickness,
        "slant_deg": slant,
        "char_spacing": spacing * (0.85 if connectivity > 0.5 else 1.0),
        "word_spacing": spacing * 1.1,
        "size_factor": size_factor,
        "baseline_jitter": baseline_jitter,
        "x_jitter": x_jitter,
        "rotation_jitter": rotation_jitter,
        # New fields
        "pressure_variance": pressure_variance,
        "size_jitter": size_jitter_val,
        "line_drift_per_line": 0.0,  # will be randomized at render time
        "connectivity": connectivity,
        "pen_type": pen_type,
        "true_stroke_width": true_stroke,
        "height_variance": height_variance,
        "paragraph_indent": 40,
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
# OpenCV-based stroke analysis
# ---------------------------------------------------------------------------

def _analyze_with_opencv(raw: bytes) -> dict:
    """Use OpenCV for accurate stroke width and character metrics."""
    nparr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}

    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

    # Distance transform → true stroke width
    dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    ink_pixels = dist_transform[dist_transform > 0]
    true_stroke_width = float(np.mean(ink_pixels) * 2) if len(ink_pixels) > 0 else 2.0

    # Connected components → character size stats
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    if num_labels <= 1:
        return {'true_stroke_width': true_stroke_width}

    widths = stats[1:, cv2.CC_STAT_WIDTH]
    heights = stats[1:, cv2.CC_STAT_HEIGHT]

    valid_heights = heights[heights > 5]
    valid_widths = widths[widths > 2]

    avg_char_height = float(np.median(valid_heights)) if len(valid_heights) > 0 else 15.0
    avg_char_width = float(np.median(valid_widths)) if len(valid_widths) > 0 else 8.0
    height_variance = float(np.std(valid_heights)) if len(valid_heights) > 0 else 2.0

    return {
        'true_stroke_width': true_stroke_width,
        'avg_char_height': avg_char_height,
        'avg_char_width': avg_char_width,
        'height_variance': height_variance,
    }


# ---------------------------------------------------------------------------
# New feature extractors
# ---------------------------------------------------------------------------

def _extract_pen_type(arr: np.ndarray) -> str:
    """
    Classify pen type by stroke width variance.
    Ball-point = thin uniform. Gel = medium. Fountain = thick+variable.
    """
    gray = np.mean(arr, axis=2)
    mask = gray < 128
    if mask.sum() < 50:
        return 'ballpoint'

    # Measure run-length variance in horizontal strokes
    row_runs = []
    for row_idx in range(0, mask.shape[0], 3):
        row = mask[row_idx]
        run_len = 0
        for px in row:
            if px:
                run_len += 1
            else:
                if run_len > 1:
                    row_runs.append(run_len)
                run_len = 0

    if not row_runs or len(row_runs) < 10:
        return 'ballpoint'

    run_std = float(np.std(row_runs))
    run_mean = float(np.mean(row_runs))
    cv = run_std / max(run_mean, 1)

    if cv < 0.3:
        return 'ballpoint'
    elif cv < 0.6:
        return 'gel'
    else:
        return 'fountain'


def _extract_slant_consistency(img: Image.Image) -> float:
    """
    Measure how consistent the slant is across the page.
    Returns a value 0 (perfectly consistent) to 1 (chaotic).
    """
    ref_w = 400
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    # Split image into vertical strips, estimate slant in each
    strip_count = 8
    strip_w = mask.shape[1] // strip_count
    slants = []

    for s in range(strip_count):
        strip = mask[:, s * strip_w: (s + 1) * strip_w]
        centroids = []
        for y in range(strip.shape[0]):
            row = strip[y]
            xs = np.where(row)[0]
            if len(xs) > 2:
                centroids.append((y, float(np.mean(xs))))
        if len(centroids) >= 5:
            ys = np.array([c[0] for c in centroids], dtype=float)
            xs = np.array([c[1] for c in centroids], dtype=float)
            n = len(ys)
            denom = n * np.sum(ys ** 2) - np.sum(ys) ** 2 + 1e-9
            slope = (n * np.sum(xs * ys) - np.sum(xs) * np.sum(ys)) / denom
            slants.append(math.degrees(math.atan(slope)))

    if len(slants) < 2:
        return 0.0

    return min(1.0, float(np.std(slants)) / 10.0)


def _extract_letter_connectivity(img: Image.Image) -> float:
    """
    Measure connectivity: 0 = print (many gaps), 1 = cursive (few gaps).
    Looks at horizontal gap frequency between ink blobs.
    """
    ref_w = 800
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    # Sample several horizontal bands in the middle
    h = mask.shape[0]
    mid = h // 2
    band = mask[max(0, mid - 30): mid + 30, :]
    if band.sum() < 20:
        return 0.0

    col_has_ink = band.any(axis=0)

    # Count transitions from ink to no-ink
    transitions = 0
    ink_runs = 0
    in_ink = False
    for v in col_has_ink:
        if v and not in_ink:
            in_ink = True
            ink_runs += 1
        elif not v and in_ink:
            in_ink = False
            transitions += 1

    if ink_runs == 0:
        return 0.0

    # More gaps per ink run = more print-like
    gap_ratio = transitions / max(ink_runs, 1)
    # Invert so higher = more connected (cursive)
    return max(0.0, min(1.0, 1.0 - gap_ratio * 0.3))


def _extract_word_size_variance(img: Image.Image) -> float:
    """
    Track ink blob width variance — larger variance = more size variation.
    Returns normalized variance (0-5 scale).
    """
    ref_w = 800
    ratio = ref_w / img.width
    small = img.resize((ref_w, int(img.height * ratio)), Image.LANCZOS)
    mask = _to_binary(small)

    # Find horizontal ink blobs via run-length encoding on columns
    h = mask.shape[0]
    mid = h // 2
    band = mask[max(0, mid - 40): mid + 40, :]
    col_has_ink = band.any(axis=0)

    blob_widths = []
    run = 0
    for v in col_has_ink:
        if v:
            run += 1
        else:
            if run > 3:
                blob_widths.append(run)
            run = 0

    if len(blob_widths) < 3:
        return 0.0

    return min(5.0, float(np.std(blob_widths)) / max(float(np.mean(blob_widths)), 1.0) * 3.0)


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
        "pressure_variance", "size_jitter", "line_drift_per_line",
        "connectivity", "true_stroke_width", "height_variance",
        "paragraph_indent",
    ]:
        vals = [p[key] for p in profiles if key in p]
        if vals:
            merged[key] = statistics.mean(vals)

    # Pen type: majority vote
    pen_types = [p.get("pen_type", "ballpoint") for p in profiles]
    merged["pen_type"] = max(set(pen_types), key=pen_types.count)

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
        "baseline_jitter": 1.0,
        "x_jitter": 0.3,
        "rotation_jitter": 0.015,
        # New fields
        "pressure_variance": 0.08,
        "size_jitter": 0.0,
        "line_drift_per_line": 0.0,
        "connectivity": 0.0,
        "pen_type": "ballpoint",
        "true_stroke_width": 2.0,
        "height_variance": 2.0,
        "paragraph_indent": 40,
    }
