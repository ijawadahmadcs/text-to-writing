"""
Generate high-quality paper templates at A4 ratio (2480 × 3508 px, 300 DPI).

Templates:
  1. lined        — classic ruled notebook paper (blue lines, red margin)
  2. blank        — clean white paper with subtle border
  3. exam         — exam/answer sheet with header area and numbered lines
  4. grid         — graph/grid paper (engineering style)
  5. dotted       — dot-grid paper (bullet journal style)
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public" / "templates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# A4 at 300 DPI
W, H = 2480, 3508


def _subtle_paper_texture(img: Image.Image, seed: int = 42) -> Image.Image:
    """Add a very subtle warm-paper tint — no noise, just a gentle fill."""
    overlay = Image.new("RGBA", img.size, (252, 249, 242, 18))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


# -----------------------------------------------------------------------
# 1. Lined Notebook
# -----------------------------------------------------------------------
def generate_lined():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    img = _subtle_paper_texture(img)
    draw = ImageDraw.Draw(img)

    margin_left = 260  # ~10.5% from left
    line_spacing = 88  # ~30 lines per page
    first_line_y = 300  # start below top margin
    line_color = (180, 210, 240)       # soft blue
    margin_color = (230, 140, 140)     # soft red

    # Horizontal ruled lines
    y = first_line_y
    while y < H - 200:
        draw.line([(100, y), (W - 100, y)], fill=line_color, width=2)
        y += line_spacing

    # Vertical margin line
    draw.line([(margin_left, 100), (margin_left, H - 100)], fill=margin_color, width=3)

    # Three hole punches (left edge)
    holes = [H // 4, H // 2, 3 * H // 4]
    for hy in holes:
        draw.ellipse(
            [(50, hy - 30), (110, hy + 30)],
            fill=(240, 240, 240), outline=(200, 200, 200), width=2,
        )

    out = img.convert("RGB")
    out.save(OUTPUT_DIR / "lined.png", "PNG", dpi=(300, 300))
    print(f"  ✓ lined.png  ({W}×{H})")


# -----------------------------------------------------------------------
# 2. Blank Paper
# -----------------------------------------------------------------------
def generate_blank():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    img = _subtle_paper_texture(img)
    draw = ImageDraw.Draw(img)

    # Very faint border
    draw.rectangle(
        [(80, 80), (W - 80, H - 80)],
        outline=(230, 230, 230), width=2,
    )

    out = img.convert("RGB")
    out.save(OUTPUT_DIR / "blank.png", "PNG", dpi=(300, 300))
    print(f"  ✓ blank.png  ({W}×{H})")


# -----------------------------------------------------------------------
# 3. Exam / Answer Sheet
# -----------------------------------------------------------------------
def generate_exam():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    img = _subtle_paper_texture(img)
    draw = ImageDraw.Draw(img)

    line_color = (190, 190, 190)
    margin_color = (210, 150, 150)

    # Header area
    draw.rectangle([(100, 80), (W - 100, 380)], outline=(180, 180, 180), width=3)

    # Header fields
    try:
        hdr_font = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        hdr_font = ImageFont.load_default()

    fields = [
        ("Name: ___________________________________", 160, 120),
        ("Date: __________________    Subject: _______________________", 160, 200),
        ("Roll No: _______________    Section: _______________________", 160, 280),
    ]
    for text, fx, fy in fields:
        draw.text((fx, fy), text, fill=(100, 100, 100), font=hdr_font)

    # Ruled lines below header
    line_spacing = 88
    first_line_y = 480
    y = first_line_y
    while y < H - 200:
        draw.line([(140, y), (W - 140, y)], fill=line_color, width=2)
        y += line_spacing

    # Left margin line
    draw.line([(240, 400), (240, H - 100)], fill=margin_color, width=3)

    # Outer border
    draw.rectangle([(80, 60), (W - 80, H - 60)], outline=(160, 160, 160), width=4)

    out = img.convert("RGB")
    out.save(OUTPUT_DIR / "exam.png", "PNG", dpi=(300, 300))
    print(f"  ✓ exam.png   ({W}×{H})")


# -----------------------------------------------------------------------
# 4. Grid / Graph Paper
# -----------------------------------------------------------------------
def generate_grid():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    img = _subtle_paper_texture(img)
    draw = ImageDraw.Draw(img)

    grid_color = (200, 220, 240)       # light blue grid
    major_color = (160, 190, 220)      # slightly darker for major lines
    cell = 62                          # ~5mm at 300 DPI
    major_every = 5                    # bold line every 5 cells

    margin = 100

    # Vertical lines
    x = margin
    col = 0
    while x < W - margin:
        c = major_color if col % major_every == 0 else grid_color
        w = 2 if col % major_every == 0 else 1
        draw.line([(x, margin), (x, H - margin)], fill=c, width=w)
        x += cell
        col += 1

    # Horizontal lines
    y = margin
    row = 0
    while y < H - margin:
        c = major_color if row % major_every == 0 else grid_color
        w = 2 if row % major_every == 0 else 1
        draw.line([(margin, y), (W - margin, y)], fill=c, width=w)
        y += cell
        row += 1

    out = img.convert("RGB")
    out.save(OUTPUT_DIR / "grid.png", "PNG", dpi=(300, 300))
    print(f"  ✓ grid.png   ({W}×{H})")


# -----------------------------------------------------------------------
# 5. Dot Grid Paper
# -----------------------------------------------------------------------
def generate_dotted():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    img = _subtle_paper_texture(img)
    draw = ImageDraw.Draw(img)

    dot_color = (180, 190, 200)
    spacing = 62  # same as grid cell
    dot_r = 3
    margin = 120

    x = margin
    while x < W - margin:
        y = margin
        while y < H - margin:
            draw.ellipse(
                [(x - dot_r, y - dot_r), (x + dot_r, y + dot_r)],
                fill=dot_color,
            )
            y += spacing
        x += spacing

    out = img.convert("RGB")
    out.save(OUTPUT_DIR / "dotted.png", "PNG", dpi=(300, 300))
    print(f"  ✓ dotted.png ({W}×{H})")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating high-quality paper templates (A4 @ 300 DPI)...\n")
    generate_lined()
    generate_blank()
    generate_exam()
    generate_grid()
    generate_dotted()
    print(f"\nAll templates saved to {OUTPUT_DIR}")
