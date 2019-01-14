from functools import wraps
from flask import redirect, render_template, request, session, flash


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrap


def apology(msg):
    return render_template("apology.html", errorMessage=msg)