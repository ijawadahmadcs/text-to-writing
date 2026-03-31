"""
Handwriting generator — renders text onto template images using Pillow,
applying a style profile extracted from handwriting samples.
"""

import io
import math
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTransform

from analyzer import default_profile
from template_analyzer import analyze_template, analyze_template_from_path, analyze_template_v2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "public" / "fonts"
TEMPLATES_DIR = BASE_DIR / "public" / "templates"

# ---------------------------------------------------------------------------
# Font catalogue – maps an index to a .ttf file
# ---------------------------------------------------------------------------
FONT_FILES = [
    # Original bundled fonts (indices 0-3)
    FONTS_DIR / "DancingScript.ttf",
    FONTS_DIR / "IndieFlower.ttf",
    FONTS_DIR / "Caveat.ttf",
    FONTS_DIR / "ArchitectsDaughter.ttf",
    # Font Vault handwriting fonts (indices 4-41)
    FONTS_DIR / "QEAntonyLark.ttf",         # 4
    FONTS_DIR / "QEBEV.ttf",                # 5
    FONTS_DIR / "QEBradenHill.ttf",         # 6
    FONTS_DIR / "QECarolineMutiboko.ttf",   # 7
    FONTS_DIR / "QECursiveVersion.ttf",     # 8
    FONTS_DIR / "QEDaveMergens.ttf",        # 9
    FONTS_DIR / "QEDavidReid.ttf",          # 10
    FONTS_DIR / "QEDavidReidCAP.ttf",       # 11
    FONTS_DIR / "QEDonaldRoss.ttf",         # 12
    FONTS_DIR / "QEDSFont.ttf",             # 13
    FONTS_DIR / "QEGarrettWMoretz.ttf",     # 14
    FONTS_DIR / "QEgeeKzoid.ttf",           # 15
    FONTS_DIR / "QEGHHughes.ttf",           # 16
    FONTS_DIR / "QEHerbertCooper.ttf",      # 17
    FONTS_DIR / "QEJeffDungan.ttf",         # 18
    FONTS_DIR / "QEJER.ttf",               # 19
    FONTS_DIR / "QEJohnCaplin.ttf",         # 20
    FONTS_DIR / "QEJohnWilliams.ttf",       # 21
    FONTS_DIR / "QEJulianDean.ttf",         # 22
    FONTS_DIR / "QEKevinKnowles.ttf",       # 23
    FONTS_DIR / "QEKevinShirley.ttf",       # 24
    FONTS_DIR / "QEKunjarScript.ttf",       # 25
    FONTS_DIR / "QEMamasAndPapas.ttf",      # 26
    FONTS_DIR / "QEPamRosenberry.ttf",      # 27
    FONTS_DIR / "QEPhilipBean.ttf",         # 28
    FONTS_DIR / "QEPhillips.ttf",           # 29
    FONTS_DIR / "QEPrintVersion.ttf",       # 30
    FONTS_DIR / "QERoystonSuch.ttf",        # 31
    FONTS_DIR / "QERoystonSuchCAP.ttf",     # 32
    FONTS_DIR / "QERufus.ttf",              # 33
    FONTS_DIR / "QERuthStafford.ttf",       # 34
    FONTS_DIR / "QESamRoberts.ttf",         # 35
    FONTS_DIR / "QESamRoberts2.ttf",        # 36
    FONTS_DIR / "QEScottWilliams.ttf",      # 37
    FONTS_DIR / "QETimDoremus.ttf",         # 38
    FONTS_DIR / "QETonyFlores.ttf",         # 39
    FONTS_DIR / "QEVRead.ttf",              # 40
    FONTS_DIR / "QEVickyCaulfield.ttf",     # 41
]

