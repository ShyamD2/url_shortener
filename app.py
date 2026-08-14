"""
URL Shortener - Flask application
Run with: python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import sqlite3
import string
import random
from datetime import datetime
from flask import Flask, request, redirect, render_template, jsonify, abort, g

app = Flask(__name__)

DATABASE = "urls.db"
SHORT_CODE_LENGTH = 6
ALPHABET = string.ascii_letters + string.digits


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_short_code(length=SHORT_CODE_LENGTH):
    """Generate a random short code that doesn't already exist in the DB."""
    db = get_db()
    while True:
        code = "".join(random.choices(ALPHABET, k=length))
        existing = db.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (code,)
        ).fetchone()
        if not existing:
            return code


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


# ---------------------------------------------------------------------------
# Routes - Web UI
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM urls ORDER BY id DESC LIMIT 20"
    ).fetchall()
    return render_template("index.html", urls=rows, short_base=request.host_url)


@app.route("/shorten", methods=["POST"])
def shorten():
    original_url = request.form.get("url", "").strip()
    custom_code = request.form.get("custom_code", "").strip()

    if not original_url:
        return render_template(
            "index.html",
            error="Please enter a URL.",
            urls=get_db().execute("SELECT * FROM urls ORDER BY id DESC LIMIT 20").fetchall(),
            short_base=request.host_url,
        )

    original_url = normalize_url(original_url)
    db = get_db()

    if custom_code:
        if not custom_code.isalnum():
            return render_template(
                "index.html",
                error="Custom code must be alphanumeric.",
                urls=db.execute("SELECT * FROM urls ORDER BY id DESC LIMIT 20").fetchall(),
                short_base=request.host_url,
            )
        existing = db.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (custom_code,)
        ).fetchone()
        if existing:
            return render_template(
                "index.html",
                error=f"Custom code '{custom_code}' is already taken.",
                urls=db.execute("SELECT * FROM urls ORDER BY id DESC LIMIT 20").fetchall(),
                short_base=request.host_url,
            )
        short_code = custom_code
    else:
        short_code = generate_short_code()

    db.execute(
        "INSERT INTO urls (short_code, original_url, created_at, clicks) VALUES (?, ?, ?, 0)",
        (short_code, original_url, datetime.utcnow().isoformat()),
    )
    db.commit()

    return redirect("/")


@app.route("/<short_code>")
def redirect_to_url(short_code):
    db = get_db()
    row = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if row is None:
        abort(404)

    db.execute(
        "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,)
    )
    db.commit()
    return redirect(row["original_url"])


@app.route("/stats/<short_code>")
def stats(short_code):
    db = get_db()
    row = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if row is None:
        abort(404)
    return render_template("stats.html", url=row, short_base=request.host_url)


# ---------------------------------------------------------------------------
# Routes - JSON API
# ---------------------------------------------------------------------------

@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json(silent=True) or {}
    original_url = data.get("url", "").strip()
    custom_code = data.get("custom_code", "").strip()

    if not original_url:
        return jsonify({"error": "Missing 'url' field."}), 400

    original_url = normalize_url(original_url)
    db = get_db()

    if custom_code:
        if not custom_code.isalnum():
            return jsonify({"error": "Custom code must be alphanumeric."}), 400
        existing = db.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (custom_code,)
        ).fetchone()
        if existing:
            return jsonify({"error": f"Custom code '{custom_code}' is already taken."}), 409
        short_code = custom_code
    else:
        short_code = generate_short_code()

    db.execute(
        "INSERT INTO urls (short_code, original_url, created_at, clicks) VALUES (?, ?, ?, 0)",
        (short_code, original_url, datetime.utcnow().isoformat()),
    )
    db.commit()

    return jsonify({
        "short_code": short_code,
        "short_url": request.host_url + short_code,
        "original_url": original_url,
    }), 201


@app.route("/api/stats/<short_code>")
def api_stats(short_code):
    db = get_db()
    row = db.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "Short code not found."}), 404
    return jsonify({
        "short_code": row["short_code"],
        "original_url": row["original_url"],
        "created_at": row["created_at"],
        "clicks": row["clicks"],
    })


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
