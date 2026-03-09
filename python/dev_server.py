"""
Flask dev server that exposes the handwriting generator as a REST API.

Endpoints
---------
POST /api/generate
    Form fields:
        text        (required) — the text to render
        template    (optional) — "lined" | "blank" | "exam"  (default: "lined")
        fontIndex   (optional) — 0-3                         (default: 0)
        fontSize    (optional) — int                         (default: auto)
        lineSpacing (optional) — int                         (default: auto)
        inkColor    (optional) — hex color                   (default: "#1a1a2e")
    File fields:
        customTemplate (optional) — a PNG/JPG image to use as background

    Returns JSON: { "pages": ["data:image/png;base64,...", ...] }

GET /api/fonts
    Returns JSON list of available font names.

GET /api/templates
    Returns JSON list of built-in template ids.
"""

import base64
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from analyzer import analyze_samples, default_profile
from generator import generate_pages, FONT_NAMES, BUILTIN_TEMPLATES
from template_analyzer import analyze_template, analyze_template_from_path

app = Flask(__name__)
CORS(app)                       # allow cross-origin from Next.js dev server


@app.route("/api/generate", methods=["POST"])
def api_generate():
    # Accept both JSON and multipart/form-data
    sample_bytes_list: list[bytes] = []

    if request.content_type and "multipart" in request.content_type:
        text = request.form.get("text", "")
        template = request.form.get("template", "lined")
        font_index = int(request.form.get("fontIndex", 0))
        font_size = request.form.get("fontSize")
        line_spacing = request.form.get("lineSpacing")
        ink_color = request.form.get("inkColor", "#1a1a2e")
        use_extracted = request.form.get("useExtractedStyle", "0") == "1"

        custom_file = request.files.get("customTemplate")
        custom_bytes = custom_file.read() if custom_file else None

        # Collect handwriting sample images
        for key in request.files:
            if key.startswith("sample"):
                sample_bytes_list.append(request.files[key].read())
    else:
        data = request.get_json(force=True) or {}
        text = data.get("text", "")
        template = data.get("template", "lined")
        font_index = int(data.get("fontIndex", 0))
        font_size = data.get("fontSize")
        line_spacing = data.get("lineSpacing")
        ink_color = data.get("inkColor", "#1a1a2e")
        use_extracted = bool(data.get("useExtractedStyle", False))
        custom_bytes = None

        b64_template = data.get("customTemplateBase64")
        if b64_template:
            custom_bytes = base64.b64decode(b64_template)

        # Support base64-encoded samples in JSON mode
        for b64 in (data.get("samples") or []):
            sample_bytes_list.append(base64.b64decode(b64))

    if not text.strip():
        return jsonify({"error": "text is required"}), 400

    # Analyze samples → style profile only if user chose extracted style
    if use_extracted and sample_bytes_list:
        profile = analyze_samples(sample_bytes_list)
    else:
        profile = None  # use default — font_index drives the font choice

    font_size = int(font_size) if font_size else None
    line_spacing = int(line_spacing) if line_spacing else None

    pages = generate_pages(
        text=text,
        template=template,
        font_index=font_index,
        font_size=font_size,
        line_spacing=line_spacing,
        ink_color=ink_color,
        custom_template_bytes=custom_bytes,
        style_profile=profile,
    )

    encoded = [
        "data:image/png;base64," + base64.b64encode(p).decode()
        for p in pages
    ]
    return jsonify({"pages": encoded, "profile": _serialize_profile(profile) if profile else None})


def _serialize_profile(p: dict | None) -> dict | None:
    """Make the profile JSON-serializable."""
    if p is None:
        return None
    out = dict(p)
    if isinstance(out.get("ink_color"), tuple):
        out["ink_color"] = list(out["ink_color"])
    return out


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Analyze handwriting samples and return the style profile (no generation)."""
    sample_bytes_list: list[bytes] = []

    if request.content_type and "multipart" in request.content_type:
        for key in request.files:
            if key.startswith("sample"):
                sample_bytes_list.append(request.files[key].read())
    else:
        data = request.get_json(force=True) or {}
        for b64 in (data.get("samples") or []):
            sample_bytes_list.append(base64.b64decode(b64))

    if not sample_bytes_list:
        return jsonify({"error": "At least one sample image is required"}), 400

    profile = analyze_samples(sample_bytes_list)
    return jsonify({"profile": _serialize_profile(profile)})


@app.route("/api/fonts", methods=["GET"])
def api_fonts():
    return jsonify(FONT_NAMES)


@app.route("/api/templates", methods=["GET"])
def api_templates():
    return jsonify(list(BUILTIN_TEMPLATES.keys()))


@app.route("/api/analyze-template", methods=["POST"])
def api_analyze_template():
    """Analyze a template image and return detected layout info."""
    if request.content_type and "multipart" in request.content_type:
        tpl_file = request.files.get("template")
        if not tpl_file:
            return jsonify({"error": "template file is required"}), 400
        layout = analyze_template(tpl_file.read())
    else:
        data = request.get_json(force=True) or {}
        b64 = data.get("templateBase64")
        if b64:
            layout = analyze_template(base64.b64decode(b64))
        else:
            tpl_id = data.get("templateId")
            if tpl_id and tpl_id in BUILTIN_TEMPLATES:
                layout = analyze_template_from_path(str(BUILTIN_TEMPLATES[tpl_id]))
            else:
                return jsonify({"error": "templateBase64 or templateId required"}), 400

    return jsonify(layout)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5328))
    app.run(host="127.0.0.1", port=port, debug=True)
