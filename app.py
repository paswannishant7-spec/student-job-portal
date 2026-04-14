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

# Admin credentials (hardcoded as required)
ADMIN_EMAIL = "admin@portal.com"
ADMIN_PASSWORD = "Admin@123"

# ──────────────────────────────────────────────
# Database Helpers
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

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'student'
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            company     TEXT NOT NULL,
            location    TEXT NOT NULL,
            salary      TEXT,
            description TEXT NOT NULL,
            posted_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            job_id      INTEGER NOT NULL,
            resume      TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id)  REFERENCES jobs(id)
        );
    """)
    # Seed some sample jobs if none exist
    count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        sample_jobs = [
            ("Computer Operator", "TechSoft Pvt. Ltd.", "Delhi", "₹15,000 – ₹20,000/month",
             "We need a qualified Computer Operator with basic typing, MS Office, and internet skills. ITI COPA pass-outs are preferred.", datetime.now().strftime("%Y-%m-%d")),
            ("Data Entry Executive", "InfoData Solutions", "Noida", "₹12,000 – ₹18,000/month",
             "Accurate data entry, maintaining records in Excel and Tally. Must type at least 30 WPM.", datetime.now().strftime("%Y-%m-%d")),
            ("Junior Web Developer", "DigiCreate Agency", "Faridabad", "₹18,000 – ₹25,000/month",
             "Basic HTML, CSS, and JavaScript knowledge required. Training will be provided for freshers.", datetime.now().strftime("%Y-%m-%d")),
            ("IT Support Executive", "BrightStar Corp.", "Gurugram", "₹14,000 – ₹20,000/month",
             "Handle hardware/software issues, install OS, maintain computers. ITI/Diploma in CS preferred.", datetime.now().strftime("%Y-%m-%d")),
            ("Office Assistant (Computer)", "GreenLeaf Enterprises", "Delhi", "₹10,000 – ₹15,000/month",
             "MS Word, Excel, email handling, internet browsing. Freshers from ITI COPA background welcome.", datetime.now().strftime("%Y-%m-%d")),
        ]
        db.executemany(
            "INSERT INTO jobs (title, company, location, salary, description, posted_date) VALUES (?,?,?,?,?,?)",
            sample_jobs
        )
    db.commit()
    db.close()

# ──────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ──────────────────────────────────────────────
# Public Routes
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        hashed = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
            (name, email, hashed)
        )
        db.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Admin check
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["user_id"] = 0
            session["name"]    = "Administrator"
            session["role"]    = "admin"
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["role"]    = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ──────────────────────────────────────────────
# Student Routes
# ──────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    my_apps    = db.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ?", (session["user_id"],)
    ).fetchone()[0]
    recent_jobs = db.execute(
        "SELECT * FROM jobs ORDER BY id DESC LIMIT 3"
    ).fetchall()
    return render_template("dashboard.html", user=user, total_jobs=total_jobs,
                           my_apps=my_apps, recent_jobs=recent_jobs)

@app.route("/jobs")
@login_required
def jobs():
    db = get_db()
    search = request.args.get("search", "").strip()
    if search:
        all_jobs = db.execute(
            "SELECT * FROM jobs WHERE title LIKE ? OR company LIKE ? OR location LIKE ? ORDER BY id DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        all_jobs = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()

    # Find jobs already applied to by this student
    applied_ids = {
        row["job_id"]
        for row in db.execute(
            "SELECT job_id FROM applications WHERE user_id = ?", (session["user_id"],)
        ).fetchall()
    }
    return render_template("jobs.html", jobs=all_jobs, applied_ids=applied_ids, search=search)

@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
def apply(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("jobs"))

    # Already applied?
    already = db.execute(
        "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
        (session["user_id"], job_id)
    ).fetchone()
    if already:
        flash("You have already applied for this job.", "warning")
        return redirect(url_for("my_applications"))

    if request.method == "POST":
        if "resume" not in request.files:
            flash("No file selected.", "danger")
            return render_template("apply.html", job=job)

        file = request.files["resume"]
        if file.filename == "":
            flash("Please select a resume file.", "danger")
            return render_template("apply.html", job=job)

        if not allowed_file(file.filename):
            flash("Only PDF, DOC, and DOCX files are allowed.", "danger")
            return render_template("apply.html", job=job)

        filename = secure_filename(
            f"user{session['user_id']}_job{job_id}_{file.filename}"
        )
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute(
            "INSERT INTO applications (user_id, job_id, resume, date) VALUES (?, ?, ?, ?)",
            (session["user_id"], job_id, filename, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        db.commit()
        flash("Application submitted successfully! 🎉", "success")
        return redirect(url_for("my_applications"))

    return render_template("apply.html", job=job)

@app.route("/my-applications")
@login_required
def my_applications():
    db = get_db()
    apps = db.execute("""
        SELECT a.id, a.resume, a.date,
               j.title, j.company, j.location, j.salary
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.user_id = ?
        ORDER BY a.id DESC
    """, (session["user_id"],)).fetchall()
    return render_template("my_applications.html", apps=apps)

# ──────────────────────────────────────────────
# Admin Routes
# ──────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    total_jobs     = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_apps     = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    recent_apps    = db.execute("""
        SELECT a.id, a.date, a.resume,
               u.name AS student_name, u.email,
               j.title, j.company
        FROM applications a
        JOIN users u ON a.user_id = u.id
        JOIN jobs  j ON a.job_id  = j.id
        ORDER BY a.id DESC LIMIT 5
    """).fetchall()
    return render_template("admin.html", total_students=total_students,
                           total_jobs=total_jobs, total_apps=total_apps,
                           recent_apps=recent_apps)

@app.route("/admin/jobs")
@admin_required
def admin_jobs():
    db  = get_db()
    all_jobs = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    return render_template("admin_jobs.html", jobs=all_jobs)

@app.route("/admin/add-job", methods=["GET", "POST"])
@admin_required
def add_job():
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        company     = request.form.get("company", "").strip()
        location    = request.form.get("location", "").strip()
        salary      = request.form.get("salary", "").strip()
        description = request.form.get("description", "").strip()

        if not all([title, company, location, description]):
            flash("Title, Company, Location and Description are required.", "danger")
            return render_template("add_job.html")

        db = get_db()
        db.execute(
            "INSERT INTO jobs (title, company, location, salary, description, posted_date) VALUES (?,?,?,?,?,?)",
            (title, company, location, salary, description, datetime.now().strftime("%Y-%m-%d"))
        )
        db.commit()
        flash(f"Job '{title}' added successfully!", "success")
        return redirect(url_for("admin_jobs"))

    return render_template("add_job.html")

@app.route("/admin/delete-job/<int:job_id>", methods=["POST"])
@admin_required
def delete_job(job_id):
    db = get_db()
    db.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    db.commit()
    flash("Job deleted successfully.", "success")
    return redirect(url_for("admin_jobs"))

@app.route("/admin/applications")
@admin_required
def admin_applications():
    db = get_db()
    apps = db.execute("""
        SELECT a.id, a.date, a.resume,
               u.name AS student_name, u.email,
               j.title, j.company, j.location
        FROM applications a
        JOIN users u ON a.user_id = u.id
        JOIN jobs  j ON a.job_id  = j.id
        ORDER BY a.id DESC
    """).fetchall()
    return render_template("admin_applications.html", apps=apps)

@app.route("/admin/download/<filename>")
@admin_required
def download_resume(filename):
    safe = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe, as_attachment=True)

# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
