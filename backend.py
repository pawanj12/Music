from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "database.db"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# CREATE DATABASE TABLE
# -----------------------------
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            instrument TEXT NOT NULL,
            age INTEGER,
            preferred_time TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# CONTACT PAGE
# -----------------------------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# -----------------------------
# CONTACT FORM SUBMISSION
# -----------------------------
@app.route("/submit-enquiry", methods=["POST"])
def submit_enquiry():

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    instrument = request.form.get("instrument", "").strip()
    age = request.form.get("age", "").strip()
    preferred_time = request.form.get("preferred_time", "").strip()
    message = request.form.get("message", "").strip()

    # Basic validation
    if not full_name:
        return "Full name is required", 400

    if not phone:
        return "Phone number is required", 400

    if not email:
        return "Email is required", 400

    if not instrument:
        return "Instrument is required", 400

    # Convert age safely
    age_value = None

    if age:
        try:
            age_value = int(age)
        except ValueError:
            return "Age must be a number", 400

    # Save to database
    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO enquiries
        (
            full_name,
            phone,
            email,
            instrument,
            age,
            preferred_time,
            message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        full_name,
        phone,
        email,
        instrument,
        age_value,
        preferred_time,
        message
    ))

    enquiry_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print("New enquiry received:", enquiry_id)

    return f"""
        <h1>Demo request received!</h1>
        <p>Thank you, {full_name}.</p>
        <p>Your enquiry ID is: {enquiry_id}</p>
        <p>We will contact you soon.</p>
        <br>
        <a href="/contact">Back to Contact</a>
    """


# -----------------------------
# START APPLICATION
# -----------------------------
if __name__ == "__main__":
    init_db()

    app.run(
        debug=True
    )