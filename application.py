import os
from flask import Flask, session, render_template, request, redirect, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, apology
from werkzeug.security import check_password_hash, generate_password_hash
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

if not os.getenv("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY is not set")
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.secret_key = os.getenv("SECRET_KEY")

# Set up database — normalize postgres:// to postgresql:// for SQLAlchemy 1.4+
database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(database_url, pool_pre_ping=True)
db = scoped_session(sessionmaker(bind=engine))

try:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS books (
            isbn   TEXT PRIMARY KEY,
            title  TEXT NOT NULL,
            author TEXT,
            year   TEXT
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS reviews (
            username TEXT NOT NULL REFERENCES users(username),
            isbn     TEXT NOT NULL REFERENCES books(isbn),
            rating   INTEGER,
            comments TEXT,
            PRIMARY KEY (username, isbn)
        )
    """))
    db.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS genre TEXT"))
    db.commit()
except Exception:
    db.rollback()
finally:
    db.remove()


@app.route("/", methods=['GET', 'POST'])
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
            params
        ).fetchall()

        if not results:
            return apology("No results found. Try broadening your search.")
        return render_template("search.html", books=results)
    else:
        return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("Invalid username")

        elif not request.form.get("password"):
            return apology("Invalid password")

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match")

        username = request.form.get("username")
        hashed_password = generate_password_hash(request.form.get("password"))

        check = db.execute(text("SELECT * FROM users WHERE username=:username"), {'username': username}).fetchone()

        if check is None:
            db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), {'username': username, 'password': hashed_password})
            db.commit()
            session['username'] = username
        else:
            return apology("Username is already taken")

        return redirect('/')
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Invalid username")

        elif not request.form.get("password"):
            return apology("Invalid password")

        username = request.form.get("username")

        check = db.execute(text("SELECT * FROM users WHERE username=:username"), {'username': username}).fetchall()

        if not check:
            return apology("Username not found")

        elif not check_password_hash(check[0].password, request.form.get("password")):
            return apology("Incorrect password")

        session['username'] = check[0].username

        return redirect('/')

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api(isbn):
    result = db.execute(text("SELECT * FROM books WHERE isbn=:isbn"), {'isbn': isbn}).fetchone()

    if not result:
        return jsonify({"error": "Invalid ISBN"}), 404

    res = requests.get("https://openlibrary.org/search.json", params={"isbn": isbn, "fields": "ratings_count,ratings_average"})
    data = res.json()
    if data.get('numFound', 0) > 0:
        book_data = data['docs'][0]
        review_count = book_data.get('ratings_count', 0)
        average_score = round(book_data.get('ratings_average', 0), 2)
    else:
        review_count = 0
        average_score = 0

    return jsonify({'title': result[1], 'author': result[2], 'year': result[3], 'isbn': result[0],
                    'review_count': review_count, 'average_score': average_score})


@app.route("/review/<isbn>", methods=['GET', 'POST'])
@login_required
def review(isbn):
    result = db.execute(text("SELECT * FROM books WHERE isbn=:isbn"), {'isbn': isbn}).fetchone()

    if not result:
        return apology("Invalid ISBN")

    if request.method == 'POST':
        rating = request.form.get("rating")
        comments = request.form.get("comments")

        existing = db.execute(text("SELECT * FROM reviews WHERE username=:username AND isbn=:isbn"), {'username': session['username'], 'isbn': result[0]}).fetchone()

        if not existing:
            db.execute(text("INSERT INTO reviews (username, isbn, rating, comments) VALUES (:username, :isbn, :rating, :comments)"), {'username': session['username'], 'isbn': result[0], 'rating': rating, 'comments': comments})
        else:
            db.execute(text("UPDATE reviews SET rating=:rating, comments=:comments WHERE username=:username AND isbn=:isbn"), {'rating': rating, 'comments': comments, 'username': session['username'], 'isbn': result[0]})
        db.commit()

    allReviews = db.execute(text("SELECT * FROM reviews WHERE isbn=:isbn"), {'isbn': result[0]}).fetchall()
    allRatings = [int(i[2]) for i in allReviews if i[2] is not None]
    averageRating = "{0:0.1f}".format(sum(allRatings) / len(allRatings)) if allRatings else "N/A"

    return render_template("review.html", isbn=result[0], title=result[1], author=result[2], year=result[3],
                           averageRating=averageRating, reviews=allReviews)

if __name__ == '__main__':
    app.run(debug=True)
