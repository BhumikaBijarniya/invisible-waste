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


# -------- CREATE TABLES --------
conn = get_db()

conn.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
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


# -------- HOME --------
@app.route("/")
def home():
    return redirect("/login")


# -------- SIGNUP --------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (username,password)
            )
            conn.commit()
        except:
            return "User already exists ❌"

        conn.close()
        return redirect("/login")

    return render_template("signup.html")


# -------- LOGIN --------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # 👑 ADMIN LOGIN
        if username == "bhumikabijarniya" and password == "bijarniya":
            session["username"] = username
            return redirect("/dashboard")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        conn.close()

        if user:
            if user["password"] == password:
                session["username"] = username
                return redirect("/report")
            else:
                return "Wrong Password ❌"
        else:
            return "User not found ❌"

    return render_template("login.html")


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------- REPORT --------
@app.route("/report", methods=["GET","POST"])
def report():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        location = request.form["location"]
        description = request.form["description"]
        image = request.files["image"]
        latitude = request.form.get("latitude")
longitude = request.form.get("longitude")

        filename = ""

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
       conn.execute(
    "INSERT INTO reports(location,description,image,status,username,latitude,longitude) VALUES (?,?,?,?,?,?,?)",
    (location, description, filename, "Pending", session["username"], latitude, longitude)
)
        conn.commit()
        conn.close()

        # 👇 FIXED REDIRECT
        if session["username"] == "bhumikabijarniya":
            return redirect("/dashboard")
        else:
            return redirect("/my_reports")

    return render_template("report.html")


# -------- USER REPORTS --------
@app.route("/my_reports")
def my_reports():

    if "username" not in session:
        return redirect("/login")

    conn = get_db()

    username = session.get("username")

    reports = conn.execute(
        "SELECT * FROM reports WHERE username=?",
        (username,)
    ).fetchall()

    conn.close()

    return render_template("my_reports.html", reports=reports)


# -------- ADMIN DASHBOARD --------
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    if session["username"] != "bhumikabijarniya":
        return redirect("/login")

    conn = get_db()

    reports = conn.execute("SELECT * FROM reports").fetchall()

    conn.close()

    return render_template("dashboard.html", reports=reports)


# -------- DELETE (ADMIN ONLY) --------
@app.route("/delete/<int:id>")
def delete(id):

    if session.get("username") != "bhumikabijarniya":
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM reports WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- UPDATE STATUS (ADMIN ONLY) --------
@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    if session.get("username") != "bhumikabijarniya":
        return redirect("/login")

    conn = get_db()

    conn.execute(
        "UPDATE reports SET status=? WHERE id=?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