FONT_NAMES = [
    "Dancing Script",
    "Indie Flower",
    "Caveat",
    "Architects Daughter",
    "Antony Lark",
    "Beverly Smith",
    "Braden Hill",
    "Caroline Mutiboko",
    "Harriet DeLaughter (Cursive)",
    "David Mergens",
    "David Reid",
    "David Reid (Print)",
    "Donald Ross",
    "DS Font",
    "Garrett Moretz",
    "geeKzoid",
    "George Hughes",
    "Herbert Cooper",
    "Jeff Dungan",
    "Kate Rothrock",
    "John Caplin",
    "John Williams",
    "Julian Dean",
    "Kevin Knowles",
    "Kevin Shirley",
    "Kunjar Bhaduri",
    "Mamas and Papas",
    "Pamela Rosenberry",
    "Philip Bean",
    "William Phillips",
    "Harriet DeLaughter (Print)",
    "Royston Such",
    "Royston Such (Print)",
    "Rufus",
    "Ruth Stafford",
    "Sam Roberts",
    "Sam Roberts (2)",
    "Scott Williams",
    "Tim Doremus",
    "Tony Flores",
    "Valerie Read",
    "Vicky Caulfield",
]

# Built-in template catalogue
BUILTIN_TEMPLATES = {
    "lined": TEMPLATES_DIR / "lined.png",
    "blank": TEMPLATES_DIR / "blank.png",
    "exam": TEMPLATES_DIR / "exam.png",
    "grid": TEMPLATES_DIR / "grid.png",
    "dotted": TEMPLATES_DIR / "dotted.png",
}


def _load_font(font_index: int, size: int) -> ImageFont.FreeTypeFont:
    idx = font_index % len(FONT_FILES)
    path = str(FONT_FILES[idx])
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# Text structure parser
# ---------------------------------------------------------------------------

def parse_text_structure(text: str) -> list[dict]:
    """
    Detect structure from the raw text.
    Returns list of blocks: {type: 'heading'|'body'|'list_item'|'blank', content: str}
    """
    blocks: list[dict] = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            blocks.append({'type': 'blank', 'content': ''})
        elif stripped.startswith('#'):
            heading_text = stripped.lstrip('#').strip()
            if heading_text:
                blocks.append({'type': 'heading', 'content': heading_text})
            else:
                blocks.append({'type': 'blank', 'content': ''})
        elif len(stripped) >= 2 and stripped[0].isdigit() and stripped[1] in '.):' :
            blocks.append({'type': 'list_item', 'content': stripped})
        elif len(stripped) < 60 and stripped.endswith(':'):
            blocks.append({'type': 'heading', 'content': stripped})
        elif stripped.isupper() and len(stripped) < 80:
            blocks.append({'type': 'heading', 'content': stripped})
        else:
            blocks.append({'type': 'body', 'content': stripped})
    return blocks


# ---------------------------------------------------------------------------
# Font baseline calibration
# ---------------------------------------------------------------------------

def _calibrate_font_baseline_offset(font: ImageFont.FreeTypeFont) -> int:
    """
    Find how many pixels below the draw y-origin the actual baseline sits
    for this font. We render 'x' and measure where the bottom of the glyph
    lands relative to the draw position.
    """
    test_img = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(test_img)
    draw.text((10, 10), 'x', font=font, fill='black')
    arr = np.array(test_img)[:, :, 3]  # alpha channel
    ink_rows = np.where(arr.any(axis=1))[0]
    if len(ink_rows):
        return int(ink_rows[-1] - 10)  # distance from y=10 to bottom of 'x'
    return font.size // 2


# ---------------------------------------------------------------------------
# Ink pressure / opacity variation
# ---------------------------------------------------------------------------

def _vary_ink_color(base_rgb: tuple[int, int, int], pressure_variance: float) -> str:
    """
    Slightly darken or lighten the ink colour to simulate pen pressure.
    pressure_variance controls the stddev of the multiplier (e.g. 0.08).
    """
    factor = random.gauss(1.0, pressure_variance)
    r = int(min(255, max(0, base_rgb[0] * (2 - factor))))
    g = int(min(255, max(0, base_rgb[1] * (2 - factor))))
    b = int(min(255, max(0, base_rgb[2] * (2 - factor))))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Natural word gap
