import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from gen import login_required, gen_coords, get_distances, check_risk

app = Flask(__name__)

conn = sqlite3.connect('debris.db')
cur = conn.cursor()

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/form", methods=["GET", "POST"])
@login_required
def form():
    coords, satellites, num = gen_coords()
    if request.method == "POST":
        cantidad = int(request.form.get('cantidad'))
        return render_template("total.html", debris=coords, cantidad=cantidad)
    else:
        return render_template("form.html")


@app.route("/", methods=["GET", "POST"])
def login():
    conn = sqlite3.connect('debris.db')
    cur = conn.cursor()
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Falta información', 'error')
            return render_template("login.html")

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("Falta información", 'error')
            return render_template("login.html")

        # Query database for username
        cur.execute("SELECT * FROM users WHERE username = :username", {"username" : request.form.get("username")})
        rows = cur.fetchall()

        # Ensure username exists and password is correct
        if len(rows) < 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            flash("Información incoherente!", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        conn.commit()
        conn.close()
        # Redirect user to home page
        return redirect("/form")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        conn.commit()
        conn.close()
        return render_template("login.html")



@app.route("/logout")
def logout():
    conn = sqlite3.connect('sistemas.db')
    db = conn.cursor()
    """Log user out"""

    # Forget any user_id
    session.clear()

    conn.close()
    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    conn = sqlite3.connect('debris.db')
    cur = conn.cursor()

    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        """ Missing information"""
        if not request.form.get("username"):
            flash("Falta información", 'error')
            return render_template("register.html")
        if not request.form.get("password"):
            flash("Falta información", 'error')
            return render_template("register.html")
        if not request.form.get("confirmation"):
            flash("Falta información", 'error')
            return render_template("register.html")

        """ Query database"""
        cur.execute("SELECT * FROM users WHERE username =:username", {"username" : request.form.get("username")})
        rows = cur.fetchall()

        """ If finds already existing username"""
        if len(rows) != 0:
            flash("Usuario existente", 'error')
            return render_template("register.html")
        """ If passwords don't match"""
        if request.form.get("password") != request.form.get("confirmation"):
            flash("Información incoherente!", 'error')
            return render_template("register.html")

        cur.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                {"username" : request.form.get("username"), "hash" : generate_password_hash(request.form.get("password"))})

        flash("Registered!")

        conn.commit()
        conn.close()

        return redirect("/")



@app.route("/collisions")
@login_required
def closeness():
    coords, satellites, amount = gen_coords()
    risk, num = check_risk(amount)
    '''for i in range(num):
        print(num)
        risk['name1'].append(satellites['name'][risk['deb1']])
        risk['name2'].append(satellites['name'][risk['deb2']])'''
    return render_template("collisions.html", risk=risk, num=num)

@app.route("/distances")
@login_required
def distances():
    nearest, amount = get_distances()
    return render_template("historial.html", nearest=nearest, amount=amount)