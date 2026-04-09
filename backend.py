from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from flask import send_from_directory

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -------- DATABASE CONNECTION --------
def get_db():
    conn = psycopg2.connect(
        "postgresql://invisible_waste_db_user:wPba3jUvBiyELSqiWzEv9KSm5it3jZS0@dpg-d7bu2dnafjfc73f7i3t0-a.oregon-postgres.render.com:5432/invisible_waste_db"
    )
    return conn


# -------- CREATE TABLE --------
conn = get_db()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id SERIAL PRIMARY KEY,
username TEXT UNIQUE,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
id SERIAL PRIMARY KEY,
location TEXT,
description TEXT,
image TEXT,
status TEXT,
username TEXT,
latitude TEXT,
longitude TEXT
)
""")

conn.commit()
cur.close()
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
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password) VALUES (%s,%s)",
                (username,password)
            )
            conn.commit()
        except:
            return "User already exists ❌"

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# -------- LOGIN --------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # ADMIN LOGIN
        if username == "bhumikabijarniya" and password == "bijarniya":
            session["username"] = username
            return redirect("/dashboard")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            if user[2] == password:
                session["username"] = username
                return redirect("/report")
            else:
                return "Wrong Password ❌"
        else:
            return "User not found ❌"

    return render_template("login.html")


# -------- REPORT --------
@app.route("/report", methods=["GET","POST"])
def report():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        location = request.form["location"]
        description = request.form["description"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]

        image = request.files["image"]
        filename = ""

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO reports(location,description,image,status,username,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (location, description, filename, "Pending", session["username"], latitude, longitude)
        )

        conn.commit()
        cur.close()
        conn.close()

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
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports WHERE username=%s", (session["username"],))
    reports = cur.fetchall()

    cur.close()
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
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports")
    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboard.html", reports=reports)


# -------- STATUS UPDATE --------
@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):
    if session.get("username") != "bhumikabijarniya":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE reports SET status=%s WHERE id=%s",
        (status, id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")


# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
