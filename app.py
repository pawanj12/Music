from flask import Flask, render_template, request, redirect, url_for, session
import os
import uuid
import mysql.connector

from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_STATUSES = [
    "NEW",
    "CONTACTED",
    "DEMO_SCHEDULED",
    "DEMO_CONFIRMED",
    "DEMO_COMPLETED",
    "ENROLLED",
    "CANCELLED",
    "CLOSED",
]

STUDENT_STATUSES = ["ACTIVE", "INACTIVE"]


# ============================================================
# DATABASE CONNECTION
# ============================================================


def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


# ============================================================
# TIME FORMAT HELPER
# ============================================================


def format_db_time(value):
    """Safely convert MySQL TIME values to HH:MM."""

    if value is None:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    if hasattr(value, "total_seconds"):
        total_seconds = int(value.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    return str(value)[:5]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================


def init_db():
    """Create the application tables that belong to the backend."""

    conn = get_db()
    cursor = conn.cursor()
    database_name = os.getenv("MYSQL_DATABASE")

    # --------------------------------------------------------
    # ROLES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role_name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT IGNORE INTO roles (role_name, description)
        VALUES
            ('SUPER_ADMIN', 'Full access to the entire system'),
            ('MANAGER', 'Manage institute operations'),
            ('EMPLOYEE', 'Manage enquiries, demos and students'),
            ('TEACHER', 'Manage assigned classes, students and attendance')
    """)

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role_id INT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id)
                REFERENCES roles(id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
    """)

    # --------------------------------------------------------
    # DEMO REQUESTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demo_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            demo_id VARCHAR(50) NOT NULL UNIQUE,
            full_name VARCHAR(150) NOT NULL,
            phone VARCHAR(30) NOT NULL,
            email VARCHAR(150) NOT NULL,
            instrument VARCHAR(100) NOT NULL,
            age INT NULL,
            preferred_time VARCHAR(100) NULL,
            message TEXT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'NEW',
            teacher_name VARCHAR(150) NULL,
            teacher_id INT NULL,
            demo_date DATE NULL,
            demo_time TIME NULL,
            created_at DATETIME NOT NULL
        )
    """)

    conn.commit()

    # teacher_id was added later to an existing database.
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = 'demo_requests'
          AND column_name = 'teacher_id'
    """, (database_name,))

    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            ALTER TABLE demo_requests
            ADD COLUMN teacher_id INT NULL AFTER teacher_name
        """)
        conn.commit()

    # Add FK only when it does not already exist.
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.table_constraints
        WHERE constraint_schema = %s
          AND table_name = 'demo_requests'
          AND constraint_name = 'fk_demo_requests_teacher'
    """, (database_name,))

    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            ALTER TABLE demo_requests
            ADD CONSTRAINT fk_demo_requests_teacher
            FOREIGN KEY (teacher_id)
            REFERENCES users(id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
        """)
        conn.commit()

    # --------------------------------------------------------
    # TEACHER PROFILES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            phone VARCHAR(30),
            instrument VARCHAR(100),
            experience_years DECIMAL(4,1) NULL,
            qualification VARCHAR(255),
            bio TEXT,
            joining_date DATE NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_teacher_profiles_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_code VARCHAR(50) NOT NULL UNIQUE,
            full_name VARCHAR(150) NOT NULL,
            phone VARCHAR(30),
            email VARCHAR(150),
            age INT NULL,
            instrument VARCHAR(100),
            teacher_id INT NULL,
            source_enquiry_id INT NULL,
            enrollment_date DATE NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
            notes TEXT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_students_teacher
                FOREIGN KEY (teacher_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                ON UPDATE CASCADE,
            CONSTRAINT fk_students_enquiry
                FOREIGN KEY (source_enquiry_id)
                REFERENCES demo_requests(id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ============================================================
# HOME
# ============================================================


@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# COURSES
# ============================================================


@app.route("/courses")
def courses():
    return render_template("courses.html")


# ============================================================
# CONTACT PAGE
# ============================================================


@app.route("/contact")
def contact():
    submitted = request.args.get("submitted") == "1"
    demo_id = request.args.get("demo_id", "")
    return render_template(
        "contact.html",
        submitted=submitted,
        demo_id=demo_id,
    )


# ============================================================
# SUBMIT ENQUIRY
# ============================================================


@app.route("/submit-enquiry", methods=["POST"])
def submit_enquiry():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    instrument = request.form.get("instrument", "").strip()
    age = request.form.get("age", "").strip()
    preferred_time = request.form.get("preferred_time", "").strip()
    message = request.form.get("message", "").strip()

    if not full_name or not phone or not email or not instrument:
        return render_template(
            "contact.html",
            error="Please fill all required fields.",
        )

    try:
        age_value = int(age) if age else None
    except ValueError:
        return render_template(
            "contact.html",
            error="Please enter a valid age.",
        )

    demo_id = "MIN-" + uuid.uuid4().hex[:8].upper()

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO demo_requests
            (
                demo_id,
                full_name,
                phone,
                email,
                instrument,
                age,
                preferred_time,
                message,
                status,
                created_at
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, 'NEW', %s)
        """, (
            demo_id,
            full_name,
            phone,
            email,
            instrument,
            age_value,
            preferred_time,
            message,
            datetime.now(),
        ))
        conn.commit()
    except mysql.connector.Error:
        conn.rollback()
        cursor.close()
        conn.close()
        return render_template(
            "contact.html",
            error="We could not submit your request. Please try again.",
        )

    cursor.close()
    conn.close()

    return redirect(url_for("contact", submitted="1", demo_id=demo_id))


