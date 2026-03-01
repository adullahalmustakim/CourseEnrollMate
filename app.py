from flask import Flask, request, render_template, redirect, url_for, session
from helper import login_required, role_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

import sqlite3
def get_db_connection():
    conn = sqlite3.connect("courseenrollmate.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


from flask_session import Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE full_name=?",(username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["username"] = user["full_name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))

        return "Invalid username or password"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        role = request.form["role"]

        if password != confirm_password:
            return "Passwords do not match"

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        conn.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, role)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/student")
@login_required
@role_required("student")
def student_dashboard():
    return render_template("student_dashboard.html")


@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():

    conn = get_db_connection()

    total_courses = conn.execute(
        "SELECT COUNT(*) FROM courses"
    ).fetchone()[0]

    total_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='student'"
    ).fetchone()[0]

    total_admins = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='admin'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html", total_courses=total_courses, total_students=total_students, total_admins=total_admins
    )

@app.route("/add_course", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_course():

    if request.method == "POST":

        course_code = request.form["course_code"]
        course_title = request.form["course_title"]
        course_description = request.form["course_description"]
        credit_hours = request.form["credit_hours"]

        conn = get_db_connection()

        conn.execute(
            "INSERT INTO courses (course_code, course_title, course_description, credit_hours) VALUES (?, ?, ?, ?)",
            (course_code, course_title, course_description, credit_hours)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("manage_courses"))

    return render_template("add_course.html")

@app.route("/manage_courses")
@login_required
@role_required("admin")
def manage_courses():

    conn = get_db_connection()

    courses = conn.execute("SELECT * FROM courses").fetchall()

    conn.close()

    return render_template("manage_courses.html", courses=courses)

@app.route("/edit_course/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_course(id):

    conn = get_db_connection()

    course = conn.execute(
        "SELECT * FROM courses WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == "POST":

        course_code = request.form["course_code"]
        course_title = request.form["course_title"]
        course_description = request.form["course_description"]

        conn.execute(
            """UPDATE courses
               SET course_code=?, course_title=?, course_description=?
               WHERE id=?""",
            (course_code, course_title, course_description, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("manage_courses"))

    conn.close()

    return render_template("edit_course.html", course=course)

@app.route("/delete_course/<int:id>")
@login_required
@role_required("admin")
def delete_course(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM courses WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_courses"))

@app.route("/manage_credit_hours", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_credit_hours():

    conn = get_db_connection()

    if request.method == "POST":
        course_id = request.form["course_id"]
        credit_hours = request.form["credit_hours"]

        conn.execute(
            "UPDATE courses SET credit_hours=? WHERE id=?",
            (credit_hours, course_id)
        )
        conn.commit()

        return redirect(url_for("manage_credit_hours"))

    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    return render_template("manage_credit_hours.html", courses=courses)

@app.route("/manage_prerequisites", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_prerequisites():

    conn = get_db_connection()

    if request.method == "POST":

        course_id = request.form["course_id"]
        prerequisite_id = request.form["prerequisite_id"]

        if course_id == prerequisite_id:
            return "A course cannot be its own prerequisite"

        conn.execute(
            "INSERT INTO course_prerequisites (course_id, prerequisite_id) VALUES (?, ?)",
            (course_id, prerequisite_id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("manage_prerequisites"))

    courses = conn.execute("SELECT * FROM courses").fetchall()

    prerequisites = conn.execute("""
        SELECT cp.id, c.course_title AS course, p.course_title AS prerequisite
        FROM course_prerequisites cp
        JOIN courses c ON cp.course_id = c.id
        JOIN courses p ON cp.prerequisite_id = p.id
    """).fetchall()

    conn.close()

    return render_template(
        "manage_prerequisites.html",
        courses=courses,
        prerequisites=prerequisites
    )

@app.route("/delete_prerequisite/<int:id>")
@login_required
@role_required("admin")
def delete_prerequisite(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM course_prerequisites WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_prerequisites"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)