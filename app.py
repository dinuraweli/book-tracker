"""Book Tracker — a self-contained Flask app.

Reads the original books.csv on first run, migrates every book into a JSON
store (books.json) with stable ids + rating/review fields, then serves a REST
API and a single-page frontend. The original books.csv is never modified.
"""
import csv
import json
import os
from datetime import date
from flask import Flask, jsonify, request, render_template

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE, "books.csv")
JSON_FILE = os.path.join(BASE, "books.json")
LEGACY_REVIEWS = os.path.join(BASE, "reviews.json")

app = Flask(__name__)

READ_VALUES = {"Y", "YES", "TRUE", "1", "READ"}
FORMATS = ["Kindle", "Physical", "PDF", "Audio", "Other"]


# ---------- storage ----------
def _clean(v):
    return (v or "").strip()


def migrate_from_csv():
    """Build the JSON store from the original CSV (+ legacy reviews if any)."""
    books = []
    if not os.path.exists(CSV_FILE):
        return books

    # Optional legacy ratings keyed by "Title :: Author" or "title_author"
    legacy = {}
    if os.path.exists(LEGACY_REVIEWS):
        try:
            with open(LEGACY_REVIEWS) as f:
                legacy = json.load(f)
        except Exception:
            legacy = {}

    def legacy_lookup(title, author):
        for key in (f"{title} :: {author}", f"{title}_{author}"):
            entry = legacy.get(key)
            if isinstance(entry, dict):
                return entry.get("rating", 0) or 0, entry.get("review", "") or ""
            if isinstance(entry, (int, float)):
                return int(entry), ""
        return 0, ""

    today = date.today().isoformat()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            title = _clean(row.get("title")) or "Unknown Title"
            author = _clean(row.get("author")) or "Unknown Author"
            fmt = _clean(row.get("format")) or "Unknown"
            is_read = _clean(row.get("is_read")).upper() in READ_VALUES
            rating, review = legacy_lookup(title, author)
            books.append({
                "id": i,
                "title": title,
                "author": author,
                "series": _clean(row.get("series")),
                "book_number": _clean(row.get("book_number")).replace(".0", ""),
                "format": fmt if fmt in FORMATS else ("Physical" if fmt == "Physical" else fmt),
                "status": "read" if is_read else "unread",
                "date_added": _clean(row.get("date_added")) or today,
                "date_finished": _clean(row.get("date_finished")),
                "rating": int(rating) if rating else 0,
                "review": review,
            })
    return books


def load_books():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, encoding="utf-8") as f:
            return json.load(f)
    books = migrate_from_csv()
    save_books(books)
    return books


def save_books(books):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def next_id(books):
    return (max((b["id"] for b in books), default=0)) + 1


# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/books")
def api_list():
    return jsonify(load_books())


@app.post("/api/books")
def api_add():
    data = request.get_json(force=True) or {}
    title = _clean(data.get("title"))
    author = _clean(data.get("author"))
    if not title or not author:
        return jsonify({"error": "Title and author are required."}), 400

    books = load_books()
    dupe = any(b["title"].lower() == title.lower()
               and b["author"].lower() == author.lower() for b in books)
    if dupe:
        return jsonify({"error": "That book is already in your library."}), 409

    status = "read" if data.get("status") == "read" else "unread"
    book = {
        "id": next_id(books),
        "title": title,
        "author": author,
        "series": _clean(data.get("series")),
        "book_number": _clean(data.get("book_number")),
        "format": data.get("format") if data.get("format") in FORMATS else "Kindle",
        "status": status,
        "date_added": date.today().isoformat(),
        "date_finished": _clean(data.get("date_finished")) or (date.today().isoformat() if status == "read" else ""),
        "rating": int(data.get("rating") or 0),
        "review": _clean(data.get("review")),
    }
    books.append(book)
    save_books(books)
    return jsonify(book), 201


@app.put("/api/books/<int:book_id>")
def api_update(book_id):
    data = request.get_json(force=True) or {}
    books = load_books()
    for b in books:
        if b["id"] == book_id:
            if "status" in data:
                b["status"] = "read" if data["status"] == "read" else "unread"
                if b["status"] == "read" and not b["date_finished"]:
                    b["date_finished"] = data.get("date_finished") or date.today().isoformat()
                if b["status"] == "unread":
                    b["date_finished"] = ""
            for field in ("format", "series", "book_number", "review", "date_finished"):
                if field in data:
                    b[field] = _clean(str(data[field]))
            if "rating" in data:
                b["rating"] = max(0, min(5, int(data["rating"] or 0)))
            save_books(books)
            return jsonify(b)
    return jsonify({"error": "Not found"}), 404


@app.delete("/api/books/<int:book_id>")
def api_delete(book_id):
    books = load_books()
    remaining = [b for b in books if b["id"] != book_id]
    if len(remaining) == len(books):
        return jsonify({"error": "Not found"}), 404
    save_books(remaining)
    return jsonify({"ok": True})


if __name__ == "__main__":
    load_books()  # ensure migration runs at startup
    app.run(host="127.0.0.1", port=5000, debug=False)
