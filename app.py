from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import hashlib
import os

app = Flask(__name__, template_folder="templates")  # Ensure Flask finds your HTML files
CORS(app)

# --- DATABASE CONFIGURATION ---
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Parlapalli@56",  # ⚠️ Use .env file in production
    "database": "apnabridge"
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("🔥 Database connection error:", err)
        return None


# ---------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"message": "ApnaBridge Backend Connected ✅"})


# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        role = data.get("role")
        password = hashlib.sha256(data.get("password", "").encode()).hexdigest()

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, phone, role, password) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, role, password)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Registration successful ✅"}), 200

    except mysql.connector.IntegrityError:
        return jsonify({"message": "Email already registered ⚠️"}), 400
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = hashlib.sha256(data.get("password", "").encode()).hexdigest()

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            user.pop('password', None)
            return jsonify({"message": "Login successful ✅", "user": user}), 200
        else:
            return jsonify({"message": "Invalid email or password ❌"}), 401
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()
        email = data.get("email")
        new_password = data.get("new_password")

        if not email or not new_password:
            return jsonify({"message": "Email and new password required ⚠️"}), 400

        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"message": "Email not found ❌"}), 404

        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Password reset successful ✅"}), 200

    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- ADD JOB ----------------
@app.route("/add_job", methods=["POST"])
def add_job():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        company = data.get("company")
        location = data.get("location")

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, company, location) VALUES (%s, %s, %s, %s)",
            (title, description, company, location)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Job added successfully ✅"}), 200
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- ADD RENTAL ----------------
@app.route("/add_rental", methods=["POST"])
def add_rental():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        price = data.get("price")
        location = data.get("location")

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rentals (title, description, price, location) VALUES (%s, %s, %s, %s)",
            (title, description, price, location)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Rental added successfully ✅"}), 200
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- GET ALL JOBS ----------------
@app.route("/jobs", methods=["GET"])
def get_jobs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(jobs), 200
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- GET SINGLE JOB DETAILS ----------------
@app.route("/jobs/<int:id>", methods=["GET"])
def get_job_details(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs WHERE id=%s", (id,))
        job = cursor.fetchone()
        cursor.close()
        conn.close()
        if job:
            return jsonify(job), 200
        return jsonify({"message": "Job not found"}), 404
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- GET ALL RENTALS ----------------
@app.route("/rentals", methods=["GET"])
def get_rentals():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rentals ORDER BY created_at DESC")
        rentals = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rentals), 200
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- GET SINGLE RENTAL DETAILS ----------------
@app.route("/rentals/<int:id>", methods=["GET"])
def get_rental_details(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rentals WHERE id=%s", (id,))
        rental = cursor.fetchone()
        cursor.close()
        conn.close()
        if rental:
            return jsonify(rental), 200
        return jsonify({"message": "Rental not found"}), 404
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- TRENDING ----------------
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
        trending = cursor.fetchall()

        for item in trending:
            if item['type'] == 'job':
                item['url'] = f"/job_details?id={item['id']}"
            else:
                item['url'] = f"/rental_details?id={item['id']}"

        cursor.close()
        conn.close()
        return jsonify(trending), 200
    except Exception as e:
        print("🔥 SERVER ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ---------------- HTML ROUTES ----------------
@app.route("/job_details")
def job_details_page():
    job_id = request.args.get("id")
    return render_template("job_details.html", job_id=job_id)


@app.route("/rental_details")
def rental_details_page():
    rental_id = request.args.get("id")
    return render_template("rental_details.html", rental_id=rental_id)


@app.route("/reset")
def reset_page():
    return render_template("reset_password.html")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)






