# ---------------------------------------------------------------------------

def _natural_word_gap(base_gap: float) -> float:
    """Return a slightly randomized word gap."""
    variance = base_gap * 0.25
    return base_gap + random.gauss(0, variance)


# ---------------------------------------------------------------------------
# Ink smudge artifacts
# ---------------------------------------------------------------------------

def _add_ink_artifacts(img: Image.Image, ink_color: str,
                       line_positions: list[int] | None) -> None:
    """Add tiny random ink dots near line ends to mimic pen resting."""
    if not line_positions:
        return
    draw = ImageDraw.Draw(img)
    w = img.width
    for _ in range(random.randint(0, 3)):
        x = random.randint(50, min(200, w - 10))
        y = random.choice(line_positions) + random.randint(-2, 2)
        r = random.randint(1, 3)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=ink_color)


# ---------------------------------------------------------------------------
# Structured text layout engine
# ---------------------------------------------------------------------------

def _layout_structured_text(
    font: ImageFont.FreeTypeFont,
    heading_font: ImageFont.FreeTypeFont,
    text: str,
    margin_left: int,
    margin_right: int,
    margin_top: int,
    margin_bottom: int,
    line_spacing: int,
    spacing_mul: float,
    line_positions: list[int] | None,
    profile: dict[str, Any],
) -> tuple[list[tuple[str, int, int, str, ImageFont.FreeTypeFont]], str]:
    """
    Layout structured text (headings, body, list items) respecting margins
    and optional ruled-line positions.

    Returns (placements, remaining_text) where each placement is
    (word, x, y, block_type, font_to_use).
    """
    baseline_offset = _calibrate_font_baseline_offset(font)
    heading_baseline_offset = _calibrate_font_baseline_offset(heading_font)
    paragraph_indent = profile.get('paragraph_indent', 40)

    # Build y-positions
    if line_positions:
        y_positions = [
            lp - baseline_offset
            for lp in line_positions
            if margin_top <= lp <= margin_bottom
        ]
        if not y_positions:
            y_positions = list(range(margin_top, margin_bottom, line_spacing))
    else:
        y_positions = list(range(margin_top, margin_bottom, line_spacing))

    # Skip the first line to leave it empty (natural handwriting look)
    if len(y_positions) > 2:
        y_positions = y_positions[1:]

    if not y_positions:
        return [], text

    blocks = parse_text_structure(text)
    placements: list[tuple[str, int, int, str, ImageFont.FreeTypeFont]] = []

    line_idx = 0
    is_paragraph_start = True

    # Line drift
    line_drift = 0.0
    drift_per_line = profile.get('line_drift_per_line', random.gauss(0, 1.5))

    consumed_block_count = 0

    for block in blocks:
        btype = block['type']
        content = block['content']

        if line_idx >= len(y_positions):
            break
        consumed_block_count += 1

        if btype == 'blank':
            # Skip one line for blank
            line_idx += 1
            line_drift += drift_per_line
            line_drift = max(-8, min(8, line_drift))
            is_paragraph_start = True
            continue

        if btype == 'heading':
            # Extra gap before heading
            if placements:
                line_idx += 1
                line_drift += drift_per_line
                line_drift = max(-8, min(8, line_drift))

            if line_idx >= len(y_positions):
                consumed_block_count -= 1
                break

            active_font = heading_font
            y_off = y_positions[line_idx] - heading_baseline_offset + baseline_offset

            words = content.split()
            x = margin_left
            for word in words:
                bbox = active_font.getbbox(word + " ")
                w = int((bbox[2] - bbox[0]) * spacing_mul)
                if x + w > margin_right and x > margin_left:
                    line_idx += 1
                    line_drift += drift_per_line
                    line_drift = max(-8, min(8, line_drift))
                    if line_idx >= len(y_positions):
                        break
                    y_off = y_positions[line_idx] - heading_baseline_offset + baseline_offset
                    x = margin_left
                placements.append((word, x, int(y_off + line_drift), btype, active_font))
                x += w

            # Extra gap after heading
            line_idx += 1
            line_drift += drift_per_line
            line_drift = max(-8, min(8, line_drift))
            is_paragraph_start = True
            continue

        # body or list_item
        active_font = font
        indent = 0
        if btype == 'list_item':
            indent = int(active_font.size * 1.2)
        elif btype == 'body' and is_paragraph_start:
            indent = paragraph_indent

        words = content.split()
        if not words:
            continue

        if line_idx >= len(y_positions):
            consumed_block_count -= 1
            break

        y_current = y_positions[line_idx] + line_drift
        x = margin_left + indent
        first_word_in_block = True

        for wi, word in enumerate(words):
            bbox = active_font.getbbox(word + " ")
            w = int((bbox[2] - bbox[0]) * spacing_mul)

            if x + w > margin_right and not first_word_in_block:
                line_idx += 1
                line_drift += drift_per_line
                line_drift = max(-8, min(8, line_drift))
                if line_idx >= len(y_positions):
                    # Couldn't finish this block; reconstruct remaining
                    remaining_words = words[wi:]
                    remaining_block = {'type': btype, 'content': ' '.join(remaining_words)}
                    remaining_blocks = [remaining_block] + blocks[consumed_block_count:]
                    remaining_text = '\n'.join(
                        b['content'] if b['type'] != 'blank' else ''
                        for b in remaining_blocks
                    )
                    return placements, remaining_text
                y_current = y_positions[line_idx] + line_drift
                x = margin_left  # no indent on continuation lines

            placements.append((word, x, int(y_current), btype, active_font))
            x += w
            first_word_in_block = False

        # Move to next line after block
        line_idx += 1
        line_drift += drift_per_line
        line_drift = max(-8, min(8, line_drift))
        is_paragraph_start = False

    # Build remaining text from unconsumed blocks
    unconsumed = blocks[consumed_block_count:]
    if unconsumed:
        remaining_text = '\n'.join(
            b['content'] if b['type'] != 'blank' else ''
            for b in unconsumed
        )
    else:
        remaining_text = ''

    return placements, remaining_text


