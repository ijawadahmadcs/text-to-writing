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


# ---------------------------------------------------------------------------
# Advanced layout detection
# ---------------------------------------------------------------------------

def _detect_header_region(arr: np.ndarray, bg_color: np.ndarray) -> int | None:
    """
    Detect a header box (common in exam sheets) — a large rectangle near
    the top of the page.  Returns the y-coordinate of the header bottom,
    or None if no header is found.

    Only triggers when there is an anomalously large gap between two
    horizontal lines (indicating a box interior, e.g. name/date fields).
    Regular ruled lines are ignored so they aren't mistaken for a header.
    """
    h, w, _ = arr.shape
    scan_h = int(h * 0.30)
    top_region = arr[:scan_h, :, :]

    diff = np.sqrt(
        np.sum((top_region.astype(float) - bg_color.astype(float)) ** 2, axis=2)
    )
    is_line_pixel = diff > 40

    row_scores = np.sum(is_line_pixel, axis=1)
    min_run = int(w * 0.3)
    candidate_rows = np.where(row_scores >= min_run)[0]

    if len(candidate_rows) < 2:
        return None

    groups: list[list[int]] = [[candidate_rows[0]]]
    for i in range(1, len(candidate_rows)):
        if candidate_rows[i] - candidate_rows[i - 1] <= 5:
            groups[-1].append(candidate_rows[i])
        else:
            groups.append([candidate_rows[i]])

    if len(groups) < 2:
        return None

    group_centers = [int(np.mean(g)) for g in groups]
    spacings = [
        group_centers[i + 1] - group_centers[i]
        for i in range(len(group_centers) - 1)
    ]
    if not spacings:
        return None

    med_sp = statistics.median(spacings)

    # A real header box has an anomalously large gap (its interior).
    # If all spacings are roughly equal (ruled lines), there is no header.
    header_limit = int(h * 0.25)
    for i, sp in enumerate(spacings):
        if sp >= med_sp * 2.5 and group_centers[i + 1] <= header_limit:
            return group_centers[i + 1]

    return None


def _detect_hole_punches(arr: np.ndarray, bg_color: np.ndarray) -> int | None:
    """
    Detect hole punches on the left edge of the paper.
    Hole punches appear as dark circles near x=0.
    Returns the rightmost x-coordinate to avoid, or None.
    """
    h, w, _ = arr.shape
    # Only scan left 8% of the image
    scan_w = max(10, int(w * 0.08))
    left_strip = arr[:, :scan_w, :]

    diff = np.sqrt(
        np.sum((left_strip.astype(float) - bg_color.astype(float)) ** 2, axis=2)
    )
    # Hole punches are dark circles — check for concentrated dark spots
    is_dark = diff > 60
    col_dark_count = np.sum(is_dark, axis=0)

    # A hole punch creates a vertical column with many dark pixels
    min_dark = int(h * 0.01)  # at least 1% of page height
    dark_cols = np.where(col_dark_count >= min_dark)[0]

    if len(dark_cols) == 0:
        return None

    return int(np.max(dark_cols))


def _detect_footer_region(arr: np.ndarray, bg_color: np.ndarray) -> int | None:
    """
    Detect a footer area at the bottom of the page.
    Returns the y-coordinate of the footer top, or None.

    Only triggers when there is an anomalously large gap between horizontal
    lines in the bottom region (indicating a separator before a footer box).
    Regular ruled lines are not treated as a footer.
    """
    h, w, _ = arr.shape
    scan_start = int(h * 0.80)
    bottom_region = arr[scan_start:, :, :]

    diff = np.sqrt(
        np.sum((bottom_region.astype(float) - bg_color.astype(float)) ** 2, axis=2)
    )
    is_line_pixel = diff > 40
    row_scores = np.sum(is_line_pixel, axis=1)
    min_run = int(w * 0.3)
    candidate_rows = np.where(row_scores >= min_run)[0]

    if len(candidate_rows) < 2:
        return None

    groups: list[list[int]] = [[candidate_rows[0]]]
    for i in range(1, len(candidate_rows)):
        if candidate_rows[i] - candidate_rows[i - 1] <= 5:
            groups[-1].append(candidate_rows[i])
        else:
            groups.append([candidate_rows[i]])

    if len(groups) < 2:
        return None

    group_centers = [int(np.mean(g)) for g in groups]
    spacings = [
        group_centers[i + 1] - group_centers[i]
        for i in range(len(group_centers) - 1)
    ]
    if not spacings:
        return None

    med_sp = statistics.median(spacings)

    # A real footer region has an anomalously large gap before it
    # (separating content from a footer box).  Evenly-spaced ruled
    # lines reaching the bottom are normal and not a footer.
    for i, sp in enumerate(spacings):
        if sp >= med_sp * 2.5:
            return scan_start + group_centers[i + 1]

    return None


def analyze_template_v2(image_bytes: bytes) -> dict[str, Any]:
    """
    Enhanced template analysis that accounts for header zones,
    hole punches, and footer regions.
    """
    layout = analyze_template(image_bytes)
    base_margin_top = layout['margin_top']
    base_margin_bottom = layout['margin_bottom']
    base_line_count = len(layout.get('line_positions', []))

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)
    bg_color = _detect_background_color(arr)

    # Detect header box
    header_bottom = _detect_header_region(arr, bg_color)
    if header_bottom:
        layout['margin_top'] = max(layout['margin_top'], header_bottom + 20)

    # Detect hole punches
    hole_punch_x = _detect_hole_punches(arr, bg_color)
    if hole_punch_x:
        layout['margin_left'] = max(layout['margin_left'], hole_punch_x + 15)

    # Detect footer
    footer_top = _detect_footer_region(arr, bg_color)
    if footer_top:
        layout['margin_bottom'] = min(layout['margin_bottom'], footer_top - 20)

    # Filter line positions to respect updated margins
    if layout.get('line_positions'):
        layout['line_positions'] = [
            lp for lp in layout['line_positions']
            if layout['margin_top'] <= lp <= layout['margin_bottom']
        ]

        # Safety: if v2 adjustments eliminated more than 30% of lines,
        # the detection was likely a false positive — revert margins.
        if base_line_count > 0 and len(layout['line_positions']) < base_line_count * 0.7:
            layout['margin_top'] = base_margin_top
            layout['margin_bottom'] = base_margin_bottom
            layout['line_positions'] = [
                lp for lp in layout['line_positions']
                if layout['margin_top'] <= lp <= layout['margin_bottom']
            ]
            # Re-derive from original base analysis lines
            full_layout = analyze_template(image_bytes)
            layout['line_positions'] = full_layout['line_positions']

    return layout
