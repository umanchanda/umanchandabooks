import os
from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, apology
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database — normalize postgres:// to postgresql:// for SQLAlchemy 1.4+
database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(database_url)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        search = str(request.form.get("book")).lower()
        if not search:
            return apology("Invalid search query")
        search = "%" + search + "%"
        results = db.execute(text("SELECT * FROM books WHERE LOWER(title) LIKE :search OR LOWER(author) LIKE :search OR isbn LIKE :search OR year LIKE :search"), {'search': search}).fetchall()
        if len(results) == 0:
            return apology("Returned no results. Please alter your search query")
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
        return apology("Invalid ISBN")

    res = requests.get("https://openlibrary.org/search.json", params={"isbn": isbn, "fields": "ratings_count,ratings_average"})
    data = res.json()
    if data.get('numFound', 0) > 0:
        book_data = data['docs'][0]
        review_count = book_data.get('ratings_count', 0)
        average_score = round(book_data.get('ratings_average', 0), 2)
    else:
        review_count = 0
        average_score = 0

    return json.dumps({'title': result[1], 'author': result[2], 'year': result[3], 'isbn': result[0],
                       'review_count': review_count, 'average_score': average_score}, sort_keys=False)


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

        return render_template("review.html", isbn=result[0], title=result[1], author=result[2], year=result[3], averageRating=averageRating, username=session['username'], reviews=allReviews)
    else:
        return render_template("review.html", isbn=result[0], title=result[1], author=result[2], year=result[3])

if __name__ == '__main__':
    app.run(debug=True)
