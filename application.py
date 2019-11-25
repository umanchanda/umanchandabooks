from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, apology
from werkzeug.exceptions import default_exceptions
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

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://wzhyqownmxotta:996a486a693a09dc9427b75e4787782c71f51ee2416c860b0f753f0dcaadc097@ec2-107-20-250-113.compute-1.amazonaws.com:5432/d3lpaali8o0um2")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        search = str(request.form.get("book")).lower()
        if not search:
            return apology("Invalid search query")
        search = "%" + search + "%"
        results = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :search OR LOWER(author) LIKE :search OR isbn LIKE :search OR year LIKE :search", {'search':search}).fetchall()
        if len(results) == 0:
            return apology("Returned no results. Please alter your search query")
        return render_template("search.html",books=results)
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
        review
        username = request.form.get("username")
        hashed_password = generate_password_hash(request.form.get("password"))

        check = db.execute("SELECT * FROM users WHERE username=:username", {'username': username}).fetchone()

        if check is None:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {'username': username, 'password':hashed_password})
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

        check = db.execute("SELECT * FROM users WHERE username=:username", {'username': username}).fetchall()
        
        if check is None:
            return apology("Username exists")
        
        elif not check_password_hash(check[0]['password'], request.form.get("password")):
            return apology("Incorrect password")

        session['username'] = check[0]['username']
        
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
    result = db.execute("SELECT * FROM books WHERE isbn=:isbn", {'isbn':isbn}).fetchone()

    if not result:
        return apology("Invalid ISBN")
    
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "1AgC1FgCvS4k7iktD7JqIg", "isbns": isbn})
    books = res.json()['books']

    return json.dumps({'title':result[1], 'author':result[2], 'year':result[3], 'isbn':result[0], 
    'review_count': books[0]['reviews_count'], 'average_score':books[0]['average_rating']}, sort_keys=False)


@app.route("/review/<isbn>", methods=['GET', 'POST'])
@login_required
def review(isbn):
    result = db.execute("SELECT * FROM books WHERE isbn=:isbn", {'isbn':isbn}).fetchone()
    if request.method == 'POST':

        if not result:
            return apology("Invalid ISBN")
        
        rating = request.form.get("rating")
        comments = request.form.get("comments")

        allReviews = db.execute("SELECT * FROM reviews WHERE isbn=:isbn", {'isbn': result[0]}).fetchall()
        allRatings = [int(i[2]) for i in allReviews if i[2] is not None]
        
        if not db.execute("SELECT * FROM reviews WHERE username=:username AND isbn=:isbn", {'username': session['username'], 'isbn': result[0]}).fetchall():
            db.execute("INSERT INTO reviews (username, isbn, rating, comments) VALUES (:username, :isbn, :rating, :comments)", {'username': session['username'], 'isbn': result[0], 'rating': rating, 'comments':comments})
            db.commit()
        else:
            db.execute("UPDATE reviews SET rating=:rating, comments=:comments WHERE username=:username AND isbn=:isbn", {'rating': rating, 'comments': comments, 'username': session['username'], 'isbn': result[0]})
            db.commit()
        
        
        averageRating = "{0:0.1f}".format(sum(allRatings) / len(allRatings))
        
        return render_template("review.html", isbn=result[0], title=result[1], author=result[2], year=result[3], averageRating=averageRating, username=session['username'], reviews=allReviews)
    else:
        return render_template("review.html", isbn=result[0], title=result[1], author=result[2], year=result[3])

if __name__ == '__main__':
    app.run(debug=True)