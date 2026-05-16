from flask import Blueprint, render_template, request
from sqlalchemy import text
from db import db
from helpers import login_required, apology

books = Blueprint("books", __name__)


@books.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        genre = request.form.get("genre", "").strip()
        year = request.form.get("year", "").strip()

        if not any([title, author, genre, year]):
            return apology("Please enter at least one search term")

        conditions = []
        params = {}
        if title:
            conditions.append("LOWER(title) LIKE :title")
            params["title"] = f"%{title.lower()}%"
        if author:
            conditions.append("LOWER(author) LIKE :author")
            params["author"] = f"%{author.lower()}%"
        if genre:
            conditions.append("LOWER(COALESCE(genre,'')) LIKE :genre")
            params["genre"] = f"%{genre.lower()}%"
        if year:
            conditions.append("year LIKE :year")
            params["year"] = f"%{year}%"

        where_clause = " AND ".join(conditions)
        results = db.execute(
            text(f"SELECT * FROM books WHERE {where_clause} LIMIT 100"),
            params,
        ).fetchall()

        if not results:
            return apology("No results found. Try broadening your search.")
        return render_template("search.html", books=results)

    return render_template("index.html")
