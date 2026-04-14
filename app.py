import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_from_directory, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ──────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "student_job_portal_secret_2024"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max

# Admin credentials
ADMIN_EMAIL = "admin@portal.com"
ADMIN_PASSWORD = "Admin@123"

# ──────────────────────────────────────────────
# DATABASE INIT (FIX FOR RENDER)
# ──────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            salary TEXT,
            description TEXT NOT NULL,
            posted_date TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            resume TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # Seed jobs only once
    count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        db.executemany("""
            INSERT INTO jobs (title, company, location, salary, description, posted_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("Computer Operator", "TechSoft Pvt. Ltd.", "Delhi", "₹15,000 – ₹20,000/month",
             "MS Office, typing skills required.", datetime.now().strftime("%Y-%m-%d")),
            ("Data Entry Executive", "InfoData Solutions", "Noida", "₹12,000 – ₹18,000/month",
             "Excel, accuracy required.", datetime.now().strftime("%Y-%m-%d")),
            ("Web Developer", "DigiCreate", "Faridabad", "₹18,000 – ₹25,000/month",
             "HTML, CSS, JS basics.", datetime.now().strftime("%Y-%m-%d"))
        ])

    db.commit()
    db.close()

# 🔥 IMPORTANT FIX: RUN DB ON START (RENDER SAFE)
with app.app_context():
    init_db()

# ──────────────────────────────────────────────
# DB HELPERS
# ──────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ──────────────────────────────────────────────
# UTILITIES
# ──────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].lower()
        password = request.form["password"]

        db = get_db()
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            flash("User already exists")
            return redirect(url_for("login"))

        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
            (name, email, generate_password_hash(password))
        )
        db.commit()

        flash("Registered successfully")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template("dashboard.html", jobs=jobs)

@app.route("/jobs")
def jobs():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template("jobs.html", jobs=jobs)

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db()
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    apps = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

    return render_template("admin.html", users=users, jobs=jobs, apps=apps)

# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)