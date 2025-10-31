# app.py (simplified, SQLite fallback)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import sqlite3
import os
from config import DB

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

def get_sqlite_conn():
    path = DB.get("sqlite_path")
    if not path:
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB if sqlite
def init_db():
    if DB.get("sqlite_path"):
        conn = get_sqlite_conn()
        with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

@app.route("/")
def root():
    # optional: serve frontend index
    return send_from_directory(app.static_folder, "index.html")

# Example: register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    role = data.get("role")
    password = hashlib.sha256(data.get("password", "").encode()).hexdigest()

    conn = get_sqlite_conn()
    if conn is None:
        return jsonify({"message":"DB not configured"}), 500
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name,email,phone,role,password) VALUES (?, ?, ?, ?, ?)",
                    (name,email,phone,role,password))
        conn.commit()
        return jsonify({"message":"Registration successful ✅"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"message":"Email already registered ⚠️"}), 400
    finally:
        conn.close()

# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = hashlib.sha256(data.get("password","").encode()).hexdigest()
    conn = get_sqlite_conn()
    if conn is None:
        return jsonify({"message":"DB not configured"}), 500
    cur = conn.cursor()
    cur.execute("SELECT id,name,email,phone,role FROM users WHERE email=? AND password=?", (email,password))
    row = cur.fetchone()
    conn.close()
    if row:
        user = dict(row)
        return jsonify({"message":"Login successful ✅","user": user}), 200
    return jsonify({"message":"Invalid credentials ❌"}), 401

# add_job
@app.route("/add_job", methods=["POST"])
def add_job():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    company = data.get("company")
    location = data.get("location")
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs (title,description,company,location) VALUES (?,?,?,?)",
                (title,description,company,location))
    conn.commit()
    conn.close()
    return jsonify({"message":"Job added successfully ✅"}), 200

# job list
@app.route("/jobs", methods=["GET"])
def get_jobs():
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    jobs = [dict(r) for r in rows]
    return jsonify(jobs), 200

# single job
@app.route("/jobs/<int:id>", methods=["GET"])
def get_job_details(id):
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row)), 200
    return jsonify({"message":"Job not found"}), 404

# rentals endpoints (similar to jobs)...
@app.route("/add_rental", methods=["POST"])
def add_rental():
    data = request.get_json()
    title = data.get("title"); description = data.get("description")
    price = data.get("price"); location = data.get("location")
    conn = get_sqlite_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO rentals (title,description,price,location) VALUES (?,?,?,?)",
                (title,description,price,location))
    conn.commit(); conn.close()
    return jsonify({"message":"Rental added successfully ✅"}), 200

@app.route("/rentals", methods=["GET"])
def get_rentals():
    conn = get_sqlite_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM rentals ORDER BY created_at DESC")
    rows = cur.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows]), 200

@app.route("/rentals/<int:id>", methods=["GET"])
def get_rental_details(id):
    conn = get_sqlite_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM rentals WHERE id=?", (id,))
    row = cur.fetchone(); conn.close()
    if row: return jsonify(dict(row)), 200
    return jsonify({"message":"Rental not found"}), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)





















