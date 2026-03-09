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

from PIL import Image, ImageDraw, ImageFont, ImageTransform

from analyzer import default_profile
from template_analyzer import analyze_template, analyze_template_from_path

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


def _wrap_text_on_template(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    margin_left: int,
    margin_right: int,
    margin_top: int,
    margin_bottom: int,
    line_spacing: int,
    canvas_width: int,
    canvas_height: int,
    spacing_mul: float = 1.0,
    line_positions: list[int] | None = None,
):
    """
    Word-wrap *text* within the given margins and return a list of
    (word, x, y) tuples for one page, plus the remaining words.

    When *line_positions* is provided, text is snapped to detected
    ruled-line y-coordinates for proper alignment with the template.
    """
    words = text.split()
    placements: list[tuple[str, int, int]] = []

    x = margin_left

    # Build the list of y-positions to write on
    if line_positions:
        # Use detected line positions, offset text slightly above each line
        font_bbox = font.getbbox("Ay")
        font_ascent = font_bbox[3] - font_bbox[1]
        y_positions = [
            lp - font_ascent
            for lp in line_positions
            if margin_top <= lp <= margin_bottom
        ]
        if not y_positions:
            y_positions = list(range(margin_top, margin_bottom, line_spacing))
    else:
        y_positions = list(range(margin_top, margin_bottom, line_spacing))

    line_idx = 0
    if line_idx >= len(y_positions):
        return placements, text

    y = y_positions[line_idx]

    remaining_words: list[str] = []
    for i, word in enumerate(words):
        bbox = font.getbbox(word + " ")
        w = int((bbox[2] - bbox[0]) * spacing_mul)

        if x + w > margin_right:
            # Move to next line
            line_idx += 1
            if line_idx >= len(y_positions):
                remaining_words = words[i:]
                break
            x = margin_left
            y = y_positions[line_idx]

        placements.append((word, x, y))
        x += w

    return placements, " ".join(remaining_words)


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
    custom_template_bytes: bytes | None = None,
    style_profile: dict[str, Any] | None = None,
) -> list[bytes]:
    """
    Render *text* onto the chosen template and return a list of PNG byte
    buffers (one per page).  The template is analyzed to detect ruled lines,
    margins, and writing areas so text is placed properly on the paper.
    When *style_profile* is provided the renderer adapts ink colour, size,
    spacing, jitter and slant to mimic the analysed handwriting.
    """

    profile = style_profile or default_profile()

    # ------------------------------------------------------------------
    # Load template image
    # ------------------------------------------------------------------
    if custom_template_bytes:
        bg = Image.open(io.BytesIO(custom_template_bytes)).convert("RGBA")
        tpl_layout = analyze_template(custom_template_bytes)
    elif template in BUILTIN_TEMPLATES:
        bg = Image.open(BUILTIN_TEMPLATES[template]).convert("RGBA")
        tpl_layout = analyze_template_from_path(str(BUILTIN_TEMPLATES[template]))
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

    # Resolve ink colour — prefer profile's analysed colour
    p_ink = profile.get("ink_color")
    if p_ink and style_profile is not None:
        fill_color = _rgb_to_hex(p_ink)
    else:
        fill_color = ink_color

    slant_rad = math.radians(profile.get("slant_deg", 0.0))
    y_jitter_std = profile.get("baseline_jitter", 0.5) * scale
    x_jitter_std = profile.get("x_jitter", 0.3) * scale
    rot_jitter_std = profile.get("rotation_jitter", 0.015)

    # ------------------------------------------------------------------
    # Paginate & render
    # ------------------------------------------------------------------
    pages: list[bytes] = []
    remaining = text.strip()

    while remaining:
        page = bg.copy()
        draw = ImageDraw.Draw(page)

        placements, remaining = _wrap_text_on_template(
            draw, remaining, font, ml, mr, mt, mb,
            _line_spacing, cw, ch, spacing_mul,
            line_positions=line_positions,
        )

        for word, wx, wy in placements:
            jx = random.gauss(0, x_jitter_std)
            jy = random.gauss(0, y_jitter_std)
            rot = slant_rad + random.gauss(0, rot_jitter_std)

            _draw_word(page, draw, word, font, fill_color,
                       wx + jx, wy + jy, rot)

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


def _draw_word(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    word: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    x: float,
    y: float,
    rotation: float,
):
    """Render a single word with rotation onto the page."""
    if abs(rotation) < 0.005:
        # fast path — no rotation needed
        draw.text((x, y), word, font=font, fill=fill)
        return

    # Render word onto a small transparent patch, rotate, paste
    bbox = font.getbbox(word)
    tw = bbox[2] - bbox[0] + 4
    th = bbox[3] - bbox[1] + 4
    patch = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(patch)
    pdraw.text((-bbox[0] + 2, -bbox[1] + 2), word, font=font, fill=fill)
    rotated = patch.rotate(-math.degrees(rotation), expand=True,
                           resample=Image.BICUBIC)
    ix, iy = int(x), int(y + bbox[1])
    img.paste(rotated, (ix, iy), rotated)
