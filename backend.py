from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect("waste.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE TABLES
conn = get_db()

conn.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS reports(
id INTEGER PRIMARY KEY AUTOINCREMENT,
location TEXT,
description TEXT,
image TEXT,
status TEXT,
username TEXT
)
""")

conn.commit()
conn.close()


@app.route("/")
def home():
    return redirect("/signup")


# SIGNUP
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        conn.execute("INSERT INTO users(username,password) VALUES (?,?)",(username,password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username

            if username == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/dashboard")

        return "Invalid Credentials ❌"

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# REPORT
@app.route("/report", methods=["GET","POST"])
def report():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        location = request.form["location"]
        description = request.form["description"]
        image = request.files["image"]

        filename = ""

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
        conn.execute(
            "INSERT INTO reports(location,description,image,status,username) VALUES (?,?,?,?,?)",
            (location,description,filename,"Pending",session["user"])
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("report.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    if session["user"] == "admin":
        # admin sees all
        reports = conn.execute("SELECT * FROM reports").fetchall()
    else:
        # user sees only their reports
        reports = conn.execute(
            "SELECT * FROM reports WHERE username=?",
            (session["user"],)
        ).fetchall()

    conn.close()

    return render_template("dashboard.html", reports=reports)


# DELETE (admin only)
@app.route("/delete/<int:id>")
def delete(id):

    if "user" not in session or session["user"] != "admin":
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM reports WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(debug=True)