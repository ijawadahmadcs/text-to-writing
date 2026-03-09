"""
Template image analyzer — detects ruled lines, margins, and writing areas
from paper template images (lined notebook, exam sheets, blank paper, etc.)

Returns a TemplateLayout dict:
    {
        "line_positions":  [int, ...],   # y-coordinates of each ruled line
        "margin_left":     int,          # left writing boundary (px)
        "margin_right":    int,          # right writing boundary (px)
        "margin_top":      int,          # top writing boundary (px)
        "margin_bottom":   int,          # bottom writing boundary (px)
        "line_spacing":    int,          # detected spacing between lines (px)
        "has_lines":       bool,         # whether ruled lines were found
        "has_margin_line": bool,         # whether a vertical margin line was found
    }
"""

import io
import statistics
from typing import Any

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_template(image_bytes: bytes) -> dict[str, Any]:
    """Analyze a template image and return layout information."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return _analyze_template_image(img)


def analyze_template_from_path(path: str) -> dict[str, Any]:
    """Analyze a template image from a file path."""
    img = Image.open(path).convert("RGB")
    return _analyze_template_image(img)


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _analyze_template_image(img: Image.Image) -> dict[str, Any]:
    arr = np.array(img)
    h, w, _ = arr.shape

    bg_color = _detect_background_color(arr)
    horizontal_lines = _detect_horizontal_lines(arr, bg_color)
    margin_line_x = _detect_vertical_margin_line(arr, bg_color)

    has_lines = len(horizontal_lines) >= 3
    has_margin = margin_line_x is not None

    # Compute line spacing from detected lines
    if has_lines:
        spacings = [
            horizontal_lines[i + 1] - horizontal_lines[i]
            for i in range(len(horizontal_lines) - 1)
        ]
        line_spacing = int(statistics.median(spacings))
        margin_top = max(0, horizontal_lines[0] - line_spacing // 4)
        margin_bottom = min(h, horizontal_lines[-1] + line_spacing)
    else:
        line_spacing = max(20, int(h * 0.035))
        margin_top = int(h * 0.08)
        margin_bottom = int(h * 0.95)

    if has_margin:
        margin_left = margin_line_x + max(5, int(w * 0.01))
    else:
        margin_left = _detect_content_margin_left(arr, bg_color, w)

    margin_right = _detect_content_margin_right(arr, bg_color, w)

    return {
        "line_positions": horizontal_lines,
        "margin_left": margin_left,
        "margin_right": margin_right,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "line_spacing": line_spacing,
        "has_lines": has_lines,
        "has_margin_line": has_margin,
        "width": w,
        "height": h,
    }


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _detect_background_color(arr: np.ndarray) -> np.ndarray:
    """Estimate the dominant background color (usually white/off-white)."""
    # Sample center region — more likely to be background
    h, w, _ = arr.shape
    center = arr[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    return np.median(center.reshape(-1, 3), axis=0).astype(np.uint8)


def _color_distance(pixel: np.ndarray, ref: np.ndarray) -> float:
    return float(np.sqrt(np.sum((pixel.astype(float) - ref.astype(float)) ** 2)))


def _detect_horizontal_lines(
    arr: np.ndarray, bg_color: np.ndarray, min_line_run_pct: float = 0.25
) -> list[int]:
    """
    Detect horizontal ruled lines by finding rows where a significant
    proportion of pixels differ from the background in a consistent color.
    """
    h, w, _ = arr.shape
    min_run = int(w * min_line_run_pct)

    # Compute per-pixel distance from background
    diff = np.sqrt(np.sum((arr.astype(float) - bg_color.astype(float)) ** 2, axis=2))

    # Threshold: pixels significantly different from background
    threshold = 40.0
    is_line_pixel = diff > threshold

    # For each row, count how many consecutive non-bg pixels there are
    # We look for rows where many pixels in a row are colored (a ruled line)
    row_scores = np.sum(is_line_pixel, axis=1)

    # A ruled line row has a large fraction of colored pixels
    candidate_rows = np.where(row_scores >= min_run)[0]

    if len(candidate_rows) == 0:
        return []

    # Cluster nearby candidate rows into line groups (lines are a few px thick)
    lines: list[int] = []
    group = [candidate_rows[0]]
    for i in range(1, len(candidate_rows)):
        if candidate_rows[i] - candidate_rows[i - 1] <= 3:
            group.append(candidate_rows[i])
        else:
            lines.append(int(np.mean(group)))
            group = [candidate_rows[i]]
    lines.append(int(np.mean(group)))

    # Filter: lines should have roughly consistent spacing
    if len(lines) < 3:
        return lines

    spacings = [lines[i + 1] - lines[i] for i in range(len(lines) - 1)]
    med_spacing = statistics.median(spacings)

    # Keep only lines whose spacing from neighbors is close to median
    filtered = [lines[0]]
    for i in range(1, len(lines)):
        gap = lines[i] - filtered[-1]
        # Allow gap to be 0.5x to 2.0x the median (to handle missing lines)
        if gap >= med_spacing * 0.4:
            filtered.append(lines[i])

    return filtered


def _detect_vertical_margin_line(
    arr: np.ndarray, bg_color: np.ndarray
) -> int | None:
    """
    Detect a vertical margin line (usually red/pink) on the left side.
    Returns the x-coordinate or None if not found.
    """
    h, w, _ = arr.shape

    # Only scan the left 30% of the image
    scan_width = int(w * 0.30)

    # Look for columns with high red content relative to background
    left_region = arr[:, :scan_width, :]

    # Compute redness: high R, low G and B relative to background
    r = left_region[:, :, 0].astype(float)
    g = left_region[:, :, 1].astype(float)
    b = left_region[:, :, 2].astype(float)

    # Red-ish pixels: R is much higher than G and B
    is_reddish = (r > 100) & (r > g + 30) & (r > b + 30)

    # For each column, count reddish pixels
    col_red_count = np.sum(is_reddish, axis=0)

    # A margin line should span most of the page height
    min_vertical_span = int(h * 0.4)

    red_cols = np.where(col_red_count >= min_vertical_span)[0]
    if len(red_cols) == 0:
        # Try a softer approach: look for any colored vertical line
        diff = np.sqrt(
            np.sum((left_region.astype(float) - bg_color.astype(float)) ** 2, axis=2)
        )
        col_scores = np.sum(diff > 50, axis=0)
        colored_cols = np.where(col_scores >= min_vertical_span)[0]
        if len(colored_cols) == 0:
            return None
        # Return rightmost colored column in the cluster
        return int(colored_cols[-1]) if len(colored_cols) < 20 else int(np.median(colored_cols))

    # Return the rightmost red column (right edge of margin line)
    # Cluster them first
    groups: list[list[int]] = [[red_cols[0]]]
    for i in range(1, len(red_cols)):
        if red_cols[i] - red_cols[i - 1] <= 3:
            groups[-1].append(red_cols[i])
        else:
            groups.append([red_cols[i]])

    # Take the group closest to a typical margin (5-20% from left)
    best_group = max(groups, key=lambda g: len(g))
    return int(np.max(best_group))


def _detect_content_margin_left(
    arr: np.ndarray, bg_color: np.ndarray, w: int
) -> int:
    """Fallback: estimate left margin when no vertical line is found."""
    return int(w * 0.08)


def _detect_content_margin_right(
    arr: np.ndarray, bg_color: np.ndarray, w: int
) -> int:
    """Estimate right content boundary."""
    return int(w * 0.95)