def generate_pages(
    text: str,
    template: str = "lined",
    font_index: int = 0,
    font_size: int | None = None,
    line_spacing: int | None = None,
    ink_color: str = "#1a1a2e",
    margin_left_pct: float = 0.12,
    margin_right_pct: float = 0.06,
    margin_top_pct: float = 0.09,
    margin_bottom_pct: float = 0.05,
    enable_heading_bold: bool = True,
    custom_template_bytes: bytes | None = None,
    style_profile: dict[str, Any] | None = None,
) -> list[bytes]:
    """
    Render *text* onto the chosen template and return a list of PNG byte
    buffers (one per page).  The template is analyzed to detect ruled lines,
    margins, and writing areas so text is placed properly on the paper.
    When *style_profile* is provided the renderer adapts ink colour, size,
    spacing, jitter and slant to mimic the analysed handwriting.
    When *enable_heading_bold* is True, detected headings are rendered thicker
    than normal body text.
    """

    profile = style_profile or default_profile()

    # ------------------------------------------------------------------
    # Load template image
    # ------------------------------------------------------------------
    if custom_template_bytes:
        bg = Image.open(io.BytesIO(custom_template_bytes)).convert("RGBA")
        tpl_layout = analyze_template_v2(custom_template_bytes)
    elif template in BUILTIN_TEMPLATES:
        bg = Image.open(BUILTIN_TEMPLATES[template]).convert("RGBA")
        with open(BUILTIN_TEMPLATES[template], 'rb') as f:
            tpl_layout = analyze_template_v2(f.read())
    else:
        bg = Image.new("RGBA", (800, 1100), (255, 255, 255, 255))
        tpl_layout = None

    cw, ch = bg.size

    # ------------------------------------------------------------------
    # Derive layout metrics from template analysis + profile
    # ------------------------------------------------------------------
    scale = cw / 800
    size_mul = profile.get("size_factor", 1.0)
    spacing_mul = profile.get("word_spacing", 1.0)

    if tpl_layout and tpl_layout["has_lines"]:
        # Use detected layout — adapt font size to line spacing
        detected_spacing = tpl_layout["line_spacing"]
        _font_size = font_size or max(12, int(detected_spacing * 0.55 * size_mul))
        _line_spacing = detected_spacing
        ml = tpl_layout["margin_left"]
        mr = tpl_layout["margin_right"]
        mt = tpl_layout["margin_top"]
        mb = tpl_layout["margin_bottom"]
        line_positions = tpl_layout["line_positions"]
    elif tpl_layout:
        # Blank paper — use detected margins but no line snapping
        _font_size = font_size or max(16, int(24 * scale * size_mul))
        _line_spacing = line_spacing or max(20, int(34 * scale * size_mul))
        ml = tpl_layout["margin_left"]
        mr = tpl_layout["margin_right"]
        mt = tpl_layout["margin_top"]
        mb = tpl_layout["margin_bottom"]
        line_positions = None
    else:
        # Fallback: percentage-based margins
        _font_size = font_size or max(16, int(24 * scale * size_mul))
        _line_spacing = line_spacing or max(20, int(34 * scale * size_mul))
        ml = int(cw * margin_left_pct)
        mr = int(cw * (1 - margin_right_pct))
        mt = int(ch * margin_top_pct)
        mb = int(ch * (1 - margin_bottom_pct))
        line_positions = None

    font = _load_font(font_index, _font_size)
    heading_font = _load_font(font_index, int(_font_size * 1.25))

    # Resolve ink colour — prefer profile's analysed colour
    p_ink = profile.get("ink_color")
    if p_ink and style_profile is not None:
        fill_color = _rgb_to_hex(p_ink)
        ink_rgb = tuple(p_ink) if isinstance(p_ink, (list, tuple)) else (26, 26, 46)
    else:
        fill_color = ink_color
        ink_rgb = _hex_to_rgb(ink_color)

    slant_rad = math.radians(profile.get("slant_deg", 0.0))
    y_jitter_std = profile.get("baseline_jitter", 0.5) * scale
    x_jitter_std = profile.get("x_jitter", 0.3) * scale
    rot_jitter_std = profile.get("rotation_jitter", 0.015)
    pressure_var = profile.get("pressure_variance", 0.08)
    size_jitter = profile.get("size_jitter", 0.0)
    char_spacing_mul = profile.get("char_spacing", 1.0)

    # Connectivity: 0 = print, 1 = cursive — tighten spacing for cursive
    connectivity = profile.get("connectivity", 0.0)
    char_spacing_mul *= 1.0 - connectivity * 0.25  # up to 25% tighter

    # ------------------------------------------------------------------
    # Paginate & render
    # ------------------------------------------------------------------
    pages: list[bytes] = []
    remaining = text.strip()

    while remaining:
        page = bg.copy()
        draw = ImageDraw.Draw(page)

        placements, remaining = _layout_structured_text(
            font, heading_font, remaining,
            ml, mr, mt, mb,
            _line_spacing, spacing_mul,
            line_positions, profile,
        )

        # Track pressure changes — new pressure every 3-8 chars
        chars_since_pressure = 0
        current_fill = fill_color
        pressure_interval = random.randint(3, 8)

        for word, wx, wy, btype, active_font in placements:
            # Per-character rendering for natural look
            _draw_word_natural(
                page, word, active_font, ink_rgb, wx, wy,
                y_jitter_std, x_jitter_std, rot_jitter_std,
                slant_rad, pressure_var, size_jitter,
                char_spacing_mul, connectivity,
                bold_strength=3 if (enable_heading_bold and btype == 'heading') else 0,
            )

        # Add ink artifacts for realism
        _add_ink_artifacts(page, fill_color, line_positions)

        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="PNG")
        pages.append(buf.getvalue())

    if not pages:
        buf = io.BytesIO()
        bg.convert("RGB").save(buf, format="PNG")
        pages.append(buf.getvalue())

    return pages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _draw_char(
    img: Image.Image,
    char: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    x: float,
    y: float,
    rotation: float,
):
    """Render a single character with rotation onto the page."""
    if abs(rotation) < 0.005:
        draw = ImageDraw.Draw(img)
        draw.text((x, y), char, font=font, fill=fill)
        return

    bbox = font.getbbox(char)
    tw = max(1, bbox[2] - bbox[0] + 4)
    th = max(1, bbox[3] - bbox[1] + 4)
    patch = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(patch)
    pdraw.text((-bbox[0] + 2, -bbox[1] + 2), char, font=font, fill=fill)
    rotated = patch.rotate(-math.degrees(rotation), expand=True,
                           resample=Image.BICUBIC)
    ix, iy = int(x), int(y + bbox[1])
    # Bounds check
    if 0 <= ix < img.width and 0 <= iy < img.height:
        img.paste(rotated, (ix, iy), rotated)


