# 🎓 Student Job Portal

A full-stack web application built with **Python Flask**, **SQLite**, and **HTML/CSS**
that lets ITI COPA students register, browse jobs, and apply with resume upload.

---

## 🗂️ Project Structure

```
student-job-portal/
├── app.py              ← Main Flask application (routes + logic)
├── run.py              ← Local development runner
├── requirements.txt    ← Python dependencies
├── Procfile            ← Render/Heroku deployment command
├── database.db         ← SQLite database (auto-created on first run)
├── static/
│   ├── css/style.css   ← All styling
│   └── uploads/        ← Uploaded resumes stored here
└── templates/
    ├── base.html           ← Shared navbar + layout
    ├── index.html          ← Home / landing page
    ├── register.html       ← Student registration
    ├── login.html          ← Login (student + admin)
    ├── dashboard.html      ← Student dashboard
    ├── jobs.html           ← Browse jobs
    ├── apply.html          ← Apply with resume upload
    ├── my_applications.html← Student's applied jobs
    ├── admin.html          ← Admin dashboard
    ├── admin_jobs.html     ← Admin: manage jobs
    ├── add_job.html        ← Admin: add new job
    └── admin_applications.html ← Admin: view all apps + download resumes
```

---

## 💻 Run Locally (Step-by-Step)

### 1. Install Python
Download Python 3.10+ from https://python.org and install it.

### 2. Open Terminal / Command Prompt
Navigate to the project folder:
```
cd student-job-portal
```

### 3. (Optional) Create a Virtual Environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 4. Install Dependencies
```
pip install -r requirements.txt
```

### 5. Run the Application
```
python run.py
```

### 6. Open in Browser
Go to: **http://127.0.0.1:5000**

---

## 🌐 Deploy on Render (Free Hosting)

1. **Create a GitHub repository** and push this project to it.

2. **Go to** https://render.com and sign up (free).

3. Click **New → Web Service**.

4. Connect your GitHub repository.

5. Fill in the settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3

6. Add an **Environment Variable:**
   - Key: `PYTHON_VERSION`   Value: `3.11.0`

7. Click **Create Web Service**.

8. Render will build and deploy your app. You'll get a live URL like:
   `https://student-job-portal.onrender.com`

> ⚠️ **Note:** On Render's free tier, the disk resets when the service restarts.
> This means uploaded resumes may be lost between restarts. For permanent storage,
> use Render's Disk add-on or an external service like Cloudinary.
> The SQLite database will also reset. For persistent data, consider PostgreSQL.

---

## 🔐 Login Credentials

### Student Login
- Register first at `/register`
- Then log in with your email and password

### Admin Login
| Field    | Value              |
|----------|--------------------|
| Email    | admin@portal.com   |
| Password | Admin@123          |

---

## 🗄️ Database Tables

### `users`
| Column   | Type    | Description                  |
|----------|---------|------------------------------|
| id       | INTEGER | Auto-increment primary key   |
| name     | TEXT    | Student's full name          |
| email    | TEXT    | Unique email address         |
| password | TEXT    | Hashed password (bcrypt-like)|
| role     | TEXT    | 'student' (admin is hardcoded)|

### `jobs`
| Column      | Type | Description            |
|-------------|------|------------------------|
| id          | INT  | Primary key            |
| title       | TEXT | Job title              |
| company     | TEXT | Company name           |
| location    | TEXT | Job location           |
| salary      | TEXT | Salary range (optional)|
| description | TEXT | Full job description   |
| posted_date | TEXT | Date posted            |

### `applications`
| Column  | Type | Description                      |
|---------|------|----------------------------------|
| id      | INT  | Primary key                      |
| user_id | INT  | Foreign key → users.id           |
| job_id  | INT  | Foreign key → jobs.id            |
| resume  | TEXT | Saved filename of uploaded resume |
| date    | TEXT | Date and time of application      |

---

## 🔁 Complete User Flow

```
Student registers → Data saved in DB → Student logs in →
Views jobs → Clicks "Apply Now" → Uploads resume →
Application saved in DB → Admin logs in →
Admin sees all applications → Downloads student's resume
```

---

## 📄 Resume Upload – How It Works

1. Student selects a PDF / DOC / DOCX file (max 5 MB)
2. Flask validates the file extension using `allowed_file()`
3. `werkzeug.utils.secure_filename()` sanitises the filename
4. File is saved as `user{id}_job{id}_originalname.pdf` in `static/uploads/`
5. The filename is stored in the `applications` table
6. Admin can download the file from the admin panel

---

## 🔐 Security Features

- **Password hashing** using `werkzeug.security.generate_password_hash`
- **Session-based auth** with Flask sessions
- **File type validation** — only PDF, DOC, DOCX allowed
- **secure_filename** prevents path traversal attacks
- **Max file size** of 5 MB enforced
- **Admin route protection** via `@admin_required` decorator

---

## 💬 Interview Explanation (Simple Version)

> "I built a Student Job Portal using Python Flask as the backend and SQLite as the
> database. Students can register, log in, browse job listings, and apply by uploading
> their resume. The admin can log in with special credentials, post new jobs, delete them,
> and view or download resumes submitted by students. I used werkzeug for password hashing
> to keep passwords secure. The project is deployed on Render using Gunicorn as the
> production server."

---

## 🛠️ Tech Stack Summary

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python 3, Flask                   |
| Frontend   | HTML5, CSS3 (custom)              |
| Database   | SQLite (via Python sqlite3 module)|
| Auth       | Flask sessions + Werkzeug hashing |
| Server     | Gunicorn                          |
| Deployment | Render                            |

---

Built with ❤️ for ITI COPA students preparing for placement.
