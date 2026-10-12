from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import json

app = Flask(__name__)

# -----------------------------
# APP CONFIGURATION
# -----------------------------

app.secret_key = "student-management-secret-key"

DATABASE = "students.db"


# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            cgpa REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if session.get("logged_in"):
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Demo admin credentials
        if username == "admin" and password == "admin123":

            session["logged_in"] = True
            session["username"] = username

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/")
def home():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    avg_cgpa = conn.execute(
        "SELECT COALESCE(AVG(cgpa), 0) FROM students"
    ).fetchone()[0]

    total_departments = conn.execute(
        "SELECT COUNT(DISTINCT department) FROM students"
    ).fetchone()[0]

    academic_years = conn.execute(
        "SELECT COUNT(DISTINCT year) FROM students"
    ).fetchone()[0]

    recent_students = conn.execute("""
        SELECT *
        FROM students
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    # -----------------------------
    # DEPARTMENT CHART
    # -----------------------------

    department_rows = conn.execute("""
        SELECT department, COUNT(*) AS total
        FROM students
        GROUP BY department
        ORDER BY department
    """).fetchall()

    department_labels = [
        row["department"]
        for row in department_rows
    ]

    department_values = [
        row["total"]
        for row in department_rows
    ]

    # -----------------------------
    # YEAR CHART
    # -----------------------------

    year_rows = conn.execute("""
        SELECT year, COUNT(*) AS total
        FROM students
        GROUP BY year
        ORDER BY year
    """).fetchall()

    year_labels = [
        f"Year {row['year']}"
        for row in year_rows
    ]

    year_values = [
        row["total"]
        for row in year_rows
    ]

    # -----------------------------
    # CGPA CHART
    # -----------------------------

    cgpa_data = [

        conn.execute("""
            SELECT COUNT(*)
            FROM students
            WHERE cgpa >= 7 AND cgpa < 8
        """).fetchone()[0],

        conn.execute("""
            SELECT COUNT(*)
            FROM students
            WHERE cgpa >= 8 AND cgpa < 9
        """).fetchone()[0],

        conn.execute("""
            SELECT COUNT(*)
            FROM students
            WHERE cgpa >= 9 AND cgpa <= 10
        """).fetchone()[0]
    ]

    conn.close()

    # Convert chart data to JSON
    department_labels_json = json.dumps(
        department_labels
    )

    department_values_json = json.dumps(
        department_values
    )

    year_labels_json = json.dumps(
        year_labels
    )

    year_values_json = json.dumps(
        year_values
    )

    cgpa_labels_json = json.dumps([
        "7 - 7.99",
        "8 - 8.99",
        "9 - 10"
    ])

    cgpa_values_json = json.dumps(
        cgpa_data
    )

    return render_template(
        "dashboard.html",
        total_students=total_students,
        avg_cgpa=round(float(avg_cgpa), 2),
        total_departments=total_departments,
        academic_years=academic_years,
        recent_students=recent_students,

        department_labels=department_labels_json,
        department_values=department_values_json,

        year_labels=year_labels_json,
        year_values=year_values_json,

        cgpa_labels=cgpa_labels_json,
        cgpa_values=cgpa_values_json,

        username=session.get("username")
    )


# -----------------------------
# STUDENTS
# -----------------------------

@app.route("/students")
def students():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    students_list = conn.execute("""
        SELECT *
        FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students_list,
        username=session.get("username")
    )


# -----------------------------
# ADD STUDENT
# -----------------------------

@app.route("/add", methods=["GET", "POST"])
def add_student():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "")

        try:
            year = int(request.form.get("year", 0))
            cgpa = float(request.form.get("cgpa", 0))
        except ValueError:
            return "Invalid year or CGPA", 400

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO students
                (name, roll_no, email, department, year, cgpa)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                roll_no,
                email,
                department,
                year,
                cgpa
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return """
                <h2>Student already exists</h2>
                <p>Roll number or email is already registered.</p>
                <a href="/add">Go Back</a>
            """

        conn.close()

        return redirect(url_for("students"))

    return render_template("add_student.html")


# -----------------------------
# EDIT STUDENT
# -----------------------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "")

        try:
            year = int(request.form.get("year", 0))
            cgpa = float(request.form.get("cgpa", 0))
        except ValueError:
            conn.close()
            return "Invalid year or CGPA", 400

        try:

            conn.execute("""
                UPDATE students
                SET
                    name = ?,
                    roll_no = ?,
                    email = ?,
                    department = ?,
                    year = ?,
                    cgpa = ?
                WHERE id = ?
            """, (
                name,
                roll_no,
                email,
                department,
                year,
                cgpa,
                id
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return """
                <h2>Update failed</h2>
                <p>Roll number or email is already being used.</p>
                <a href="/students">Go Back</a>
            """

        conn.close()

        return redirect(url_for("students"))

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if student is None:
        return """
            <h2>Student not found</h2>
            <a href="/students">Go Back</a>
        """, 404

    return render_template(
        "edit_student.html",
        student=student
    )


# -----------------------------
# DELETE STUDENT
# -----------------------------

@app.route("/delete/<int:id>")
def delete_student(id):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("students"))


# -----------------------------
# ANALYTICS
# -----------------------------

@app.route("/analytics")
def analytics():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    # Department statistics
    department_rows = conn.execute("""
        SELECT department, COUNT(*) AS total
        FROM students
        GROUP BY department
        ORDER BY department
    """).fetchall()

    # Year statistics
    year_rows = conn.execute("""
        SELECT year, COUNT(*) AS total
        FROM students
        GROUP BY year
        ORDER BY year
    """).fetchall()

    # CGPA statistics
    cgpa_rows = conn.execute("""
        SELECT
            CASE
                WHEN cgpa >= 9 THEN '9 - 10'
                WHEN cgpa >= 8 THEN '8 - 8.99'
                ELSE '7 - 7.99'
            END AS category,
            COUNT(*) AS total
        FROM students
        GROUP BY category
        ORDER BY category
    """).fetchall()

    # Top students
    top_students = conn.execute("""
        SELECT
            name,
            roll_no,
            department,
            cgpa
        FROM students
        ORDER BY cgpa DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    department_data = {
        "labels": [
            row["department"]
            for row in department_rows
        ],
        "values": [
            row["total"]
            for row in department_rows
        ]
    }

    year_data = {
        "labels": [
            f"Year {row['year']}"
            for row in year_rows
        ],
        "values": [
            row["total"]
            for row in year_rows
        ]
    }

    cgpa_data = {
        "labels": [
            row["category"]
            for row in cgpa_rows
        ],
        "values": [
            row["total"]
            for row in cgpa_rows
        ]
    }

    return render_template(
        "analytics.html",
        department_data=json.dumps(department_data),
        year_data=json.dumps(year_data),
        cgpa_data=json.dumps(cgpa_data),
        top_students=top_students,
        username=session.get("username")
    )


# -----------------------------
# START APPLICATION
# -----------------------------

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )