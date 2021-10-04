import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from gen import gen_coords, get_distances, check_risk, gen_future_pos, last_modified

app = Flask(__name__)


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
def form():
    coords, satellites, num = gen_coords()
    if request.method == "POST":
        cantidad = int(request.form.get('cantidad'))
        if(cantidad > num):
            cantidad = num
        dt = datetime.now()
        return render_template("total.html", debris=coords, cantidad=cantidad, dt=dt)
    else:
        return render_template("form.html")

@app.route("/future", methods=["GET", "POST"])
def future():
    if request.method == "POST":
        gen_future_pos()
        flash('Updated!')
    return render_template("future.html")

@app.route("/", methods=["GET", "POST"])
def login():
    return redirect("/form")

@app.route("/collisions")
def closeness():
    coords, satellites, amount = gen_coords()
    risk, num = check_risk(amount)
    dt = last_modified()
    return render_template("collisions.html", risk=risk, num=num, dt=dt)

@app.route("/distances")
def distances():
    dt = datetime.now()
    print(dt)
    nearest, amount = get_distances()
    return render_template("historial.html", nearest=nearest, amount=amount, dt=dt)