from flask import Flask, request, render_template, redirect, url_for, session
from helper import login_required, role_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

import sqlite3
def get_db_connection():
    conn = sqlite3.connect("courseenrollmate.db")
    conn.row_factory = sqlite3.Row
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

        # Check passwords first
        if password != confirm_password:
            return "Passwords do not match"

        # Hash password AFTER checking
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
    return render_template("admin_dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)