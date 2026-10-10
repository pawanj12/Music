import os

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)

cursor = conn.cursor()


# ============================================================
# GET TEACHER INFORMATION
# ============================================================

print("\n========================================")
print("      CREATE MINERVA TEACHER")
print("========================================\n")

full_name = input("Teacher full name: ").strip()
email = input("Teacher email: ").strip()
password = input("Teacher password: ").strip()


# ============================================================
# BASIC VALIDATION
# ============================================================

if not full_name:
    print("Teacher name is required.")
    cursor.close()
    conn.close()
    exit()

if not email:
    print("Teacher email is required.")
    cursor.close()
    conn.close()
    exit()

if not password:
    print("Teacher password is required.")
    cursor.close()
    conn.close()
    exit()


# ============================================================
# CHECK EMAIL
# ============================================================

cursor.execute(
    """
    SELECT id
    FROM users
    WHERE email = %s
    """,
    (email,),
)

existing_user = cursor.fetchone()

if existing_user:
    print("\nA user with this email already exists.")
    cursor.close()
    conn.close()
    exit()


# ============================================================
# GET TEACHER ROLE
# ============================================================

cursor.execute("""
    SELECT id
    FROM roles
    WHERE role_name = 'TEACHER'
    """)

teacher_role = cursor.fetchone()

if not teacher_role:
    print("\nTEACHER role was not found.")
    cursor.close()
    conn.close()
    exit()

role_id = teacher_role[0]


# ============================================================
# PASSWORD HASH
# ============================================================

password_hash = generate_password_hash(password)


# ============================================================
# INSERT TEACHER
# ============================================================

cursor.execute(
    """
    INSERT INTO users
    (
        full_name,
        email,
        password_hash,
        role_id,
        is_active
    )
    VALUES
    (
        %s,
        %s,
        %s,
        %s,
        TRUE
    )
    """,
    (full_name, email, password_hash, role_id),
)

conn.commit()


# ============================================================
# SUCCESS
# ============================================================

print("\n========================================")
print("Teacher created successfully!")
print("========================================")

print(f"Name  : {full_name}")
print(f"Email : {email}")
print("Role  : TEACHER")

cursor.close()
conn.close()


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

    # --------------------------------------------------------
    # TODAY'S DEMOS
    # --------------------------------------------------------

    cursor.execute(
        """
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

        WHERE
            dr.teacher_id = %s
            AND dr.demo_date = CURDATE()

        ORDER BY
            dr.demo_time ASC,
            dr.id DESC
    """,
        (teacher_id,),
    )

    todays_demos = cursor.fetchall()

    # --------------------------------------------------------
    # UPCOMING DEMOS
    # --------------------------------------------------------

    cursor.execute(
        """
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

        WHERE
            dr.teacher_id = %s
            AND dr.demo_date > CURDATE()

        ORDER BY
            dr.demo_date ASC,
            dr.demo_time ASC,
            dr.id DESC

        LIMIT 50
    """,
        (teacher_id,),
    )

    upcoming_demos = cursor.fetchall()

    # --------------------------------------------------------
    # COMPLETED DEMOS
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM demo_requests

        WHERE
            teacher_id = %s
            AND status = 'DEMO_COMPLETED'
    """,
        (teacher_id,),
    )

    completed_result = cursor.fetchone()

    completed_count = completed_result["total"]

    # --------------------------------------------------------
    # TOTAL ASSIGNED
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM demo_requests

        WHERE teacher_id = %s
    """,
        (teacher_id,),
    )

    assigned_result = cursor.fetchone()

    assigned_count = assigned_result["total"]

    cursor.close()
    conn.close()

    return render_template(
        "teacher_dashboard.html",
        teacher_name=session.get("user_name"),
        todays_demos=todays_demos,
        upcoming_demos=upcoming_demos,
        completed_count=completed_count,
        assigned_count=assigned_count,
    )
