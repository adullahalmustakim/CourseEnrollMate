import sqlite3

conn = sqlite3.connect("courseenrollmate.db")

cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'student'
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_title TEXT NOT NULL,
    course_description TEXT,
    credit_hours INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS course_prerequisites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    prerequisite_id INTEGER NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (prerequisite_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    status TEXT CHECK(status IN ('active','inactive')) DEFAULT 'inactive'
);

-- tables for Module 2

CREATE TABLE IF NOT EXISTS course_offerings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    semester_id INTEGER NOT NULL,
    max_seats INTEGER,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id)
);

CREATE TABLE IF NOT EXISTS enrollment_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    offering_id INTEGER NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
    rejection_reason TEXT,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);

-- tables for Module 3

CREATE TABLE IF NOT EXISTS enrollment_deadline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL,
    deadline_date TEXT NOT NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id)
);

CREATE TABLE IF NOT EXISTS drop_deadline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL,
    deadline_date TEXT NOT NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id)
);
                     
CREATE TABLE IF NOT EXISTS admin_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending'
);
                     
CREATE TABLE IF NOT EXISTS developers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);


""")
conn.commit()
conn.close()

print("Database created successfully!")

# develpoer id creation
# from werkzeug.security import generate_password_hash
# import sqlite3

# conn = sqlite3.connect("courseenrollmate.db")

# password = generate_password_hash("dev123")  # default password

# conn.execute("""
# INSERT OR IGNORE INTO developers (username, password)
# VALUES (?, ?)
# """, ("developer", password))

# conn.commit()
# conn.close()

# print("Default developer created!")