# ============================================================
# LOGIN
# ============================================================


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="Please enter email and password.",
            )

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                u.id,
                u.full_name,
                u.email,
                u.password_hash,
                u.is_active,
                r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.email = %s
        """, (email,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return render_template("login.html", error="Invalid email or password.")

        if not user["is_active"]:
            return render_template("login.html", error="Your account is inactive.")

        try:
            password_ok = check_password_hash(user["password_hash"], password)
        except Exception:
            password_ok = False

        if not password_ok:
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["user_email"] = user["email"]
        session["role"] = user["role_name"]

        if user["role_name"] == "TEACHER":
            return redirect(url_for("teacher_dashboard"))

        return redirect(url_for("admin_dashboard"))

    return render_template("login.html")


# ============================================================
# ADMIN DASHBOARD
# ============================================================


@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM demo_requests")
    total_enquiries = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM demo_requests
        WHERE status = 'NEW'
    """)
    new_enquiries = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.demo_date,
            dr.demo_time,
            dr.status,
            COALESCE(t.full_name, dr.teacher_name) AS teacher_name
        FROM demo_requests dr
        LEFT JOIN users t ON dr.teacher_id = t.id
        WHERE dr.demo_date = CURDATE()
        ORDER BY dr.demo_time ASC, dr.id DESC
    """)
    todays_demos = cursor.fetchall()

    for demo in todays_demos:
        demo["demo_time_display"] = format_db_time(demo.get("demo_time"))

    cursor.execute("""
        SELECT id, demo_id, full_name, instrument, status, created_at
        FROM demo_requests
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_enquiries = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        total_enquiries=total_enquiries,
        new_enquiries=new_enquiries,
        todays_demos=todays_demos,
        recent_enquiries=recent_enquiries,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="dashboard",
    )


# ============================================================
# ADMIN ROOT
# ============================================================


@app.route("/admin")
def admin():
    return redirect(url_for("admin_dashboard"))


# ============================================================
# ADMIN ENQUIRIES
# ============================================================


