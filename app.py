from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from authlib.integrations.flask_client import OAuth  # ✅ added
import os

# ---------------- APP SETUP ----------------
app = Flask(__name__, template_folder="templates")
CORS(app)
app.secret_key = "super_secret_key"

# ✅ GOOGLE OAUTH CONFIG
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='183402241443-mno35b8tj1gj92rjo7t56lcae69tjj4m.apps.googleusercontent.com',
    client_secret='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',  # replace this
    # Let Authlib auto-discover endpoints (this provides jwks_uri too)
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

# ---------------- DATABASE CONFIG ----------------
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Parlapalli@56",
    "database": "apnabridge"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("🔥 Database connection error:", err)
        return None

# ---------------- EMAIL SETTINGS ----------------
SENDER_EMAIL = "ganeshsai@nuevostech.com"
SENDER_PASSWORD = "myrvnqpycpouccwb"  # App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_otp(receiver_email, otp):
    subject = "Your ApnaBridge OTP"
    body = f"Hello,\n\nYour one-time password (OTP) for ApnaBridge is: {otp}\n\nThis OTP is valid for 2 minutes.\n\n- ApnaBridge Security Team"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ OTP sent to {receiver_email}")
        return True
    except Exception as e:
        print("🔥 Email sending error:", e)
        return False

# ---------------- HELPERS ----------------
def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()

def now_utc():
    return datetime.now()

# ---------------- MEMORY STORE ----------------
active_otps = {}
otp_store = {}
verified_emails = set()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return jsonify({"message": "ApnaBridge Backend Connected ✅"})

