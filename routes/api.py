import requests
from flask import Blueprint, jsonify
from sqlalchemy import text
from db import db
from helpers import login_required

api = Blueprint("api", __name__)


@api.route("/api/<isbn>", methods=["GET"])
@login_required
def book_api(isbn):
    book = db.execute(
        text("SELECT * FROM books WHERE isbn=:isbn"), {"isbn": isbn}
    ).fetchone()

    if not book:
        return jsonify({"error": "Invalid ISBN"}), 404

    res = requests.get(
        "https://openlibrary.org/search.json",
        params={"isbn": isbn, "fields": "ratings_count,ratings_average"},
    )
    data = res.json()
    if data.get("numFound", 0) > 0:
        doc = data["docs"][0]
        review_count = doc.get("ratings_count", 0)
        average_score = round(doc.get("ratings_average", 0), 2)
    else:
        review_count = 0
        average_score = 0

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": average_score,
    })
