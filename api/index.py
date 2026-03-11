"""
Vercel Python Serverless Function — exposes the handwriting generator
as serverless API endpoints on Vercel (no separate backend needed).
Locally, use python/dev_server.py instead.
"""

import sys
import os

# Make the python/ package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import base64

from flask import Flask, jsonify, request
from flask_cors import CORS

from analyzer import analyze_samples, default_profile
from generator import generate_pages, FONT_NAMES, BUILTIN_TEMPLATES
from template_analyzer import analyze_template, analyze_template_from_path, analyze_template_v2

app = Flask(__name__)
CORS(app)


@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON instead of HTML for any unhandled errors."""
    import traceback
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Diagnostic endpoint to check if the function is running."""
    import importlib
    status = {"ok": True}
    for mod in ["flask", "PIL", "numpy"]:
        try:
            importlib.import_module(mod)
            status[mod] = "ok"
        except ImportError as e:
            status[mod] = str(e)
    try:
        from generator import FONT_NAMES, BUILTIN_TEMPLATES
        from pathlib import Path
        status["fonts"] = len(FONT_NAMES)
        status["templates"] = {k: str(v) for k, v in BUILTIN_TEMPLATES.items()}
        status["templates_exist"] = {k: Path(v).exists() for k, v in BUILTIN_TEMPLATES.items()}
    except Exception as e:
        status["generator_error"] = str(e)
    return jsonify(status)


@app.route("/api/generate", methods=["POST"])
def api_generate():
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

        for b64 in (data.get("samples") or []):
            sample_bytes_list.append(base64.b64decode(b64))

    if not text.strip():
        return jsonify({"error": "text is required"}), 400

    if use_extracted and sample_bytes_list:
        profile = analyze_samples(sample_bytes_list)
    else:
        profile = None

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
    return jsonify({
        "pages": encoded,
        "profile": _serialize_profile(profile) if profile else None,
    })


@app.route("/api/fonts", methods=["GET"])
def api_fonts():
    return jsonify(FONT_NAMES)


@app.route("/api/templates", methods=["GET"])
def api_templates():
    return jsonify(list(BUILTIN_TEMPLATES.keys()))


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Analyze handwriting samples and return the style profile."""
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


def _serialize_profile(p: dict | None) -> dict | None:
    if p is None:
        return None
    out = dict(p)
    if isinstance(out.get("ink_color"), tuple):
        out["ink_color"] = list(out["ink_color"])
    return out
