from flask import Blueprint, session, render_template, request
from sqlalchemy import text
from db import db
from helpers import login_required, apology

reviews = Blueprint("reviews", __name__)


@reviews.route("/review/<isbn>", methods=["GET", "POST"])
@login_required
def review(isbn):
    book = db.execute(
        text("SELECT * FROM books WHERE isbn=:isbn"), {"isbn": isbn}
    ).fetchone()

    if not book:
        return apology("Invalid ISBN")

    if request.method == "POST":
        rating = request.form.get("rating")
        comments = request.form.get("comments")

        existing = db.execute(
            text("SELECT 1 FROM reviews WHERE username=:u AND isbn=:isbn"),
            {"u": session["username"], "isbn": book.isbn},
        ).fetchone()

        if existing:
            db.execute(
                text("UPDATE reviews SET rating=:r, comments=:c WHERE username=:u AND isbn=:isbn"),
                {"r": rating, "c": comments, "u": session["username"], "isbn": book.isbn},
            )
        else:
            db.execute(
                text("INSERT INTO reviews (username, isbn, rating, comments) VALUES (:u, :isbn, :r, :c)"),
                {"u": session["username"], "isbn": book.isbn, "r": rating, "c": comments},
            )
        db.commit()

    all_reviews = db.execute(
        text("SELECT * FROM reviews WHERE isbn=:isbn"), {"isbn": book.isbn}
    ).fetchall()
    all_ratings = [int(r[2]) for r in all_reviews if r[2] is not None]
    average_rating = "{:.1f}".format(sum(all_ratings) / len(all_ratings)) if all_ratings else "N/A"

    return render_template(
        "review.html",
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        year=book.year,
        averageRating=average_rating,
        reviews=all_reviews,
    )


@reviews.route("/review/<isbn>/delete", methods=["POST"])
@login_required
def delete_review(isbn):
    db.execute(
        text("DELETE FROM reviews WHERE username=:u AND isbn=:isbn"),
        {"u": session["username"], "isbn": isbn},
    )
    db.commit()
    from flask import redirect
    return redirect(f"/review/{isbn}")
