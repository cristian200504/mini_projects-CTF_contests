import html
import os
import re
from string import Template

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GO_SANITIZER_URL = os.environ.get("GO_SANITIZER_URL", "http://127.0.0.1:7071/sanitize")
SCRIPT_FENCE_RE = re.compile(r"<\s*/?\s*script\b", re.IGNORECASE | re.ASCII)
TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]{1,32})\s*\}\}")
VAR_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,31}$")


def coerce_scalar(value):
    text = value.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            return text
    return text


def parse_profile_blob(blob):
    root = {}
    if not isinstance(blob, str) or blob == "":
        return root

    for part in blob.split(";"):
        piece = part.strip()
        if not piece or "=" not in piece:
            continue

        raw_key, raw_value = piece.split("=", 1)
        path = [segment for segment in raw_key.strip().split(".") if segment]
        if not path:
            continue

        node = root
        for segment in path[:-1]:
            existing = node.get(segment)
            if not isinstance(existing, dict):
                existing = {}
                node[segment] = existing
            node = existing

        node[path[-1]] = coerce_scalar(raw_value)

    return root


def brace_armor(text):
    return (
        text.replace("{{", "&#123;&#123;")
        .replace("}}", "&#125;&#125;")
        .replace("{%", "&#123;%")
        .replace("%}", "%&#125;")
        .replace("{#", "&#123;#")
        .replace("#}", "#&#125;")
    )


def build_trace_panel(raw):
    clipped = raw[:480]
    guarded = brace_armor(html.escape(clipped, quote=False))
    return (
        "<article class=\"trace-card\">"
        "<h3>server-side lane</h3>"
        f"<pre>{guarded}</pre>"
        "</article>"
    )


@app.get("/")
def index():
    tpl = request.args.get("tpl", "profile-card", type=str)
    boot = {
        "draft": request.args.get("d", "<b>preview lane</b>", type=str),
        "profile": request.args.get("p", "", type=str),
        "tpl": tpl,
        "mail_subject": request.args.get("ms", "report:$username", type=str),
        "mail_body": request.args.get("mb", "hello $username from queue", type=str),
    }
    trace_html = build_trace_panel(tpl)
    return render_template("index.html", boot=boot, trace_html=trace_html)


@app.get("/api/profile")
def api_profile():
    blob = request.args.get("p", "", type=str)
    parsed = parse_profile_blob(blob)

    payload = {
        "view": {"theme": "oxide", "track": "safety"},
        "render": {"engine": "python", "mode": "strict"},
        "mail": {"relay": "null"},
        "layout": {
            "backend": "delta",
            "probe": "carrier",
            "hints": ["alpha", "beta", "gamma"],
        },
        "flags": {"legacy": True, "dial": "v3"},
    }

    if isinstance(parsed, dict):
        payload.update(parsed)

    return jsonify(payload)


@app.post("/api/render")
def api_render():
    data = request.get_json(silent=True) or {}

    draft = data.get("draft", "")
    if not isinstance(draft, str):
        draft = str(draft)

    engine = data.get("engine", "python")
    if not isinstance(engine, str):
        engine = str(engine)
    engine = engine.strip().lower() or "python"

    meta = data.get("meta")
    if not isinstance(meta, dict):
        meta = {}

    if SCRIPT_FENCE_RE.search(draft):
        return jsonify({"html": "[blocked-by-lexical-fence]", "engine": engine, "blocked": True})

    if engine == "go":
        request_body = {
            "html": draft,
            "allow": ["script"],
            "mode": str(meta.get("mode", "legacy")),
            "switches": meta.get("switches", ["trace", "cold"]),
        }
        try:
            upstream = requests.post(GO_SANITIZER_URL, json=request_body, timeout=2.0)
            parsed = upstream.json() if upstream.ok else {}
            rendered = str(parsed.get("html", ""))
        except Exception:
            rendered = html.escape(draft, quote=False)

        return jsonify({"html": rendered, "engine": "go", "blocked": False})

    rendered = html.escape(draft, quote=False)
    if str(meta.get("dialect", "")).lower() == "entity":
        rendered = rendered.replace("&lt;", "&#x3c;").replace("&gt;", "&#x3e;")

    return jsonify({"html": rendered, "engine": "python", "blocked": False})


@app.post("/api/compose")
def api_compose():
    data = request.get_json(silent=True) or {}

    template = data.get("template", "")
    if not isinstance(template, str):
        template = str(template)

    vars_blob = data.get("vars")
    if not isinstance(vars_blob, dict):
        vars_blob = {}

    safe_vars = {}
    for key, value in vars_blob.items():
        if isinstance(key, str) and VAR_KEY_RE.fullmatch(key):
            safe_vars[key] = str(value)

    def replace_token(match):
        key = match.group(1)
        if key not in safe_vars:
            return match.group(0)
        return html.escape(safe_vars[key], quote=False)

    preview = TOKEN_RE.sub(replace_token, template)
    dialect = str(data.get("dialect", "phase-a"))

    if dialect.lower() == "phase-b":
        preview = preview.replace("${", "$ {")

    return jsonify({"preview": preview, "dialect": dialect})


@app.post("/api/mail-preview")
def api_mail_preview():
    data = request.get_json(silent=True) or {}

    subject = data.get("subject", "")
    if not isinstance(subject, str):
        subject = str(subject)

    body = data.get("body", "")
    if not isinstance(body, str):
        body = str(body)

    vars_blob = data.get("vars")
    if not isinstance(vars_blob, dict):
        vars_blob = {}

    safe_vars = {}
    for key, value in vars_blob.items():
        if isinstance(key, str) and VAR_KEY_RE.fullmatch(key):
            safe_vars[key] = str(value)

    subject_rendered = Template(subject).safe_substitute(safe_vars)
    body_rendered = Template(body).safe_substitute(safe_vars)

    safe_subject = brace_armor(html.escape(subject_rendered, quote=False))
    safe_body = brace_armor(html.escape(body_rendered, quote=False))

    html_block = (
        "<article class=\"mail-card\">"
        f"<h3>{safe_subject}</h3>"
        f"<pre>{safe_body}</pre>"
        "</article>"
    )

    return jsonify({"html": html_block, "meta": {"keys": sorted(list(safe_vars.keys()))}})


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

# POTATO_FUNGI_GROWTH_YOGURT_PIZZA @&86549&788875478-568999-34)8&£$$ STRING!!!!!