# ---- LOGIN ----
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = hash_password(data.get("password", ""))

        if not (email and password):
            return jsonify({"message": "Email and password required"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"message": "Invalid email or password ❌"}), 401

        otp = str(random.randint(100000, 999999))
        expiry = now_utc() + timedelta(minutes=2)
        active_otps[email] = {"otp": otp, "expires": expiry, "purpose": "login"}

        if send_email_otp(email, otp):
            return jsonify({"message": "OTP sent to your email ✅", "otp_required": True, "email": email}), 200
        else:
            return jsonify({"message": "Failed to send OTP ❌"}), 500

    except Exception as e:
        print("🔥 LOGIN ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ---- VERIFY LOGIN OTP ----
@app.route("/verify_email_otp", methods=["POST"])
def verify_email_otp():
    try:
        data = request.get_json()
        email = data.get("email")
        otp = data.get("otp")

        record = active_otps.get(email)
        if not record:
            return jsonify({"message": "No OTP found for this email ❌"}), 400

        if now_utc() > record["expires"]:
            active_otps.pop(email, None)
            return jsonify({"message": "OTP expired ⏰"}), 400

        if record["otp"] == otp:
            active_otps.pop(email, None)
            return jsonify({"message": "✅ OTP verified successfully!"}), 200
        else:
            return jsonify({"message": "❌ Invalid OTP"}), 400

    except Exception as e:
        print("🔥 VERIFY OTP ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ---- REGISTER ----
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        raw_password = data.get("password", "")
        name = data.get("name", "")
        phone = data.get("phone", "")
        role = data.get("role", "user")

        if not email or not raw_password:
            return jsonify({"message": "Email and password required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing = cursor.fetchone()
        cursor.close()
        conn.close()

        if existing:
            return jsonify({"message": "Email already registered ⚠️"}), 400

        otp = str(random.randint(100000, 999999))
        expiry = now_utc() + timedelta(minutes=2)
        active_otps[email] = {
            "otp": otp,
            "expires": expiry,
            "purpose": "register",
            "meta": {"name": name, "phone": phone, "role": role, "password": raw_password}
        }

        if send_email_otp(email, otp):
            return jsonify({"message": "OTP sent to your email ✅", "otp_required": True, "email": email}), 200
        else:
            active_otps.pop(email, None)
            return jsonify({"message": "Failed to send OTP ❌"}), 500

    except Exception as e:
        print("🔥 REGISTER ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ---- VERIFY REGISTER OTP ----
@app.route("/verify_register_otp", methods=["POST"])
def verify_register_otp():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        otp = data.get("otp")

        record = active_otps.get(email)
        if not record:
            return jsonify({"message": "No OTP found for this email ❌"}), 400

        if now_utc() > record["expires"]:
            active_otps.pop(email, None)
            return jsonify({"message": "OTP expired ⏰"}), 400

        if record["otp"] != otp:
            return jsonify({"message": "Invalid OTP ❌"}), 400

        meta = record.get("meta", {})
        name = meta.get("name", "")
        phone = meta.get("phone", "")
        role = meta.get("role", "user")
        raw_password = meta.get("password", "")
        hashed_pw = hash_password(raw_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, phone, role, password, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, email, phone, role, hashed_pw, now_utc())
        )
        conn.commit()
        cursor.close()
        conn.close()

        active_otps.pop(email, None)
        return jsonify({"message": "Registration successful ✅"}), 200

    except Exception as e:
        print("🔥 VERIFY REGISTER OTP ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ---- GOOGLE LOGIN (REDIRECT + CALLBACK) ----
@app.route("/login/google")
def login_google():
    redirect_uri = url_for("authorize_google", _external=True)
    return google.authorize_redirect(redirect_uri)

# --- ALIAS ROUTE: keep your frontend's /google_login working ---
@app.route("/google_login")
def google_login_alias():
    return redirect(url_for("login_google", _external=True))

@app.route("/callback")
def authorize_google():
    token = google.authorize_access_token()

    # ✅ FIX for InvalidClaimError: allow both valid issuers
    user_info = google.parse_id_token(
        token,
        claims_options={
            "iss": {"values": ["https://accounts.google.com", "accounts.google.com"]}
        }
    )

    email = user_info["email"]
    name = user_info.get("name", "User")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, "google_oauth")
        )
        conn.commit()

    cursor.close()
    conn.close()

    session["user_email"] = email
    return redirect("http://127.0.0.1:5500/index.html")  # ✅ frontend redirect to home after Google login

# ---- RESET PASSWORD ----
@app.route("/send_reset_otp", methods=["POST"])
def send_reset_otp():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    if send_email_otp(email, otp):
        return jsonify({"message": "✅ OTP sent to your email"}), 200
    else:
        return jsonify({"message": "❌ Failed to send OTP"}), 500

@app.route("/verify_reset_otp", methods=["POST"])
def verify_reset_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    if otp_store.get(email) == otp:
        verified_emails.add(email)
        return jsonify({"message": "✅ OTP verified successfully"}), 200
    else:
        return jsonify({"message": "❌ Invalid OTP"}), 400

@app.route("/reset_password_confirm", methods=["POST"])
def reset_password_confirm():
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("new_password")

    if email not in verified_emails:
        return jsonify({"message": "⚠️ OTP not verified"}), 400

    hashed_pw = hash_password(new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
    conn.commit()
    cursor.close()
    conn.close()

    verified_emails.discard(email)
    otp_store.pop(email, None)
    return jsonify({"message": "✅ Password reset successfully"}), 200

# ---- JOBS ----
@app.route("/add_job", methods=["POST"])
def add_job():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        company = data.get("company")
        location = data.get("location")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (title, description, company, location, created_at) VALUES (%s, %s, %s, %s, %s)",
                       (title, description, company, location, now_utc()))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Job added successfully ✅"}), 200
    except Exception as e:
        print("🔥 ADD JOB ERROR:", e)
        return jsonify({"message": "Server error"}), 500

@app.route("/add_rental", methods=["POST"])
def add_rental():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        price = data.get("price")
        location = data.get("location")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rentals (title, description, price, location, created_at) VALUES (%s, %s, %s, %s, %s)",
                       (title, description, price, location, now_utc()))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Rental added successfully ✅"}), 200
    except Exception as e:
        print("🔥 ADD RENTAL ERROR:", e)
        return jsonify({"message": "Server error"}), 500

@app.route("/jobs", methods=["GET"])
def get_jobs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        print("🔥 GET JOBS ERROR:", e)
        return jsonify({"message": "Server error"}), 500

@app.route("/rentals", methods=["GET"])
def get_rentals():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rentals ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        print("🔥 GET RENTALS ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ------------------ ADDED: single-item endpoints ------------------
# (these routes are added so frontend fetch("/jobs/<id>") and fetch("/rentals/<id>") succeed)

@app.route("/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        conn.close()
        if not job:
            return jsonify({"message": "Job not found"}), 404
        return jsonify(job), 200
    except Exception as e:
        print("🔥 GET JOB ERROR:", e)
        return jsonify({"message": "Server error"}), 500

@app.route("/rentals/<int:rental_id>", methods=["GET"])
def get_rental(rental_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rentals WHERE id = %s", (rental_id,))
        rental = cursor.fetchone()
        cursor.close()
        conn.close()
        if not rental:
            return jsonify({"message": "Rental not found"}), 404
        return jsonify(rental), 200
    except Exception as e:
        print("🔥 GET RENTAL ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# -------------------------------------------------------------------

@app.route("/trending", methods=["GET"])
def get_trending():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            (SELECT id, title, description, 'job' AS type, created_at FROM jobs ORDER BY created_at DESC LIMIT 3)
            UNION
            (SELECT id, title, description, 'rental' AS type, created_at FROM rentals ORDER BY created_at DESC LIMIT 3)
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        for item in rows:
            if item["type"] == "job":
                item["url"] = f"/job_details?id={item['id']}"
            else:
                item["url"] = f"/rental_details?id={item['id']}"
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        print("🔥 TRENDING ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# ---- TEMPLATES ----
@app.route("/job_details")
def job_details_page():
    job_id = request.args.get("id")
    return render_template("job_details.html", job_id=job_id)

@app.route("/rental_details")
def rental_details_page():
    rental_id = request.args.get("id")
    return render_template("rental_details.html", rental_id=rental_id)

# ---- RUN APP ----
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


















