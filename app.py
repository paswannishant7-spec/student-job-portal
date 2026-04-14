import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

# ─────────────────────────────
# APP SETUP
# ─────────────────────────────
app = Flask(__name__)
app.secret_key = "student_job_portal_secret_2024"

# IMPORTANT: Render-safe DB path
DATABASE = "database.db"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ADMIN_EMAIL = "admin@portal.com"
ADMIN_PASSWORD = "Admin@123"


# ─────────────────────────────
# DATABASE INIT
# ─────────────────────────────
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            description TEXT,
            posted_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            resume TEXT,
            date TEXT
        )
    """)

    # Seed jobs once
    count = cur.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        cur.executemany("""
            INSERT INTO jobs (title, company, location, salary, description, posted_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("Computer Operator", "TechSoft", "Delhi", "15k-20k", "Basic MS Office", datetime.now().strftime("%Y-%m-%d")),
            ("Data Entry", "InfoData", "Noida", "12k-18k", "Typing work", datetime.now().strftime("%Y-%m-%d")),
            ("Web Developer", "DigiCreate", "Delhi", "18k-25k", "HTML CSS JS", datetime.now().strftime("%Y-%m-%d")),
        ])

    conn.commit()
    conn.close()


# Run DB safely
init_db()


# ─────────────────────────────
# DB CONNECTION
# ─────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e):
    db = g.pop("db", None)
    if db:
        db.close()


# ─────────────────────────────
# ROUTES
# ─────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].lower()
        password = request.form["password"]

        db = get_db()

        user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if user:
            flash("User already exists")
            return redirect(url_for("login"))

        db.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password))
        )
        db.commit()

        flash("Registered successfully")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        # ADMIN LOGIN
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["user_id"] = 0
            session["role"] = "admin"
            session["name"] = "Admin"
            return redirect(url_for("admin_dashboard"))

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid login")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template("dashboard.html", jobs=jobs)


# JOBS
@app.route("/jobs")
def jobs():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template("jobs.html", jobs=jobs)


# ADMIN
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db()

    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    apps = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

    return render_template("admin.html", users=users, jobs=jobs, apps=apps)


# ─────────────────────────────
# MAIN RUN
# ─────────────────────────────
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)