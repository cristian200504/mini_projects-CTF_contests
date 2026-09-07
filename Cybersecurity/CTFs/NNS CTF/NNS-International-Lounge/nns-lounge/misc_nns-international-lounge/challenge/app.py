import hashlib
import hmac
import io
import mimetypes
import os
import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock

import qrcode
from flask import Flask, flash, redirect, render_template, request, send_file, session
from PIL import Image
from pyzbar.pyzbar import decode
from werkzeug.security import check_password_hash, generate_password_hash


FLAG = os.environ["FLAG"]
VISIT_ALLOWANCE = 4
TICKET_SECRET = hashlib.sha256(b"lounge").digest()

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    SECRET_KEY=secrets.token_hex(32),
)


class Rejected(Exception):
    pass


@app.errorhandler(Rejected)
def show_rejection(error):
    flash(str(error), "error")
    return redirect("/")


def ticket_fields(user):
    issued = user["issued_at"].strftime("%d%m%y%H%M")
    expires = user["expires_at"].strftime("%d%m%y%H%M")
    return [
        "LS", issued[:6], issued, expires, user["member_id"], "NNS",
        "201", user["name"], str(user["remaining_visits"]),
    ]


def sign(fields):
    return hmac.new(TICKET_SECRET, "/".join(fields).encode(), hashlib.sha256).hexdigest()[:6]


def encode_pass(fields):
    return "/".join(fields + [sign(fields)])


def decode_pass(payload):
    parts = payload.strip().split("/")
    if len(parts) != 10:
        raise Rejected("invalid ticket field count")
    fields, supplied_mac = parts[:-1], parts[-1]
    if not hmac.compare_digest(sign(fields), supplied_mac):
        raise Rejected("invalid ticket signature")
    return fields


def read_qr(upload):
    if not upload:
        raise Rejected("choose a QR image")
    try:
        results = decode(Image.open(upload.stream))
    except Exception as exc:
        raise Rejected("could not read image") from exc
    if len(results) != 1:
        raise Rejected("image must contain exactly one QR code")
    return results[0].data.decode("utf-8", "replace")


USERS = {}
NAME_INDEX = {}
STORE_LOCK = Lock()


def current_user():
    return USERS.get(session.get("user_id"))


def clean_name(value):
    return " ".join(value.split())


def create_account(first_name, last_name, password):
    name = (first_name.casefold(), last_name.casefold())
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    with STORE_LOCK:
        if name in NAME_INDEX:
            return None
        user_id = secrets.token_hex(8)
        NAME_INDEX[name] = user_id
        USERS[user_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "name": f"{first_name} {last_name}",
            "password_hash": generate_password_hash(password),
            "member_id": f"81{secrets.randbelow(10**14):014d}",
            "issued_at": now,
            "expires_at": now + timedelta(days=365),
            "visits_used": 0,
            "remaining_visits": VISIT_ALLOWANCE,
        }
    return user_id


@app.get("/")
def index():
    return render_template("index.html", user=current_user(), allowance=VISIT_ALLOWANCE)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    first_name = clean_name(request.form.get("first_name", ""))
    last_name = clean_name(request.form.get("last_name", ""))
    password = request.form.get("password", "")
    if not (1 <= len(first_name) <= 32 and 1 <= len(last_name) <= 32) or "/" in first_name + last_name:
        flash("First and last name are required, must be at most 32 characters, and cannot contain a slash.", "error")
        return render_template("register.html"), 400
    if len(password) < 8:
        flash("Password must be at least eight characters.", "error")
        return render_template("register.html"), 400
    user_id = create_account(first_name, last_name, password)
    if not user_id:
        flash("A membership with that first and last name already exists.", "error")
        return render_template("register.html"), 409
    session.clear()
    session["user_id"] = user_id
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    name = tuple(clean_name(request.form.get(field, "")).casefold() for field in ("first_name", "last_name"))
    user = USERS.get(NAME_INDEX.get(name))
    if not user or not check_password_hash(user["password_hash"], request.form.get("password", "")):
        flash("Incorrect name or password.", "error")
        return render_template("login.html"), 401
    session.clear()
    session["user_id"] = NAME_INDEX[name]
    return redirect("/")


@app.post("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.get("/pass.png")
def membership_pass():
    user = current_user()
    if not user:
        return redirect("/login")
    image = io.BytesIO()
    qrcode.make(encode_pass(ticket_fields(user))).save(image, format="PNG")
    image.seek(0)
    return send_file(image, mimetype="image/png")


@app.post("/lounge")
def scan():
    user = current_user()
    if not user:
        return redirect("/login")
    fields = decode_pass(read_qr(request.files.get("ticket")))
    try:
        encoded_remaining = int(fields[-1])
    except ValueError as exc:
        raise Rejected("invalid remaining-visit count") from exc
    if fields[:-1] != ticket_fields(user)[:-1]:
        raise Rejected("Pass details do not match the issued membership.")
    if datetime.now(timezone.utc) > user["expires_at"]:
        raise Rejected("This pass has expired.")
    with STORE_LOCK:
        activating_bonus = user["visits_used"] == 0 and encoded_remaining > VISIT_ALLOWANCE
        if encoded_remaining != user["remaining_visits"] and not activating_bonus:
            raise Rejected("This pass is stale. Download the newly updated QR pass.")
        if encoded_remaining <= 0:
            raise Rejected("No lounge visits remain on this membership.")
        user["visits_used"] += 1
        user["remaining_visits"] = encoded_remaining - 1
    return render_template("lounge.html", user=user, flag=FLAG if user["visits_used"] > VISIT_ALLOWANCE else None)


@app.get("/health")
def health():
    return {"ok": True}
