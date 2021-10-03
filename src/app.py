import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from gen import login_required, gen_coords

wd = '../lib/'
debris_file = wd + 'debris.db'

app = Flask(__name__)

conn = sqlite3.connect(debris_file)
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

'''def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"'''


@app.route("/form", methods=["GET", "POST"])
@login_required
def form():
    coords = gen_coords()
    if request.method == "POST":
        cantidad = int(request.form.get("cantidad"))
        latitudes = coords['lat']
        longitudes = coords['long']
        elevacion = coords['elev']
        return render_template("total.html", debris=coords, cantidad=cantidad)
        return render_template("form.html")
    else:
        return render_template("form.html")


@app.route("/", methods=["GET", "POST"])
def login():
    conn = sqlite3.connect(debris_file)
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
    conn = sqlite3.connect(debris_file)
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

        '''special_char = set("@_!#$%^&*()<>?/|}{~:")
        numeric_char = set("1234567890")

        if not(any((c in special_char) for c in str(request.form.get("password")))):
            flash("Contraseña inválida", 'error')
            return render_template("register.html")

        if not(any((c in numeric_char) for c in str(request.form.get("password")))):
            flash("Contraseña inválida", 'error')
            return render_template("register.html")

        if len(request.form.get("password")) < 8:
            flash("Contraseña inválida", 'error')
            return render_template("register.html")'''

        cur.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                {"username" : request.form.get("username"), "hash" : generate_password_hash(request.form.get("password"))})

        flash("Registered!")

        conn.commit()
        conn.close()

        return redirect("/")



@app.route("/history")
@login_required
def history():
    conn = sqlite3.connect(debris_file)
    cur = conn.cursor()

    orders = []

    cur.execute("SELECT orderID FROM records WHERE userID=:userID", {"userID" : session["user_id"]})
    o = cur.fetchall()
    for item in o:
        orders.append(item[0])

    cur.execute("SELECT COUNT(orderID) FROM records WHERE userID=:userID", {"userID" : session["user_id"]})
    number = cur.fetchall()[0][0]
    info = []

    for order in orders:

        cur.execute("SELECT lineas FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        lineas = cur.fetchall()[0][0]

        cur.execute("SELECT trafos FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        trafos = cur.fetchall()[0][0]

        barras = cur.execute("SELECT barras FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        barras = cur.fetchall()[0][0]

        timestamp = cur.execute("SELECT timestamp FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        timestamp = cur.fetchall()[0][0]

        precio = cur.execute("SELECT precio FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        precio = cur.fetchall()[0][0]

        nombre = cur.execute("SELECT nombre FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        nombre = cur.fetchall()[0][0]

        adicional = cur.execute("SELECT adicional FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        adicional = cur.fetchall()[0][0]

        pais = cur.execute("SELECT pais FROM records WHERE userID=:userID AND orderID=:orderID", {"userID" : session["user_id"], "orderID" : order})
        pais = cur.fetchall()[0][0]

        data = {}
        data['precio'] = precio
        data['lineas'] = lineas
        data['trafos'] = trafos
        data['barras'] = barras
        data['timestamp'] = timestamp
        data['nombre'] = nombre
        data['adicional'] = adicional
        data['pais'] = pais

        info.append(data)

    conn.commit()

    conn.close()

    return render_template("historial.html", number=number, info=info)