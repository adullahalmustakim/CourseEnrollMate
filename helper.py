from functools import wraps
from flask import session, redirect, url_for, flash
import sqlite3


def get_db_connection():
    conn = sqlite3.connect("courseenrollmate.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "username" not in session:
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


def role_required(role):
    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            if session.get("role") != role:
                return "403 Forbidden: Unauthorized access"

            return f(*args, **kwargs)

        return decorated_function

    return decorator

def developer_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "developer_id" not in session:
            flash("Developer login required!")
            return redirect(url_for("developer_login"))
        return f(*args, **kwargs)

    return decorated_function

def check_prerequisites(student_id, course_id):

    conn = get_db_connection()

    prereqs = conn.execute("""
        SELECT prerequisite_id
        FROM course_prerequisites
        WHERE course_id = ?
    """, (course_id,)).fetchall()

    if not prereqs:
        conn.close()
        return True

    for prereq in prereqs:
        approved = conn.execute("""
            SELECT *
            FROM enrollment_requests er
            JOIN course_offerings co ON er.offering_id = co.id
            WHERE er.student_id = ?
            AND co.course_id = ?
            AND er.status = 'approved'
        """, (student_id, prereq["prerequisite_id"])).fetchone()

        if not approved:
            conn.close()
            return False

    conn.close()
    return True

def check_seat_availability(offering_id):

    conn = get_db_connection()

    offering = conn.execute("""
        SELECT max_seats
        FROM course_offerings
        WHERE id = ?
    """, (offering_id,)).fetchone()

    approved_count = conn.execute("""
        SELECT COUNT(*)
        FROM enrollment_requests
        WHERE offering_id = ?
        AND status = 'approved'
    """, (offering_id,)).fetchone()[0]

    conn.close()

    if approved_count < offering["max_seats"]:
        return True

    return False