@app.route("/admin/enquiries")
def admin_enquiries():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    instrument = request.args.get("instrument", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    period = request.args.get("period", "all").strip()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    per_page = 20
    offset = (page - 1) * per_page
    conditions = []
    params = []

    if q:
        conditions.append("""
            (
                dr.demo_id LIKE %s
                OR dr.full_name LIKE %s
                OR dr.phone LIKE %s
                OR dr.email LIKE %s
                OR dr.instrument LIKE %s
            )
        """)
        search_value = f"%{q}%"
        params.extend([search_value] * 5)

    if status and status in ALLOWED_STATUSES:
        conditions.append("dr.status = %s")
        params.append(status)

    if instrument:
        conditions.append("dr.instrument = %s")
        params.append(instrument)

    if date_from:
        conditions.append("DATE(dr.created_at) >= %s")
        params.append(date_from)

    if date_to:
        conditions.append("DATE(dr.created_at) <= %s")
        params.append(date_to)

    if period == "today":
        conditions.append("DATE(dr.created_at) = CURDATE()")
    elif period == "7days":
        conditions.append("dr.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    elif period == "30days":
        conditions.append("dr.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    elif period == "old":
        conditions.append("dr.created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)")

    where_sql = "WHERE " + " AND ".join(conditions) if conditions else ""

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"""
        SELECT COUNT(*) AS total
        FROM demo_requests dr
        {where_sql}
    """, tuple(params))
    total = cursor.fetchone()["total"]

    total_pages = (total + per_page - 1) // per_page

    data_params = list(params)
    data_params.extend([per_page, offset])

    cursor.execute(f"""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.age,
            dr.preferred_time,
            dr.message,
            dr.status,
            dr.teacher_id,
            dr.teacher_name,
            dr.demo_date,
            dr.demo_time,
            dr.created_at,
            t.full_name AS assigned_teacher
        FROM demo_requests dr
        LEFT JOIN users t ON dr.teacher_id = t.id
        {where_sql}
        ORDER BY dr.id DESC
        LIMIT %s OFFSET %s
    """, tuple(data_params))

    enquiries = cursor.fetchall()

    for enquiry in enquiries:
        enquiry["demo_time_display"] = format_db_time(enquiry.get("demo_time"))

    cursor.execute("""
        SELECT DISTINCT instrument
        FROM demo_requests
        WHERE instrument IS NOT NULL
          AND instrument <> ''
        ORDER BY instrument ASC
    """)
    instruments = [row["instrument"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template(
        "enquiries.html",
        enquiries=enquiries,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        q=q,
        status=status,
        instrument=instrument,
        instruments=instruments,
        date_from=date_from,
        date_to=date_to,
        period=period,
        allowed_statuses=ALLOWED_STATUSES,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="enquiries",
    )


# ============================================================
# ENQUIRY DETAILS
# ============================================================


@app.route("/admin/enquiries/<int:enquiry_id>")
def enquiry_details(enquiry_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.age,
            dr.preferred_time,
            dr.message,
            dr.status,
            dr.teacher_id,
            dr.teacher_name,
            dr.demo_date,
            dr.demo_time,
            dr.created_at,
            t.full_name AS assigned_teacher,
            t.email AS teacher_email
        FROM demo_requests dr
        LEFT JOIN users t ON dr.teacher_id = t.id
        WHERE dr.id = %s
    """, (enquiry_id,))

    enquiry = cursor.fetchone()

    if not enquiry:
        cursor.close()
        conn.close()
        return "Enquiry not found.", 404

    enquiry["demo_time_display"] = format_db_time(enquiry.get("demo_time"))

    cursor.execute("""
        SELECT u.id, u.full_name, u.email
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.role_name = 'TEACHER'
          AND u.is_active = TRUE
        ORDER BY u.full_name ASC
    """)
    teachers = cursor.fetchall()

    cursor.execute("""
        SELECT id, student_code
        FROM students
        WHERE source_enquiry_id = %s
        LIMIT 1
    """, (enquiry_id,))
    converted_student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "enquiry_details.html",
        enquiry=enquiry,
        teachers=teachers,
        converted_student=converted_student,
        allowed_statuses=ALLOWED_STATUSES,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="enquiries",
    )


# ============================================================
# UPDATE ENQUIRY DETAILS
# ============================================================


@app.route("/admin/enquiries/<int:enquiry_id>/update", methods=["POST"])
def update_enquiry(enquiry_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    status = request.form.get("status", "").strip()
    teacher_id = request.form.get("teacher_id", "").strip()
    demo_date = request.form.get("demo_date", "").strip()
    demo_time = request.form.get("demo_time", "").strip()

    if status not in ALLOWED_STATUSES:
        return "Invalid status.", 400

    try:
        teacher_id_value = int(teacher_id) if teacher_id else None
    except ValueError:
        return "Invalid teacher selected.", 400

    try:
        demo_date_value = (
            datetime.strptime(demo_date, "%Y-%m-%d").date()
            if demo_date else None
        )
    except ValueError:
        return "Invalid demo date.", 400

    try:
        demo_time_value = (
            datetime.strptime(demo_time, "%H:%M").time()
            if demo_time else None
        )
    except ValueError:
        return "Invalid demo time.", 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        teacher_name_value = None

        if teacher_id_value:
            cursor.execute("""
                SELECT u.id, u.full_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s
                  AND r.role_name = 'TEACHER'
                  AND u.is_active = TRUE
            """, (teacher_id_value,))

            selected_teacher = cursor.fetchone()

            if not selected_teacher:
                cursor.close()
                conn.close()
                return "Invalid teacher selected.", 400

            teacher_name_value = selected_teacher[1]

        cursor.execute("""
            UPDATE demo_requests
            SET
                teacher_id = %s,
                teacher_name = %s,
                demo_date = %s,
                demo_time = %s,
                status = %s
            WHERE id = %s
        """, (
            teacher_id_value,
            teacher_name_value,
            demo_date_value,
            demo_time_value,
            status,
            enquiry_id,
        ))

        conn.commit()
    except mysql.connector.Error:
        conn.rollback()
        cursor.close()
        conn.close()
        return "Unable to update enquiry.", 500

    cursor.close()
    conn.close()
    return redirect(url_for("enquiry_details", enquiry_id=enquiry_id))


# ============================================================
# QUICK STATUS UPDATE
# ============================================================


@app.route("/admin/enquiries/<int:enquiry_id>/status", methods=["POST"])
def update_enquiry_status(enquiry_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    new_status = request.form.get("status", "").strip()

    if new_status not in ALLOWED_STATUSES:
        return "Invalid status.", 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE demo_requests
        SET status = %s
        WHERE id = %s
    """, (new_status, enquiry_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_enquiries"))


# ============================================================
# TEACHER DASHBOARD
# ============================================================


@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "TEACHER":
        return "Access Denied", 403

    teacher_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Today's assigned demos.
    cursor.execute("""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.age,
            dr.preferred_time,
            dr.message,
            dr.status,
            dr.demo_date,
            dr.demo_time,
            dr.created_at
        FROM demo_requests dr
        WHERE dr.teacher_id = %s
          AND dr.demo_date = CURDATE()
        ORDER BY dr.demo_time ASC, dr.id DESC
    """, (teacher_id,))
    todays_demos = cursor.fetchall()

    # Upcoming assigned demos.
    cursor.execute("""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.age,
            dr.preferred_time,
            dr.message,
            dr.status,
            dr.demo_date,
            dr.demo_time,
            dr.created_at
        FROM demo_requests dr
        WHERE dr.teacher_id = %s
          AND dr.demo_date > CURDATE()
        ORDER BY dr.demo_date ASC, dr.demo_time ASC, dr.id DESC
        LIMIT 100
    """, (teacher_id,))
    upcoming_demos = cursor.fetchall()

    # Assigned demos without a scheduled date yet.
    cursor.execute("""
        SELECT
            dr.id,
            dr.demo_id,
            dr.full_name,
            dr.phone,
            dr.email,
            dr.instrument,
            dr.age,
            dr.preferred_time,
            dr.message,
            dr.status,
            dr.demo_date,
            dr.demo_time,
            dr.created_at
        FROM demo_requests dr
        WHERE dr.teacher_id = %s
          AND dr.demo_date IS NULL
        ORDER BY dr.id DESC
        LIMIT 100
    """, (teacher_id,))
    unscheduled_demos = cursor.fetchall()

    # Completed count.
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM demo_requests
        WHERE teacher_id = %s
          AND status = 'DEMO_COMPLETED'
    """, (teacher_id,))
    completed_count = cursor.fetchone()["total"]

    # All assigned demos count.
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM demo_requests
        WHERE teacher_id = %s
    """, (teacher_id,))
    assigned_count = cursor.fetchone()["total"]

    # Assigned students.
    cursor.execute("""
        SELECT
            s.id,
            s.student_code,
            s.full_name,
            s.phone,
            s.email,
            s.age,
            s.instrument,
            s.enrollment_date,
            s.status,
            s.notes
        FROM students s
        WHERE s.teacher_id = %s
        ORDER BY s.id DESC
        LIMIT 100
    """, (teacher_id,))
    assigned_students = cursor.fetchall()

    for collection in (todays_demos, upcoming_demos, unscheduled_demos):
        for demo in collection:
            demo["demo_time_display"] = format_db_time(demo.get("demo_time"))

    cursor.close()
    conn.close()

    return render_template(
        "teacher_dashboard.html",
        todays_demos=todays_demos,
        upcoming_demos=upcoming_demos,
        unscheduled_demos=unscheduled_demos,
        assigned_students=assigned_students,
        completed_count=completed_count,
        assigned_count=assigned_count,
        teacher_name=session.get("user_name"),
        user_name=session.get("user_name"),
        role=session.get("role"),
    )


# ============================================================
# LOGOUT
# ============================================================


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# TEACHER MANAGEMENT
# ============================================================


@app.route("/admin/teachers")
def admin_teachers():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "all").strip()

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            u.id,
            u.full_name,
            u.email,
            u.is_active,
            u.created_at,
            p.phone,
            p.instrument,
            p.experience_years,
            p.qualification,
            p.joining_date,
            p.bio
        FROM users u
        JOIN roles r ON u.role_id = r.id
        LEFT JOIN teacher_profiles p ON u.id = p.user_id
        WHERE r.role_name = 'TEACHER'
    """
    params = []

    if search:
        query += """
            AND (
                u.full_name LIKE %s
                OR u.email LIKE %s
                OR p.phone LIKE %s
                OR p.instrument LIKE %s
            )
        """
        search_value = f"%{search}%"
        params.extend([search_value] * 4)

    if status == "active":
        query += " AND u.is_active = TRUE"
    elif status == "inactive":
        query += " AND u.is_active = FALSE"

    query += " ORDER BY u.id DESC"

    cursor.execute(query, tuple(params))
    teachers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "teachers.html",
        teachers=teachers,
        search=search,
        status=status,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="teachers",
    )


# ============================================================
# ADD TEACHER
# ============================================================


@app.route("/admin/teachers/new", methods=["GET", "POST"])
def add_teacher():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        instrument = request.form.get("instrument", "").strip()
        experience_years = request.form.get("experience_years", "").strip()
        qualification = request.form.get("qualification", "").strip()
        bio = request.form.get("bio", "").strip()
        joining_date = request.form.get("joining_date", "").strip()

        if not full_name or not email or not password:
            return render_template(
                "teacher_form.html",
                teacher=None,
                error="Name, email and password are required.",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        if len(password) < 6:
            return render_template(
                "teacher_form.html",
                teacher=None,
                error="Password must contain at least 6 characters.",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        try:
            experience_value = float(experience_years) if experience_years else None
        except ValueError:
            return render_template(
                "teacher_form.html",
                teacher=None,
                error="Experience must be a valid number.",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT id
                FROM roles
                WHERE role_name = 'TEACHER'
                LIMIT 1
            """)
            teacher_role = cursor.fetchone()

            if not teacher_role:
                raise ValueError("TEACHER role does not exist.")

            # Explicit method avoids problems with newer Werkzeug defaults.
            password_hash = generate_password_hash(
                password,
                method="pbkdf2:sha256",
                salt_length=16,
            )

            cursor.execute("""
                INSERT INTO users
                (full_name, email, password_hash, role_id)
                VALUES (%s, %s, %s, %s)
            """, (
                full_name,
                email,
                password_hash,
                teacher_role["id"],
            ))

            teacher_user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO teacher_profiles
                (
                    user_id,
                    phone,
                    instrument,
                    experience_years,
                    qualification,
                    bio,
                    joining_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                teacher_user_id,
                phone or None,
                instrument or None,
                experience_value,
                qualification or None,
                bio or None,
                joining_date or None,
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("admin_teachers"))

        except ValueError as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template(
                "teacher_form.html",
                teacher=None,
                error=str(e),
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        except mysql.connector.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()

            if getattr(e, "errno", None) == 1062:
                error_message = "This email address is already registered."
            else:
                error_message = f"Unable to create teacher. Database error: {e}"

            return render_template(
                "teacher_form.html",
                teacher=None,
                error=error_message,
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template(
                "teacher_form.html",
                teacher=None,
                error=f"Unable to create teacher: {e}",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

    return render_template(
        "teacher_form.html",
        teacher=None,
        error=None,
        user_name=session.get("user_name"),
        role=session.get("role"),
    )


# ============================================================
# EDIT TEACHER
# ============================================================


@app.route("/admin/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
def edit_teacher(teacher_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        instrument = request.form.get("instrument", "").strip()
        experience_years = request.form.get("experience_years", "").strip()
        qualification = request.form.get("qualification", "").strip()
        bio = request.form.get("bio", "").strip()
        joining_date = request.form.get("joining_date", "").strip()

        if not full_name or not email:
            cursor.close()
            conn.close()
            return render_template(
                "teacher_form.html",
                teacher=None,
                error="Name and email are required.",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        try:
            experience_value = float(experience_years) if experience_years else None
        except ValueError:
            cursor.close()
            conn.close()
            return render_template(
                "teacher_form.html",
                teacher=None,
                error="Experience must be a valid number.",
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

        try:
            if password:
                password_hash = generate_password_hash(
                    password,
                    method="pbkdf2:sha256",
                    salt_length=16,
                )
                cursor.execute("""
                    UPDATE users
                    SET full_name = %s,
                        email = %s,
                        password_hash = %s
                    WHERE id = %s
                """, (full_name, email, password_hash, teacher_id))
            else:
                cursor.execute("""
                    UPDATE users
                    SET full_name = %s,
                        email = %s
                    WHERE id = %s
                """, (full_name, email, teacher_id))

            cursor.execute("""
                INSERT INTO teacher_profiles
                (
                    user_id,
                    phone,
                    instrument,
                    experience_years,
                    qualification,
                    bio,
                    joining_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    phone = VALUES(phone),
                    instrument = VALUES(instrument),
                    experience_years = VALUES(experience_years),
                    qualification = VALUES(qualification),
                    bio = VALUES(bio),
                    joining_date = VALUES(joining_date)
            """, (
                teacher_id,
                phone or None,
                instrument or None,
                experience_value,
                qualification or None,
                bio or None,
                joining_date or None,
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("admin_teachers"))

        except mysql.connector.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()

            if getattr(e, "errno", None) == 1062:
                error_message = "This email address is already registered."
            else:
                error_message = f"Unable to update teacher. Database error: {e}"

            return render_template(
                "teacher_form.html",
                teacher=None,
                error=error_message,
                user_name=session.get("user_name"),
                role=session.get("role"),
            )

    cursor.execute("""
        SELECT
            u.id,
            u.full_name,
            u.email,
            u.is_active,
            p.phone,
            p.instrument,
            p.experience_years,
            p.qualification,
            p.bio,
            p.joining_date
        FROM users u
        JOIN roles r ON u.role_id = r.id
        LEFT JOIN teacher_profiles p ON u.id = p.user_id
        WHERE u.id = %s
          AND r.role_name = 'TEACHER'
    """, (teacher_id,))

    teacher = cursor.fetchone()
    cursor.close()
    conn.close()

    if not teacher:
        return "Teacher not found", 404

    return render_template(
        "teacher_form.html",
        teacher=teacher,
        error=None,
        user_name=session.get("user_name"),
        role=session.get("role"),
    )


# ============================================================
# ACTIVATE / DEACTIVATE TEACHER
# ============================================================


@app.route("/admin/teachers/<int:teacher_id>/toggle-status", methods=["POST"])
def toggle_teacher_status(teacher_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users u
        JOIN roles r ON u.role_id = r.id
        SET u.is_active = NOT u.is_active
        WHERE u.id = %s
          AND r.role_name = 'TEACHER'
    """, (teacher_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_teachers"))


# ============================================================
# STUDENTS
# ============================================================


@app.route("/admin/students")
def admin_students():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "ALL").strip()

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            s.id,
            s.student_code,
            s.full_name,
            s.phone,
            s.email,
            s.age,
            s.instrument,
            s.enrollment_date,
            s.status,
            s.notes,
            s.created_at,
            u.full_name AS teacher_name
        FROM students s
        LEFT JOIN users u ON s.teacher_id = u.id
        WHERE 1 = 1
    """
    params = []

    if q:
        query += """
            AND (
                s.student_code LIKE %s
                OR s.full_name LIKE %s
                OR s.phone LIKE %s
                OR s.email LIKE %s
                OR s.instrument LIKE %s
            )
        """
        search_value = f"%{q}%"
        params.extend([search_value] * 5)

    if status in STUDENT_STATUSES:
        query += " AND s.status = %s"
        params.append(status)

    query += " ORDER BY s.id DESC"

    cursor.execute(query, tuple(params))
    students = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total_students = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM students
        WHERE status = 'ACTIVE'
    """)
    active_students = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM students
        WHERE status = 'INACTIVE'
    """)
    inactive_students = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "students.html",
        students=students,
        total_students=total_students,
        active_students=active_students,
        inactive_students=inactive_students,
        q=q,
        status=status,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="students",
    )


# ============================================================
# ADD STUDENT
# ============================================================


@app.route("/admin/students/new", methods=["GET", "POST"])
def add_student():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.id, u.full_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.role_name = 'TEACHER'
          AND u.is_active = TRUE
        ORDER BY u.full_name ASC
    """)
    teachers = cursor.fetchall()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        age = request.form.get("age", "").strip()
        instrument = request.form.get("instrument", "").strip()
        teacher_id = request.form.get("teacher_id", "").strip()
        enrollment_date = request.form.get("enrollment_date", "").strip()
        status = request.form.get("status", "ACTIVE").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name:
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                error="Student name is required.",
                student=request.form,
            )

        try:
            age_value = int(age) if age else None
            teacher_value = int(teacher_id) if teacher_id else None
        except ValueError:
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                error="Age or teacher value is invalid.",
                student=request.form,
            )

        # Insert first, then use the real AUTO_INCREMENT id to create the code.
        # This avoids relying on MAX(id) during normal creation.
        try:
            cursor.execute("""
                INSERT INTO students
                (
                    student_code,
                    full_name,
                    phone,
                    email,
                    age,
                    instrument,
                    teacher_id,
                    enrollment_date,
                    status,
                    notes
                )
                VALUES
                ('TEMP', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                full_name,
                phone or None,
                email or None,
                age_value,
                instrument or None,
                teacher_value,
                enrollment_date or None,
                status,
                notes or None,
            ))

            student_id = cursor.lastrowid
            student_code = f"MIN-STU-{student_id:04d}"

            cursor.execute("""
                UPDATE students
                SET student_code = %s
                WHERE id = %s
            """, (student_code, student_id))

            conn.commit()
        except mysql.connector.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                error=f"Unable to create student: {e}",
                student=request.form,
            )

        cursor.close()
        conn.close()
        return redirect(url_for("admin_students", created=student_code))

    cursor.close()
    conn.close()
    return render_template("student_form.html", teachers=teachers, student=None)


# ============================================================
# EDIT STUDENT
# ============================================================


@app.route("/admin/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found", 404

    cursor.execute("""
        SELECT u.id, u.full_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.role_name = 'TEACHER'
          AND u.is_active = TRUE
        ORDER BY u.full_name ASC
    """)
    teachers = cursor.fetchall()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        age = request.form.get("age", "").strip()
        instrument = request.form.get("instrument", "").strip()
        teacher_id = request.form.get("teacher_id", "").strip()
        enrollment_date = request.form.get("enrollment_date", "").strip()
        status = request.form.get("status", "ACTIVE").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name:
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                student=student,
                error="Student name is required.",
            )

        try:
            age_value = int(age) if age else None
            teacher_value = int(teacher_id) if teacher_id else None
        except ValueError:
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                student=student,
                error="Age or teacher value is invalid.",
            )

        try:
            cursor.execute("""
                UPDATE students
                SET
                    full_name = %s,
                    phone = %s,
                    email = %s,
                    age = %s,
                    instrument = %s,
                    teacher_id = %s,
                    enrollment_date = %s,
                    status = %s,
                    notes = %s
                WHERE id = %s
            """, (
                full_name,
                phone or None,
                email or None,
                age_value,
                instrument or None,
                teacher_value,
                enrollment_date or None,
                status,
                notes or None,
                student_id,
            ))
            conn.commit()
        except mysql.connector.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template(
                "student_form.html",
                teachers=teachers,
                student=student,
                error=f"Unable to update student: {e}",
            )

        cursor.close()
        conn.close()
        return redirect(url_for("student_details", student_id=student_id))

    cursor.close()
    conn.close()
    return render_template("student_form.html", teachers=teachers, student=student)


# ============================================================
# STUDENT DETAILS
# ============================================================


@app.route("/admin/students/<int:student_id>")
def student_details(student_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.*,
            u.full_name AS teacher_name,
            u.email AS teacher_email
        FROM students s
        LEFT JOIN users u ON s.teacher_id = u.id
        WHERE s.id = %s
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found", 404

    cursor.close()
    conn.close()

    return render_template(
        "student_details.html",
        student=student,
        user_name=session.get("user_name"),
        role=session.get("role"),
        active_page="students",
    )


# ============================================================
# ACTIVATE / DEACTIVATE STUDENT
# ============================================================


@app.route("/admin/students/<int:student_id>/toggle-status", methods=["POST"])
def toggle_student_status(student_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found", 404

    new_status = "INACTIVE" if student["status"] == "ACTIVE" else "ACTIVE"

    cursor.execute("""
        UPDATE students
        SET status = %s
        WHERE id = %s
    """, (new_status, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("student_details", student_id=student_id))


# ============================================================
# DELETE STUDENT
# ============================================================


@app.route("/admin/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_students"))


# ============================================================
# CONVERT ENQUIRY TO STUDENT
# ============================================================


@app.route("/admin/enquiries/<int:enquiry_id>/convert-to-student", methods=["POST"])
def convert_enquiry_to_student(enquiry_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "SUPER_ADMIN":
        return "Access Denied", 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM demo_requests
            WHERE id = %s
        """, (enquiry_id,))
        enquiry = cursor.fetchone()

        if not enquiry:
            cursor.close()
            conn.close()
            return "Enquiry not found", 404

        cursor.execute("""
            SELECT id, student_code
            FROM students
            WHERE source_enquiry_id = %s
            LIMIT 1
        """, (enquiry_id,))
        existing_student = cursor.fetchone()

        if existing_student:
            cursor.close()
            conn.close()
            return redirect(url_for(
                "student_details",
                student_id=existing_student["id"],
            ))

        # Create student with temporary unique value, then replace it using id.
        cursor.execute("""
            INSERT INTO students
            (
                student_code,
                full_name,
                phone,
                email,
                age,
                instrument,
                teacher_id,
                source_enquiry_id,
                enrollment_date,
                status,
                notes
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s, %s, %s,
                CURDATE(), 'ACTIVE', %s
            )
        """, (
            f"TEMP-{uuid.uuid4().hex}",
            enquiry["full_name"],
            enquiry["phone"],
            enquiry["email"],
            enquiry["age"],
            enquiry["instrument"],
            enquiry.get("teacher_id"),
            enquiry_id,
            enquiry.get("message"),
        ))

        student_id = cursor.lastrowid
        student_code = f"MIN-STU-{student_id:04d}"

        cursor.execute("""
            UPDATE students
            SET student_code = %s
            WHERE id = %s
        """, (student_code, student_id))

        cursor.execute("""
            UPDATE demo_requests
            SET status = 'ENROLLED'
            WHERE id = %s
        """, (enquiry_id,))

        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return f"Unable to convert enquiry: {e}", 500

    cursor.close()
    conn.close()

    return redirect(url_for("student_details", student_id=student_id))


# ============================================================
# DATABASE TEST
# ============================================================


@app.route("/test-db")
def test_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"Database connected successfully: {result}"
    except Exception as e:
        return f"Database error: {e}", 500


# ============================================================
# START APPLICATION
# IMPORTANT: THIS MUST BE THE LAST PART OF THE FILE.
# ============================================================


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