def _draw_word_natural(
    img: Image.Image,
    word: str,
    font: ImageFont.FreeTypeFont,
    ink_rgb: tuple[int, int, int],
    x: float,
    y: float,
    y_jitter_std: float,
    x_jitter_std: float,
    rot_jitter_std: float,
    slant_rad: float,
    pressure_variance: float,
    size_jitter: float,
    char_spacing_mul: float,
    connectivity: float = 0.0,
    bold_strength: int = 0,
):
    """
    Render a word character-by-character with independent per-character
    jitter, pressure variation, and micro-rotation for natural handwriting.
    Connectivity (0=print, 1=cursive) reduces inter-char jitter for
    more fluid connected strokes.
    """
    char_x = x
    chars_since_pressure = 0
    pressure_interval = random.randint(3, 8)
    current_fill = _vary_ink_color(ink_rgb, pressure_variance)

    # Dampen per-char jitter for cursive styles
    jitter_dampen = 1.0 - connectivity * 0.5

    for char in word:
        # Per-character micro-jitter (reduced for cursive)
        dy = random.gauss(0, y_jitter_std * jitter_dampen)
        dx = random.gauss(0, x_jitter_std * 0.3 * jitter_dampen)
        angle = slant_rad + random.gauss(0, rot_jitter_std)

        # Pressure change every few characters
        chars_since_pressure += 1
        if chars_since_pressure >= pressure_interval:
            current_fill = _vary_ink_color(ink_rgb, pressure_variance)
            chars_since_pressure = 0
            pressure_interval = random.randint(3, 8)

        _draw_char(img, char, font, current_fill,
                   char_x + dx, y + dy, angle)

        if bold_strength > 0:
            # Synthetic bold: tiny extra strokes around the same glyph.
            _draw_char(img, char, font, current_fill,
                       char_x + dx + 0.35, y + dy, angle)
            _draw_char(img, char, font, current_fill,
                       char_x + dx, y + dy + 0.25, angle)
            if bold_strength > 2:
                _draw_char(img, char, font, current_fill,
                           char_x + dx + 0.25, y + dy + 0.2, angle)

        bbox = font.getbbox(char)
        char_width = (bbox[2] - bbox[0]) * char_spacing_mul
        char_x += char_width

    # Add a natural word gap after the word
    space_bbox = font.getbbox(' ')
    space_width = (space_bbox[2] - space_bbox[0]) * char_spacing_mul
    return char_x + _natural_word_gap(space_width)
