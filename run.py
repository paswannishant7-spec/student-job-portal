#!/usr/bin/env python3
"""
run.py – initialises the database and starts the Flask dev server.
Use this only for LOCAL development:  python run.py
For production / Render, gunicorn uses app.py directly (via Procfile).
"""
import os
from app import app, init_db, UPLOAD_FOLDER

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    print("✅ Database initialised.")
    print("🚀 Starting development server at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
