from flask import Blueprint, session, render_template, request, redirect
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash
from db import db
from helpers import login_required, apology

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Invalid username")
        if not password:
            return apology("Invalid password")
        if password != confirmation:
            return apology("Passwords do not match")

        existing = db.execute(
            text("SELECT 1 FROM users WHERE username=:u"), {"u": username}
        ).fetchone()
        if existing:
            return apology("Username is already taken")

        db.execute(
            text("INSERT INTO users (username, password) VALUES (:u, :p)"),
            {"u": username, "p": generate_password_hash(password)},
        )
        db.commit()
        session["username"] = username
        return redirect("/")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("Invalid username")
        if not password:
            return apology("Invalid password")

        row = db.execute(
            text("SELECT * FROM users WHERE username=:u"), {"u": username}
        ).fetchone()

        if not row:
            return apology("Username not found")
        if not check_password_hash(row.password, password):
            return apology("Incorrect password")

        session["username"] = row.username
        return redirect("/")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@auth.route("/profile")
@login_required
def profile():
    user_reviews = db.execute(
        text("""
            SELECT r.isbn, r.rating, r.comments, b.title, b.author, b.year
            FROM reviews r
            JOIN books b ON b.isbn = r.isbn
            WHERE r.username = :u
            ORDER BY b.title
        """),
        {"u": session["username"]},
    ).fetchall()

    ratings = [r[1] for r in user_reviews if r[1] is not None]
    average = "{:.1f}".format(sum(ratings) / len(ratings)) if ratings else None

    return render_template(
        "profile.html",
        username=session["username"],
        reviews=user_reviews,
        average=average,
    )


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirmation", "")

        if not current:
            return apology("Please enter your current password")
        if not new:
            return apology("Please enter a new password")
        if new == current:
            return apology("New password must differ from current password")
        if new != confirm:
            return apology("New passwords do not match")

        row = db.execute(
            text("SELECT password FROM users WHERE username=:u"),
            {"u": session["username"]},
        ).fetchone()

        if not check_password_hash(row.password, current):
            return apology("Current password is incorrect")

        db.execute(
            text("UPDATE users SET password=:p WHERE username=:u"),
            {"p": generate_password_hash(new), "u": session["username"]},
        )
        db.commit()
        return render_template("change_password.html", success=True)

    return render_template("change_password.html", success=False)
