from flask import Flask, request, render_template, redirect, url_for, session, flash
from helper import login_required, role_required, check_prerequisites, check_seat_availability
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

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
        selected_role = request.form["role"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE full_name=?",(username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            if user["role"] != selected_role:
                return "Invalid role selected!"

            session["user_id"] = user["id"]
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
    flash("Enrollment request submitted successfully!")
    return render_template("register.html")

@app.route("/student")
@login_required
@role_required("student")
def student_dashboard():
    return render_template("student_dashboard.html")

@app.route("/enroll_courses")
@login_required
@role_required("student")
def enroll_courses():

    student_id = session["user_id"]

    conn = get_db_connection()

    courses = conn.execute("""
        SELECT 
            co.id AS offering_id,
            co.semester_id,
            c.course_code,
            c.course_title,
            c.credit_hours,
            s.semester_name,
            er.status AS enrollment_status
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        LEFT JOIN enrollment_requests er
            ON er.offering_id = co.id AND er.student_id = ?
        WHERE s.status = 'active'
    """, (student_id,)).fetchall()

    course_list = []

    for c in courses:


        deadline = conn.execute("""
            SELECT deadline_date
            FROM enrollment_deadline
            WHERE semester_id = ?
        """, (c["semester_id"],)).fetchone()

        if deadline and date.today() > date.fromisoformat(deadline["deadline_date"]):
            deadline_passed = True
        else:
            deadline_passed = False

        course_list.append({
            "offering_id": c["offering_id"],
            "course_code": c["course_code"],
            "course_title": c["course_title"],
            "credit_hours": c["credit_hours"],
            "semester_name": c["semester_name"],
            "enrollment_status": c["enrollment_status"],
            "deadline_passed": deadline_passed
        })

    conn.close()

    return render_template("enroll_courses.html", courses=course_list)

@app.route("/request_enrollment/<int:offering_id>")
@login_required
@role_required("student")
def request_enrollment(offering_id):

    student_id = session["user_id"]
    conn = get_db_connection()

    deadline = conn.execute("""
        SELECT ed.deadline_date
        FROM enrollment_deadline ed
        JOIN course_offerings co ON ed.semester_id = co.semester_id
        WHERE co.id = ?
    """, (offering_id,)).fetchone()

    if deadline:
        if date.today() > date.fromisoformat(deadline["deadline_date"]):
            flash("Enrollment deadline has passed for this course.")
            conn.close()
            return redirect(url_for("enroll_courses"))

    existing = conn.execute("""
        SELECT * FROM enrollment_requests
        WHERE student_id = ? AND offering_id = ?
    """, (student_id, offering_id)).fetchone()

    if existing:
        flash(f"You already have a request ({existing['status']}) for this course.")
        conn.close()
        return redirect(url_for("enroll_courses"))

    conn.execute("""
        INSERT INTO enrollment_requests (student_id, offering_id)
        VALUES (?, ?)
    """, (student_id, offering_id))

    conn.commit()
    conn.close()

    flash("Enrollment request submitted successfully!")
    return redirect(url_for("enroll_courses"))

@app.route("/rejected_courses")
@login_required
@role_required("student")
def rejected_courses():

    conn = get_db_connection()

    rejected = conn.execute("""
        SELECT 
            c.course_code,
            c.course_title,
            s.semester_name,
            er.rejection_reason,
            er.request_date
        FROM enrollment_requests er
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        WHERE er.student_id = ? AND er.status = 'rejected'
        ORDER BY er.request_date DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template("rejected_courses.html", rejected=rejected)

@app.route("/my_courses")
@login_required
@role_required("student")
def my_courses():

    student_id = session["user_id"]
    conn = get_db_connection()

    courses = conn.execute("""
        SELECT 
            er.id AS enrollment_id,
            co.id AS offering_id,
            co.semester_id,
            c.course_code,
            c.course_title,
            s.semester_name
        FROM enrollment_requests er
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        WHERE er.student_id = ? AND er.status = 'approved'
    """, (student_id,)).fetchall()

    course_list = []

    for c in courses:

        deadline = conn.execute("""
            SELECT deadline_date FROM drop_deadline
            WHERE semester_id = ?
        """, (c["semester_id"],)).fetchone()

        if deadline and date.today() > date.fromisoformat(deadline["deadline_date"]):
            drop_allowed = False
        else:
            drop_allowed = True

        course_list.append({
            "enrollment_id": c["enrollment_id"],
            "course_code": c["course_code"],
            "course_title": c["course_title"],
            "semester_name": c["semester_name"],
            "drop_allowed": drop_allowed
        })

    conn.close()

    return render_template("my_courses.html", courses=course_list)

@app.route("/drop_course/<int:enrollment_id>")
@login_required
@role_required("student")
def drop_course(enrollment_id):

    conn = get_db_connection()

    # Get semester for deadline check
    data = conn.execute("""
        SELECT co.semester_id
        FROM enrollment_requests er
        JOIN course_offerings co ON er.offering_id = co.id
        WHERE er.id = ?
    """, (enrollment_id,)).fetchone()

    from datetime import date

    deadline = conn.execute("""
        SELECT deadline_date FROM drop_deadline
        WHERE semester_id = ?
    """, (data["semester_id"],)).fetchone()

    if deadline and date.today() > date.fromisoformat(deadline["deadline_date"]):
        conn.close()
        flash("Drop deadline has passed.")
        return redirect(url_for("my_courses"))

    # Delete enrollment (drop)
    conn.execute("""
        DELETE FROM enrollment_requests
        WHERE id = ?
    """, (enrollment_id,))

    conn.commit()
    conn.close()

    flash("Course dropped successfully.")
    return redirect(url_for("my_courses")) 

@app.route("/enrolled_courses")
@login_required
@role_required("student")
def enrolled_courses():

    student_id = session["user_id"]
    conn = get_db_connection()

    courses = conn.execute("""
        SELECT 
            c.course_code,
            c.course_title,
            c.credit_hours,
            s.semester_name
        FROM enrollment_requests er
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        WHERE er.student_id = ? AND er.status = 'approved'
    """, (student_id,)).fetchall()

    total_credits = sum(course["credit_hours"] for course in courses)

    conn.close()

    return render_template(
        "enrolled_courses.html",
        courses=courses,
        total_credits=total_credits
    )

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

@app.route("/manage_semesters", methods=["GET","POST"])
@login_required
@role_required("admin")
def manage_semesters():

    conn = get_db_connection()

    if request.method == "POST":

        semester_name = request.form["semester_name"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        conn.execute(
            """INSERT INTO semesters
            (semester_name,start_date,end_date)
            VALUES (?,?,?)""",
            (semester_name,start_date,end_date)
        )

        conn.commit()

    semesters = conn.execute(
        "SELECT * FROM semesters"
    ).fetchall()

    conn.close()

    return render_template(
        "manage_semesters.html",
        semesters=semesters
    )

@app.route("/activate_semester/<int:id>")
@login_required
@role_required("admin")
def activate_semester(id):

    conn = get_db_connection()

    conn.execute("UPDATE semesters SET status='inactive'")

    conn.execute(
        "UPDATE semesters SET status='active' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_semesters"))

@app.route("/delete_semester/<int:id>")
@login_required
@role_required("admin")
def delete_semester(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM semesters WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_semesters"))

@app.route("/manage_course_offerings")
@login_required
@role_required("admin")
def manage_course_offerings():

    conn = get_db_connection()

    offerings = conn.execute("""
        SELECT co.id, c.course_code, c.course_title, s.semester_name
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
    """).fetchall()

    conn.close()

    return render_template(
        "manage_course_offerings.html",
        offerings=offerings
    )

@app.route("/add_course_offering", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_course_offering():

    conn = get_db_connection()

    courses = conn.execute("SELECT * FROM courses").fetchall()
    semesters = conn.execute("SELECT * FROM semesters").fetchall()

    if request.method == "POST":

        course_ids = request.form.getlist("course_id")
        semester_id = request.form["semester_id"]

        for course_id in course_ids:

            conn.execute(
                """
                INSERT OR IGNORE INTO course_offerings
                (course_id, semester_id)
                VALUES (?, ?)
                """,
                (course_id, semester_id)
            )

        conn.commit()
        conn.close()

        return redirect(url_for("manage_course_offerings"))

    conn.close()

    return render_template(
        "add_course_offering.html",
        courses=courses,
        semesters=semesters
    )

@app.route("/delete_course_offering/<int:id>")
@login_required
@role_required("admin")
def delete_course_offering(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM course_offerings WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_course_offerings"))

@app.route("/add_seat_limit")
@login_required
@role_required("admin")
def add_seat_limit():

    conn = get_db_connection()

    offerings = conn.execute("""
        SELECT 
            co.id,
            c.course_code,
            c.course_title,
            s.semester_name,
            co.max_seats
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
    """).fetchall()

    conn.close()

    return render_template("add_seat_limit.html", offerings=offerings)

@app.route("/insert_seat_limit/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def insert_seat_limit(id):

    max_seats = request.form["max_seats"]

    conn = get_db_connection()

    conn.execute(
        "UPDATE course_offerings SET max_seats = ? WHERE id = ?",
        (max_seats, id)
    )

    conn.commit()
    conn.close()

    flash("Maximum seat limit added successfully!")

    return redirect(url_for("add_seat_limit"))

@app.route("/update_seat_limit/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def update_seat_limit(id):

    max_seats = request.form["max_seats"]

    conn = get_db_connection()

    conn.execute(
        "UPDATE course_offerings SET max_seats = ? WHERE id = ?",
        (max_seats, id)
    )

    conn.commit()
    conn.close()

    flash("Seat limit updated successfully!")

    return redirect(url_for("add_seat_limit"))

@app.route("/manage_enrollments")
@login_required
@role_required("admin")
def manage_enrollments():

    conn = get_db_connection()

    requests = conn.execute("""
        SELECT 
            er.id AS request_id,
            er.student_id,
            u.full_name AS student_name,
            c.course_code,
            c.course_title,
            c.id AS course_id,
            co.id AS offering_id,
            co.max_seats,
            s.semester_name,
            (
                SELECT COUNT(*) 
                FROM enrollment_requests
                WHERE offering_id = co.id AND status = 'approved'
            ) AS approved_count
        FROM enrollment_requests er
        JOIN users u ON er.student_id = u.id
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        WHERE er.status = 'pending'
    """).fetchall()

    request_list = []

    for r in requests:
        prereq_status = check_prerequisites(r["student_id"], r["course_id"])

        request_list.append({
            "request_id": r["request_id"],
            "student_name": r["student_name"],
            "course_code": r["course_code"],
            "course_title": r["course_title"],
            "semester_name": r["semester_name"],
            "approved_count": r["approved_count"],
            "max_seats": r["max_seats"],
            "prereq_status": prereq_status
        })

    conn.close()

    return render_template("manage_enrollments.html", requests=request_list)

@app.route("/approve_enrollment/<int:request_id>")
@login_required
@role_required("admin")
def approve_enrollment(request_id):

    conn = get_db_connection()

    req = conn.execute("""
        SELECT er.student_id, co.id AS offering_id, co.max_seats, c.id AS course_id
        FROM enrollment_requests er
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        WHERE er.id = ?
    """, (request_id,)).fetchone()

    student_id = req["student_id"]
    offering_id = req["offering_id"]
    course_id = req["course_id"]

    from helper import check_prerequisites, check_seat_availability

    if not check_prerequisites(student_id, course_id):
        flash("Cannot approve: prerequisites not completed.")
        conn.close()
        return redirect(url_for("manage_enrollments"))

    if not check_seat_availability(offering_id):
        flash("Cannot approve: seats full.")
        conn.close()
        return redirect(url_for("manage_enrollments"))

    conn.execute("""
        UPDATE enrollment_requests
        SET status = 'approved'
        WHERE id = ?
    """, (request_id,))
    conn.commit()
    conn.close()

    flash("Enrollment approved successfully!")
    return redirect(url_for("manage_enrollments"))

@app.route("/reject_enrollment/<int:request_id>", methods=["GET","POST"])
@login_required
@role_required("admin")
def reject_enrollment(request_id):

    if request.method == "POST":
        reason = request.form["rejection_reason"]

        conn = get_db_connection()
        conn.execute("""
            UPDATE enrollment_requests
            SET status = 'rejected', rejection_reason = ?
            WHERE id = ?
        """, (reason, request_id))
        conn.commit()
        conn.close()

        flash("Enrollment rejected successfully!")
        return redirect(url_for("manage_enrollments"))

    return render_template("reject_enrollment.html", request_id=request_id)

@app.route("/manage_deadlines", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_deadlines():

    conn = get_db_connection()

    if request.method == "POST":

        semester_id = request.form["semester_id"]
        deadline = request.form["deadline"]

        conn.execute("""
            INSERT INTO enrollment_deadline (semester_id, deadline_date)
            VALUES (?,?)
        """, (semester_id, deadline))

        conn.commit()

    deadlines = conn.execute("""
        SELECT ed.id, s.semester_name, ed.deadline_date
        FROM enrollment_deadline ed
        JOIN semesters s ON ed.semester_id = s.id
    """).fetchall()

    semesters = conn.execute("SELECT * FROM semesters").fetchall()

    conn.close()

    return render_template(
        "manage_deadlines.html",
        deadlines=deadlines,
        semesters=semesters
    )

@app.route("/delete_deadline/<int:id>")
@login_required
@role_required("admin")
def delete_deadline(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM enrollment_deadline WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_deadlines"))

@app.route("/manage_drop_deadlines", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_drop_deadlines():

    conn = get_db_connection()

    if request.method == "POST":
        semester_id = request.form["semester_id"]
        deadline = request.form["deadline"]

        conn.execute("""
            INSERT INTO drop_deadline (semester_id, deadline_date)
            VALUES (?, ?)
        """, (semester_id, deadline))

        conn.commit()

    deadlines = conn.execute("""
        SELECT dd.id, s.semester_name, dd.deadline_date
        FROM drop_deadline dd
        JOIN semesters s ON dd.semester_id = s.id
    """).fetchall()

    semesters = conn.execute("SELECT * FROM semesters").fetchall()

    conn.close()

    return render_template(
        "manage_drop_deadlines.html",
        deadlines=deadlines,
        semesters=semesters
    )

@app.route("/delete_drop_deadline/<int:id>")
@login_required
@role_required("admin")
def delete_drop_deadline(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM drop_deadline WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("manage_drop_deadlines"))

@app.route("/enrollment_report")
@login_required
@role_required("admin")
def enrollment_report():

    conn = get_db_connection()

    course_summary = conn.execute("""
        SELECT 
            c.course_code,
            c.course_title,
            s.semester_name,
            co.max_seats,

            SUM(CASE WHEN er.status = 'approved' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN er.status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
            SUM(CASE WHEN er.status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count

        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        LEFT JOIN enrollment_requests er ON er.offering_id = co.id

        GROUP BY co.id
        ORDER BY s.semester_name, c.course_code
    """).fetchall()

    student_details = conn.execute("""
        SELECT 
            u.full_name AS student_name,
            c.course_code,
            c.course_title,
            s.semester_name,
            er.status,
            er.request_date
        FROM enrollment_requests er
        JOIN users u ON er.student_id = u.id
        JOIN course_offerings co ON er.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN semesters s ON co.semester_id = s.id
        ORDER BY u.full_name
    """).fetchall()

    conn.close()

    return render_template(
        "enrollment_report.html",
        course_summary=course_summary,
        student_details=student_details
    )



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)