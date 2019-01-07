import os
from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, apology
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

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


@app.route("/")
@login_required
def index():
    ex = db.execute("SELECT * FROM users")
    return render_template("index.html", users=ex)

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

        check = db.execute("SELECT * FROM users WHERE username=:username", {'username': username}).fetchall()

        if check is None:
            return apology("Username already exists")
        
        register = db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {'username': username, 'password':hashed_password})
        db.commit()
        
        session['user_id'] = register

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

        session['user_id'] = check[0]['id']
        
        return redirect('/')

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")